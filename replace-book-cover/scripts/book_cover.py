#!/usr/bin/env python3
"""Inspect, replace, and verify covers in EPUB and PDF files."""

from __future__ import annotations

import argparse
import json
import posixpath
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import NoReturn
from xml.etree import ElementTree as ET


def fail(message: str) -> NoReturn:
    raise SystemExit(message)


def require_pillow():
    try:
        from PIL import Image
    except ImportError:
        fail("Pillow is required. See references/runtime.md.")
    return Image


def require_fitz():
    try:
        import fitz
    except ImportError:
        fail("PyMuPDF is required for PDF operations. See references/runtime.md.")
    return fitz


def epub_package(book: Path):
    try:
        archive = zipfile.ZipFile(book)
    except (zipfile.BadZipFile, OSError) as exc:
        fail(f"Cannot open EPUB: {exc}")
    names = set(archive.namelist())
    if "META-INF/encryption.xml" in names:
        archive.close()
        fail("Encrypted or DRM-related EPUB content is not supported.")
    try:
        container = ET.fromstring(archive.read("META-INF/container.xml"))
        rootfile = next(e for e in container.iter() if e.tag.endswith("rootfile"))
        opf_path = rootfile.attrib["full-path"]
        opf = ET.fromstring(archive.read(opf_path))
    except (KeyError, StopIteration, ET.ParseError) as exc:
        archive.close()
        fail(f"Invalid EPUB package metadata: {exc}")
    return archive, opf_path, opf


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def epub_info(book: Path):
    archive, opf_path, opf = epub_package(book)
    try:
        metadata = next((e for e in opf if local(e.tag) == "metadata"), None)
        manifest = next((e for e in opf if local(e.tag) == "manifest"), None)
        if manifest is None:
            fail("EPUB has no manifest.")
        items = {e.attrib.get("id"): e for e in manifest if local(e.tag) == "item"}
        cover_id = None
        if metadata is not None:
            for e in metadata:
                if local(e.tag) == "meta" and e.attrib.get("name", "").lower() == "cover":
                    cover_id = e.attrib.get("content")
                    break
        cover_item = items.get(cover_id)
        if cover_item is None:
            cover_item = next((e for e in items.values() if "cover-image" in e.attrib.get("properties", "").split()), None)
        if cover_item is None:
            fail("No package-declared EPUB cover image was found; refusing to guess.")
        base = PurePosixPath(opf_path).parent
        cover_path = posixpath.normpath(str(base / PurePosixPath(cover_item.attrib["href"])))
        values = {}
        if metadata is not None:
            for field in ("title", "creator", "language", "identifier"):
                values[field] = [((e.text or "").strip()) for e in metadata if local(e.tag) == field and (e.text or "").strip()]
        return archive, {
            "format": "epub",
            "path": str(book.resolve()),
            "metadata": values,
            "package_document": opf_path,
            "cover_path": cover_path,
            "cover_media_type": cover_item.attrib.get("media-type"),
            "entries": len(archive.namelist()),
        }
    except BaseException:
        archive.close()
        raise


def inspect_epub(book: Path):
    archive, info = epub_info(book)
    with archive:
        Image = require_pillow()
        with tempfile.TemporaryDirectory() as temp:
            cover = Path(temp) / Path(info["cover_path"]).name
            cover.write_bytes(archive.read(info["cover_path"]))
            with Image.open(cover) as image:
                info["cover_dimensions"] = list(image.size)
                info["cover_image_format"] = image.format
    return info


def convert_image(source: Path, media_type: str | None) -> bytes:
    Image = require_pillow()
    formats = {"image/jpeg": "JPEG", "image/jpg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}
    target_format = formats.get((media_type or "").lower())
    if target_format is None:
        fail(f"Unsupported EPUB cover media type: {media_type!r}. Expected JPEG, PNG, or WebP.")
    with Image.open(source) as image:
        image = image.convert("RGB") if target_format == "JPEG" else image.convert("RGBA")
        with tempfile.SpooledTemporaryFile() as output:
            kwargs = {"quality": 95, "optimize": True} if target_format == "JPEG" else {"optimize": True}
            image.save(output, format=target_format, **kwargs)
            output.seek(0)
            return output.read()


def replace_epub(book: Path, image: Path, output: Path):
    archive, info = epub_info(book)
    replacement = convert_image(image, info["cover_media_type"])
    with archive, zipfile.ZipFile(output, "w") as target:
        names = archive.namelist()
        if "mimetype" in names:
            old = archive.getinfo("mimetype")
            target.writestr(old, archive.read("mimetype"), compress_type=zipfile.ZIP_STORED)
        for entry in archive.infolist():
            if entry.filename == "mimetype":
                continue
            data = replacement if entry.filename == info["cover_path"] else archive.read(entry.filename)
            target.writestr(entry, data)
    return inspect_epub(output)


def inspect_pdf(book: Path):
    fitz = require_fitz()
    with fitz.open(book) as doc:
        if doc.page_count < 1:
            fail("PDF has no pages.")
        page = doc[0]
        return {
            "format": "pdf",
            "path": str(book.resolve()),
            "metadata": doc.metadata,
            "pages": doc.page_count,
            "cover_page": 1,
            "cover_dimensions_points": [page.rect.width, page.rect.height],
            "cover_text_preview": page.get_text("text")[:500].strip(),
        }


def replace_pdf(book: Path, image: Path, output: Path):
    fitz = require_fitz()
    Image = require_pillow()
    with fitz.open(book) as result:
        if result.page_count < 1:
            fail("PDF has no pages.")
        rect = result[0].rect
        toc = result.get_toc(simple=False)
        target_ratio = rect.width / rect.height
        with Image.open(image) as cover:
            width_px, height_px = cover.size
            crop_width = min(width_px, round(height_px * target_ratio))
            crop_height = min(height_px, round(width_px / target_ratio))
            left = (width_px - crop_width) // 2
            top = (height_px - crop_height) // 2
            fitted = cover.crop((left, top, left + crop_width, top + crop_height)).convert("RGB")
            with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_cover:
                fitted.save(temp_cover.name, format="JPEG", quality=95, optimize=True)
                page = result.new_page(pno=0, width=rect.width, height=rect.height)
                page.insert_image(page.rect, filename=temp_cover.name, keep_proportion=False)
        result.delete_page(1)
        if toc:
            result.set_toc(toc)
        result.save(output, garbage=4, deflate=True)
    info = inspect_pdf(output)
    info["source_cover_pixels"] = [width_px, height_px]
    return info


def output_path(source: Path, explicit: str | None) -> Path:
    target = Path(explicit) if explicit else source.with_name(f"{source.stem}-new-cover{source.suffix}")
    if target.resolve() == source.resolve():
        fail("Refusing to overwrite the source. Choose a different --output path.")
    if target.suffix.lower() != source.suffix.lower():
        fail("Output extension must match the input extension.")
    if target.exists():
        fail(f"Output already exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def inspect(book: Path):
    suffix = book.suffix.lower()
    if suffix == ".epub":
        return inspect_epub(book)
    if suffix == ".pdf":
        return inspect_pdf(book)
    fail("Input must be an .epub or .pdf file.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "verify"):
        command = sub.add_parser(name)
        command.add_argument("input")
    replace = sub.add_parser("replace")
    replace.add_argument("input")
    replace.add_argument("image")
    replace.add_argument("--output")
    args = parser.parse_args()
    book = Path(args.input)
    if not book.is_file():
        fail(f"Input does not exist: {book}")
    if args.command in ("inspect", "verify"):
        result = inspect(book)
        if args.command == "verify":
            result["valid"] = True
    else:
        image = Path(args.image)
        if not image.is_file():
            fail(f"Cover image does not exist: {image}")
        if book.suffix.lower() not in (".epub", ".pdf"):
            fail("Input must be an .epub or .pdf file.")
        target = output_path(book, args.output)
        try:
            result = replace_epub(book, image, target) if book.suffix.lower() == ".epub" else replace_pdf(book, image, target)
        except BaseException:
            target.unlink(missing_ok=True)
            raise
        result["output"] = str(target.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

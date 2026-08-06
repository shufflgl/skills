#!/usr/bin/env python3
"""Inspect one local EPUB for integrity, construction quality, and inserted ads."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import unicodedata
import urllib.parse
import zipfile
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET


AD_PATTERNS = [
    re.compile(pattern, re.I)
    for pattern in (
        r"关注.{0,12}(公众号|微信)",
        r"扫码.{0,12}(关注|加群|下载)",
        r"(加入|添加).{0,12}(QQ群|微信群|电报群)",
        r"(更多|海量).{0,12}(电子书|资源).{0,20}(下载|获取)",
        r"(加微信|微信号|QQ群)\s*[:：]",
        r"download more.{0,20}(?:free )?e-?books",
        r"join (?:our )?(?:telegram|whatsapp|discord)",
        r"visit .{0,50} for (?:more|free) e-?books",
        r"(?:free )?e-?book downloads?\s*[:：]?\s*https?://",
    )
]
TAG_RE = re.compile(r"<[^>]+>")
MAX_ARCHIVE_BYTES = 1024 * 1024 * 1024
MAX_TEXT_MEMBER_BYTES = 10 * 1024 * 1024
MAX_TEXT_SAMPLE_BYTES = 20 * 1024 * 1024


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def clean_markup(raw: str) -> str:
    raw = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", raw, flags=re.I | re.S)
    return " ".join(html.unescape(TAG_RE.sub(" ", raw)).split())


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return "".join(ch for ch in value if ch.isalnum())


def language_of(text: str) -> str:
    letters = [ch for ch in text if ch.isalpha()]
    if not letters:
        return "unknown"
    cjk = sum("\u3400" <= ch <= "\u9fff" for ch in letters)
    latin = sum("a" <= ch.casefold() <= "z" for ch in letters)
    if cjk / len(letters) >= 0.18:
        return "zh"
    if latin / len(letters) >= 0.55:
        return "en"
    return "other"


def ad_hits(text: str) -> list[str]:
    return sorted({pattern.pattern for pattern in AD_PATTERNS if pattern.search(text)})


def title_matches(actual: str, expected: str) -> bool:
    a, e = normalized(actual), normalized(expected)
    return bool(a and e and (a in e or e in a))


def manifest_member(opf_dir: PurePosixPath, href: str) -> str:
    path = urllib.parse.unquote(urllib.parse.urlsplit(href).path)
    return str(opf_dir.joinpath(PurePosixPath(path)))


def image_signature_is_valid(data: bytes, media_type: str) -> bool:
    stripped = data.lstrip()
    signatures = {
        "image/jpeg": data.startswith(b"\xff\xd8\xff"),
        "image/png": data.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/gif": data.startswith((b"GIF87a", b"GIF89a")),
        "image/webp": data.startswith(b"RIFF") and data[8:12] == b"WEBP",
        "image/svg+xml": stripped.startswith((b"<svg", b"<?xml")),
    }
    return signatures.get(media_type, bool(data))


def score_and_grade(failures: list[str], warnings: list[str]) -> tuple[int, str]:
    if failures:
        score = max(0, 45 - 8 * (len(failures) - 1) - 3 * len(warnings))
        return score, "reject"
    score = max(0, 100 - 8 * len(warnings))
    if score >= 95:
        return score, "excellent"
    if score >= 80:
        return score, "good"
    if score >= 65:
        return score, "acceptable"
    return score, "poor"


def make_report(path: Path, failures: list[str], warnings: list[str], details: dict) -> dict:
    score, grade = score_and_grade(failures, warnings)
    return {
        "status": "reject" if failures else "pass",
        "quality_score": score,
        "quality_grade": grade,
        "path": str(path.resolve()),
        "bytes": path.stat().st_size if path.exists() else 0,
        "failures": failures,
        "warnings": warnings,
        "details": details,
        "limitations": [
            "Structural plausibility does not prove textual completeness against an authoritative edition.",
            "Automated checks do not establish translation accuracy, proofreading quality, or perfect rendering.",
        ],
    }


def inspect(
    path: Path,
    expected_language: str | None = None,
    expected_title: str | None = None,
) -> dict:
    if not path.is_file():
        raise FileNotFoundError(path)
    failures: list[str] = []
    warnings: list[str] = []
    details: dict = {"format": "epub"}
    with path.open("rb") as handle:
        if not handle.read(8).startswith(b"PK"):
            return make_report(path, ["file is not a ZIP-based EPUB"], warnings, details)

    try:
        with zipfile.ZipFile(path) as zf:
            infos = zf.infolist()
            names = {info.filename for info in infos}
            total_uncompressed = sum(info.file_size for info in infos)
            details["archive_uncompressed_bytes"] = total_uncompressed
            unsafe_paths = [
                info.filename
                for info in infos
                if PurePosixPath(info.filename).is_absolute() or ".." in PurePosixPath(info.filename).parts
            ]
            if unsafe_paths:
                failures.append(f"archive contains {len(unsafe_paths)} unsafe path(s)")
            if total_uncompressed > MAX_ARCHIVE_BYTES:
                failures.append("archive expands beyond the 1 GiB safety limit")
                return make_report(path, failures, warnings, details)
            if path.stat().st_size and total_uncompressed > 50 * 1024 * 1024:
                if total_uncompressed / path.stat().st_size > 1000:
                    failures.append("suspicious compression ratio; possible ZIP bomb")
                    return make_report(path, failures, warnings, details)

            bad = zf.testzip()
            if bad:
                failures.append(f"corrupt ZIP member: {bad}")
            if "mimetype" not in names or zf.read("mimetype").strip() != b"application/epub+zip":
                failures.append("missing or invalid EPUB mimetype")
            if "META-INF/container.xml" not in names:
                failures.append("missing META-INF/container.xml")
                return make_report(path, failures, warnings, details)

            container = ET.fromstring(zf.read("META-INF/container.xml"))
            rootfile = next((element for element in container.iter() if local_name(element.tag) == "rootfile"), None)
            opf_name = rootfile.attrib.get("full-path", "") if rootfile is not None else ""
            if not opf_name or opf_name not in names:
                failures.append("package document is missing")
                return make_report(path, failures, warnings, details)
            opf = ET.fromstring(zf.read(opf_name))
            details["epub_version"] = opf.attrib.get("version", "unknown")

            metadata = next((element for element in opf.iter() if local_name(element.tag) == "metadata"), None)
            title = creator = declared_language = identifier = ""
            epub2_cover_id = ""
            if metadata is not None:
                for element in metadata.iter():
                    name = local_name(element.tag)
                    value = " ".join((element.text or "").split())
                    if name == "title" and not title:
                        title = value
                    elif name == "creator" and not creator:
                        creator = value
                    elif name == "language" and not declared_language:
                        declared_language = value.casefold()
                    elif name == "identifier" and not identifier:
                        identifier = value
                    elif name == "meta" and element.attrib.get("name") == "cover":
                        epub2_cover_id = element.attrib.get("content", "")
            details.update(
                title=title,
                creator=creator,
                identifier=identifier,
                declared_language=declared_language,
            )
            if not title:
                warnings.append("missing title metadata")
            if not creator:
                warnings.append("missing creator metadata")
            if not declared_language:
                warnings.append("missing language metadata")
            if not identifier:
                warnings.append("missing identifier metadata")
            if expected_title and (not title or not title_matches(title, expected_title)):
                failures.append(f"title metadata does not match expected title: {title or 'missing'}")

            opf_dir = PurePosixPath(opf_name).parent
            manifest: dict[str, tuple[str, str, str]] = {}
            spine_ids: list[str] = []
            cover_id = epub2_cover_id
            has_nav = has_css = False
            remote_resources = 0
            for element in opf.iter():
                name = local_name(element.tag)
                if name == "item":
                    item_id = element.attrib.get("id", "")
                    href = element.attrib.get("href", "")
                    media = element.attrib.get("media-type", "")
                    props = element.attrib.get("properties", "")
                    manifest[item_id] = (href, media, props)
                    has_nav |= "nav" in props.split()
                    has_css |= media == "text/css"
                    remote_resources += int("remote-resources" in props.split())
                    if "cover-image" in props.split():
                        cover_id = item_id
                elif name == "itemref" and element.attrib.get("linear", "yes") != "no":
                    spine_ids.append(element.attrib.get("idref", ""))
            if not has_nav:
                has_nav = any(media == "application/x-dtbncx+xml" for _, media, _ in manifest.values())

            missing_manifest = [
                item_id
                for item_id, (href, _, props) in manifest.items()
                if "remote-resources" not in props.split() and manifest_member(opf_dir, href) not in names
            ]
            if missing_manifest:
                failures.append(f"{len(missing_manifest)} manifest resource(s) are missing")
            if not has_nav:
                failures.append("missing EPUB navigation document")
            if not spine_ids:
                failures.append("empty reading-order spine")
            if not has_css:
                warnings.append("no stylesheet; presentation may be crude")
            if remote_resources:
                warnings.append(f"{remote_resources} remote resource(s) may fail offline")

            cover_valid = False
            if cover_id and cover_id in manifest:
                cover_href, cover_media, _ = manifest[cover_id]
                cover_member = manifest_member(opf_dir, cover_href)
                if cover_member in names:
                    cover_valid = image_signature_is_valid(zf.read(cover_member), cover_media)
                    if not cover_valid:
                        warnings.append("declared cover does not have a plausible image signature")
            else:
                warnings.append("no declared cover image")

            texts: list[str] = []
            missing_spine = malformed_xhtml = oversized_text = 0
            sampled_bytes = 0
            for item_id in spine_ids:
                item = manifest.get(item_id)
                if not item:
                    missing_spine += 1
                    continue
                href, media, _ = item
                member = manifest_member(opf_dir, href)
                if member not in names:
                    missing_spine += 1
                    continue
                if media not in {"application/xhtml+xml", "text/html"}:
                    continue
                info = zf.getinfo(member)
                if info.file_size > MAX_TEXT_MEMBER_BYTES:
                    oversized_text += 1
                    continue
                raw = zf.read(member)
                try:
                    ET.fromstring(raw)
                except ET.ParseError:
                    malformed_xhtml += 1
                if sampled_bytes < MAX_TEXT_SAMPLE_BYTES:
                    texts.append(clean_markup(raw.decode("utf-8", "replace")))
                    sampled_bytes += len(raw)
            if missing_spine:
                failures.append(f"{missing_spine} spine item(s) are missing")
            if malformed_xhtml:
                failures.append(f"{malformed_xhtml} spine document(s) contain malformed XHTML")
            if oversized_text:
                warnings.append(f"{oversized_text} unusually large spine document(s) were not sampled")

            combined = "\n".join(texts)
            inferred = language_of(combined[:250000])
            declared_primary = declared_language.split("-")[0] if declared_language else ""
            if expected_language and declared_primary and declared_primary != expected_language:
                failures.append(f"declared language {declared_language} is not {expected_language}")
            if expected_language and inferred not in {expected_language, "unknown"}:
                failures.append(f"content language appears to be {inferred}, not {expected_language}")
            if declared_primary in {"zh", "en"} and inferred not in {declared_primary, "unknown"}:
                warnings.append(
                    f"declared language {declared_language} differs from inferred content language {inferred}"
                )
            if len(texts) < 2 or len(combined) < 5000:
                failures.append("too little readable book content")

            hits = ad_hits(combined)
            if len(hits) >= 2:
                failures.append("multiple strong inserted-advertising signals found")
            elif hits:
                warnings.append("one possible inserted-advertising signal needs manual review")

            encryption_algorithms: list[str] = []
            unsupported_encryption: list[str] = []
            if "META-INF/encryption.xml" in names:
                enc_text = zf.read("META-INF/encryption.xml").decode("utf-8", "replace")
                encryption_algorithms = re.findall(r'Algorithm=["\']([^"\']+)', enc_text, re.I)
                allowed = ("http://www.idpf.org/2008/embedding", "http://ns.adobe.com/pdf/enc#RC")
                unsupported_encryption = [item for item in encryption_algorithms if item not in allowed]
                if unsupported_encryption:
                    failures.append("EPUB contains unsupported encryption or DRM")

            details.update(
                manifest_resources=len(manifest),
                spine_documents=len(texts),
                text_characters=len(combined),
                navigation=has_nav,
                cover=bool(cover_id),
                cover_signature_valid=cover_valid,
                stylesheet=has_css,
                remote_resources=remote_resources,
                inferred_language=inferred,
                advertising_signals=hits,
                encryption_algorithms=encryption_algorithms,
            )
    except (zipfile.BadZipFile, ET.ParseError, OSError, KeyError) as exc:
        failures.append(f"invalid EPUB: {exc}")
    return make_report(path, failures, warnings, details)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--expected-language", choices=("zh", "en"))
    parser.add_argument("--expected-title")
    args = parser.parse_args()
    try:
        result = inspect(args.file, args.expected_language, args.expected_title)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "pass" else 1
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())

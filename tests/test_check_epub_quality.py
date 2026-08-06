from __future__ import annotations

import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "check-epub-quality" / "scripts" / "inspect_epub.py"
SPEC = importlib.util.spec_from_file_location("inspect_epub", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def make_epub(
    path: Path,
    *,
    title: str,
    language: str,
    body: str,
    declare_cover: bool = True,
    include_cover: bool = True,
    malformed_chapter: bool = False,
) -> None:
    container = """<?xml version="1.0"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>"""
    cover_item = (
        '<item id="cover" href="cover.png" media-type="image/png" properties="cover-image"/>'
        if declare_cover
        else ""
    )
    opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier>urn:test:book</dc:identifier>
    <dc:title>{title}</dc:title><dc:creator>Test Author</dc:creator><dc:language>{language}</dc:language>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="c1" href="c1.xhtml" media-type="application/xhtml+xml"/>
    <item id="c2" href="c2.xhtml" media-type="application/xhtml+xml"/>
    <item id="css" href="style.css" media-type="text/css"/>
    {cover_item}
  </manifest>
  <spine><itemref idref="c1"/><itemref idref="c2"/></spine>
</package>"""
    chapter = f"<html xmlns='http://www.w3.org/1999/xhtml'><body><p>{body}</p></body></html>"
    if malformed_chapter:
        chapter = f"<html><body><p>{body}</body></html>"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("OEBPS/content.opf", opf)
        archive.writestr(
            "OEBPS/nav.xhtml",
            "<html xmlns='http://www.w3.org/1999/xhtml'><body><nav>Contents</nav></body></html>",
        )
        archive.writestr("OEBPS/c1.xhtml", chapter)
        archive.writestr("OEBPS/c2.xhtml", chapter)
        archive.writestr("OEBPS/style.css", "p { margin: 1em; }")
        if include_cover:
            archive.writestr("OEBPS/cover.png", b"\x89PNG\r\n\x1a\nsynthetic")


class InspectEpubTests(unittest.TestCase):
    def test_clean_epub_is_excellent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "clean.epub"
            make_epub(path, title="A Clean Book", language="en", body="Readable prose. " * 300)
            result = MODULE.inspect(path, "en", "A Clean Book")
            self.assertEqual(result["status"], "pass", result)
            self.assertEqual(result["quality_grade"], "excellent", result)
            self.assertEqual(result["quality_score"], 100, result)
            self.assertTrue(result["details"]["cover_signature_valid"])

    def test_multiple_ad_signals_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ads.epub"
            body = "这是完整的中文正文。" * 600 + " 关注我们的微信公众号。扫码加群下载更多电子书。"
            make_epub(path, title="测试书", language="zh-CN", body=body)
            result = MODULE.inspect(path, "zh", "测试书")
            self.assertEqual(result["status"], "reject", result)
            self.assertGreaterEqual(len(result["details"]["advertising_signals"]), 2)

    def test_html_disguised_as_epub_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fake.epub"
            path.write_text("<html>download error</html>")
            result = MODULE.inspect(path, "en", "Anything")
            self.assertEqual(result["status"], "reject", result)

    def test_missing_declared_cover_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.epub"
            make_epub(
                path,
                title="Broken Book",
                language="en",
                body="Readable prose. " * 300,
                include_cover=False,
            )
            result = MODULE.inspect(path, "en", "Broken Book")
            self.assertEqual(result["status"], "reject", result)
            self.assertTrue(any("manifest resource" in item for item in result["failures"]))

    def test_missing_cover_is_a_quality_warning(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "coverless.epub"
            make_epub(
                path,
                title="Coverless Book",
                language="en",
                body="Readable prose. " * 300,
                declare_cover=False,
                include_cover=False,
            )
            result = MODULE.inspect(path, "en", "Coverless Book")
            self.assertEqual(result["status"], "pass", result)
            self.assertLess(result["quality_score"], 100, result)
            self.assertTrue(any("cover" in item for item in result["warnings"]))

    def test_malformed_spine_xhtml_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "malformed.epub"
            make_epub(
                path,
                title="Malformed Book",
                language="en",
                body="Readable prose. " * 300,
                malformed_chapter=True,
            )
            result = MODULE.inspect(path, "en", "Malformed Book")
            self.assertEqual(result["status"], "reject", result)
            self.assertTrue(any("malformed XHTML" in item for item in result["failures"]))

    def test_expected_language_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "english.epub"
            make_epub(path, title="English Book", language="en", body="Readable prose. " * 300)
            result = MODULE.inspect(path, "zh", "English Book")
            self.assertEqual(result["status"], "reject", result)
            self.assertTrue(any("language" in item for item in result["failures"]))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SKILL = ROOT / "create-photo-art"
PLUGIN = ROOT / "photo-art-studio"
BUNDLED_SKILL = PLUGIN / "skills" / "create-photo-art"


class PhotoArtPluginTests(unittest.TestCase):
    def test_manifest_points_to_packaged_skill_and_logo(self) -> None:
        manifest = json.loads(
            (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["name"], PLUGIN.name)
        self.assertEqual(manifest["skills"], "./skills/")
        for key in ("composerIcon", "logo"):
            asset = manifest["interface"][key].removeprefix("./")
            self.assertTrue((PLUGIN / asset).is_file(), asset)

    def test_packaged_skill_matches_canonical_source(self) -> None:
        source_files = {
            path.relative_to(SOURCE_SKILL): path.read_bytes()
            for path in SOURCE_SKILL.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }
        bundled_files = {
            path.relative_to(BUNDLED_SKILL): path.read_bytes()
            for path in BUNDLED_SKILL.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }
        self.assertEqual(bundled_files, source_files)

    def test_logo_is_square_rgba_png(self) -> None:
        logo = (PLUGIN / "assets" / "logo.png").read_bytes()
        self.assertEqual(logo[:8], b"\x89PNG\r\n\x1a\n")
        width, height, _, color_type = struct.unpack(">IIBB", logo[16:26])
        self.assertEqual(width, height)
        self.assertEqual(color_type, 6)


if __name__ == "__main__":
    unittest.main()

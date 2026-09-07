from __future__ import annotations

import re
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
STYLE_ROOT = SKILL_ROOT / "references" / "styles"
ENTRY_PATTERN = re.compile(
    r"^(\d+)\. \*\*(.+?)\*\* .+?\[([^]]+\.md)\]\(([^)]+\.md)\)",
    re.MULTILINE,
)
RATIO_PATTERN = re.compile(
    r"^\| `(\d+:\d+)` \| ([^|]+) \| ([^|]+) \|$", re.MULTILINE
)


class StyleCatalogTests(unittest.TestCase):
    def test_registered_styles_have_stable_unique_ids_and_existing_files(self) -> None:
        catalog = (STYLE_ROOT / "index.md").read_text(encoding="utf-8")
        entries = ENTRY_PATTERN.findall(catalog)
        self.assertEqual([number for number, *_ in entries], ["1", "2", "3"])
        self.assertEqual(len({target for *_, target in entries}), len(entries))
        for _, _, label, target in entries:
            self.assertEqual(label, target)
            self.assertTrue((STYLE_ROOT / target).is_file(), target)

    def test_each_registered_style_has_a_complete_contract(self) -> None:
        catalog = (STYLE_ROOT / "index.md").read_text(encoding="utf-8")
        for number, name, _, target in ENTRY_PATTERN.findall(catalog):
            style = (STYLE_ROOT / target).read_text(encoding="utf-8")
            self.assertTrue(style.startswith(f"# Style {number}: {name}\n"), target)
            self.assertIn("## Creation modes", style, target)
            self.assertIn("## Composition", style, target)
            self.assertIn("## Exclusions", style, target)
            self.assertIn("## Verify", style, target)

    def test_ratio_catalog_covers_square_portrait_and_landscape_outputs(self) -> None:
        ratios = (SKILL_ROOT / "references" / "aspect-ratios.md").read_text(
            encoding="utf-8"
        )
        entries = RATIO_PATTERN.findall(ratios)
        identifiers = [identifier for identifier, _, _ in entries]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertGreaterEqual(len(identifiers), 5)
        self.assertIn("1:1", identifiers)
        dimensions = [tuple(map(int, value.split(":"))) for value in identifiers]
        self.assertTrue(any(width < height for width, height in dimensions))
        self.assertTrue(any(width > height for width, height in dimensions))


if __name__ == "__main__":
    unittest.main()

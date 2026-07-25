from __future__ import annotations

import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


class SkillContractTests(unittest.TestCase):
    def test_download_means_complete_atomic_workflow(self) -> None:
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn('Treat "download" as shorthand for the complete workflow', text)
        self.assertIn("never deliver an untagged or coverless audio file", text)
        self.assertIn("Atomic completion contract", text)
        self.assertIn("exactly one playable M4A", text)

    def test_generated_cover_is_a_required_fallback(self) -> None:
        text = (
            SKILL_ROOT / "references" / "generated-cover-art.md"
        ).read_text(encoding="utf-8")

        self.assertIn("whenever no suitable original artwork exists", text)
        self.assertIn("report the blocker with no audio output", text)

    def test_ui_prompt_describes_complete_output(self) -> None:
        text = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn("complete Apple Music-ready M4A", text)
        self.assertIn("verified metadata and embedded cover art", text)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


class SkillContractTests(unittest.TestCase):
    def test_download_means_complete_atomic_workflow(self) -> None:
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn('Treat "download" as shorthand for the complete workflow', text)
        self.assertIn(
            "never deliver a transcoded, untagged, unverified, or coverless audio file",
            text,
        )
        self.assertIn("Atomic completion contract", text)
        self.assertIn("exactly one playable audio file", text)

    def test_generated_cover_is_a_required_fallback(self) -> None:
        text = (
            SKILL_ROOT / "references" / "generated-cover-art.md"
        ).read_text(encoding="utf-8")

        self.assertIn("whenever no verified official song or release cover", text)
        self.assertIn("report the blocker with no audio output", text)

    def test_metadata_follows_actual_recording_not_catalog(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        reference = (
            SKILL_ROOT / "references" / "music-identification.md"
        ).read_text(encoding="utf-8")

        self.assertIn("actual recording", reference)
        self.assertIn("Never use them as evidence", reference)
        distributable_text_files = [
            SKILL_ROOT / "SKILL.md",
            SKILL_ROOT / "agents" / "openai.yaml",
            *sorted((SKILL_ROOT / "references").glob("*.md")),
            *sorted((SKILL_ROOT / "scripts").glob("*.py")),
        ]
        for path in distributable_text_files:
            with self.subTest(path=path):
                self.assertNotIn("Apple Music", path.read_text(encoding="utf-8"))

    def test_metadata_requires_external_official_research(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        reference = (
            SKILL_ROOT / "references" / "music-identification.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Perform a real web search", skill)
        self.assertIn("Do not transfer any Bilibili field directly", skill)
        self.assertIn("Require an external official source", skill)
        self.assertIn("Perform a live web search", reference)
        self.assertIn("Never copy or paraphrase", reference)
        self.assertIn("stop the atomic workflow", reference)

    def test_final_filename_contains_only_verified_title(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        reference = (
            SKILL_ROOT / "references" / "music-identification.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "Use exactly `<verified title>.<source-compatible extension>`", skill
        )
        self.assertIn("Never add an artist, uploader, BV identifier", skill)
        self.assertIn("filename stem equals the embedded title", skill)
        self.assertIn("Set the filename stem to exactly", reference)
        self.assertIn("Never overwrite an existing file", reference)

    def test_cover_has_only_official_or_generated_sources(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        reference = (
            SKILL_ROOT / "references" / "music-identification.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Use exactly one of these two cover sources", skill)
        self.assertIn("verified official song or release cover", skill)
        self.assertIn("newly generated cover", skill)
        self.assertIn("Do not use the Bilibili video thumbnail", skill)
        self.assertIn("Do not use a Bilibili video thumbnail", reference)

    def test_ui_prompt_describes_complete_output(self) -> None:
        text = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn("title-named source-quality audio file", text)
        self.assertIn("verified metadata", text)
        self.assertIn("official or newly generated cover art", text)

    def test_preserves_source_audio_without_transcoding(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        script = (
            SKILL_ROOT / "scripts" / "download_bilibili_audio.py"
        ).read_text(encoding="utf-8")

        self.assertIn("Never transcode the downloaded audio", skill)
        self.assertIn("encoded audio stream hash", skill)
        self.assertIn("A lossy source cannot be made lossless", skill)
        self.assertNotIn("--audio-format", script)


if __name__ == "__main__":
    unittest.main()

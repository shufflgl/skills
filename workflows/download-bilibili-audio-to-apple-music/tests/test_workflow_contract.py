from __future__ import annotations

import unittest
from pathlib import Path


WORKFLOW = Path(__file__).resolve().parents[1] / "SKILL.md"


class WorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_ineligible_record_requires_guarded_reimport(self) -> None:
        self.assertIn("If it is `Ineligible`", self.text)
        self.assertIn("final deletion confirmation", self.text)
        self.assertIn("explicitly choose to keep the disk file", self.text)
        self.assertIn("playlist membership", self.text)

    def test_need_upload_is_never_reported_as_cloud_complete(self) -> None:
        self.assertIn("`Need upload` or `Waiting` is a truthful pending result", self.text)
        self.assertIn("must never be reported as available on other devices", self.text)

    def test_hash_mismatch_must_stop_before_import(self) -> None:
        self.assertIn("If audio hashes differ", self.text)
        self.assertIn("stop before import", self.text)

    def test_cloud_status_not_local_playback_controls_completion(self) -> None:
        self.assertIn("Local import and playback are necessary checks", self.text)
        self.assertIn("Cloud Status is not `Ineligible`", self.text)
        self.assertIn("background upload task reports no error", self.text)


if __name__ == "__main__":
    unittest.main()

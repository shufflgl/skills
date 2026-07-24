from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
INIT = SKILL_ROOT / "scripts" / "init_handoff.py"
VERIFY = SKILL_ROOT / "scripts" / "verify_handoff.py"


def command(script: Path, repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), "--repo", str(repo), *args],
        text=True,
        capture_output=True,
        check=False,
    )


class HandoffScriptsTest(unittest.TestCase):
    def make_git_repo(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        repo = Path(temp.name)
        for args in (("init",), ("config", "user.email", "test@example.invalid"), ("config", "user.name", "Test")):
            subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)
        (repo / "README.md").write_text("test\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "README.md"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m", "initial"], check=True, capture_output=True)
        return temp

    def mark_ready(self, repo: Path, artifact_dir: Path | None = None) -> None:
        root = artifact_dir or repo / "AGENT_HANDOFF"
        readme = root / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8").replace("Status: DRAFT", "Status: READY"), encoding="utf-8")
        transfer = root / "transfer.md"
        transfer.write_text(transfer.read_text(encoding="utf-8").replace("Ready for receiver: NO", "Ready for receiver: YES"), encoding="utf-8")

    def test_init_is_idempotent_and_ready_handoff_verifies(self) -> None:
        with self.make_git_repo() as temp_dir:
            repo = Path(temp_dir)
            first = command(
                INIT,
                repo,
                "--objective",
                "Smoke-test task",
                "--next-action",
                "Run verification",
                "--transfer-method",
                "commit",
                "--baseline-ref",
                "HEAD",
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            snapshot = (repo / "AGENT_HANDOFF" / "snapshot.md").read_text(encoding="utf-8")
            workspace = (repo / "AGENT_HANDOFF" / "workspace.md").read_text(encoding="utf-8")
            self.assertIn("Smoke-test task", snapshot)
            self.assertIn("Run verification", snapshot)
            self.assertIn("Transfer method: `commit`", workspace)
            second = command(INIT, repo)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn("created: none", second.stdout)
            self.mark_ready(repo)
            verified = command(VERIFY, repo, "--require-ready")
            self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)


    def test_external_artifact_directory_is_the_only_created_copy(self) -> None:
        with self.make_git_repo() as temp_dir, tempfile.TemporaryDirectory() as artifact_temp:
            repo = Path(temp_dir)
            artifact_dir = Path(artifact_temp) / "portable-handoff"
            initialized = command(
                INIT,
                repo,
                "--artifact-dir",
                str(artifact_dir),
                "--objective",
                "Transfer elsewhere",
                "--next-action",
                "Verify the artifacts",
            )
            self.assertEqual(initialized.returncode, 0, initialized.stdout + initialized.stderr)
            self.assertTrue((artifact_dir / "snapshot.md").is_file())
            self.assertFalse((repo / "AGENT_HANDOFF").exists())
            self.mark_ready(repo, artifact_dir)
            verified = command(VERIFY, repo, "--artifact-dir", str(artifact_dir), "--require-ready")
            self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)

    def test_verifier_rejects_secret_and_reports_baseline_mismatch(self) -> None:
        with self.make_git_repo() as temp_dir:
            repo = Path(temp_dir)
            self.assertEqual(command(INIT, repo).returncode, 0)
            self.mark_ready(repo)
            workspace = repo / "AGENT_HANDOFF" / "workspace.md"
            workspace.write_text(workspace.read_text(encoding="utf-8").replace("HEAD: `", "HEAD: `deadbeef"), encoding="utf-8")
            mismatch = command(VERIFY, repo, "--require-ready")
            self.assertEqual(mismatch.returncode, 0, mismatch.stdout + mismatch.stderr)
            self.assertIn("Git HEAD mismatch", mismatch.stdout)
            snapshot = repo / "AGENT_HANDOFF" / "snapshot.md"
            snapshot.write_text(snapshot.read_text(encoding="utf-8") + "\nsecret sk-abcdefghijklmnopqrstuvwxyz123456\n", encoding="utf-8")
            secret = command(VERIFY, repo, "--require-ready")
            self.assertEqual(secret.returncode, 1)
            self.assertIn("appears to contain a secret", secret.stdout)


if __name__ == "__main__":
    unittest.main()

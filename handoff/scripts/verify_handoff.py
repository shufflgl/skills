#!/usr/bin/env python3
"""Validate portable-agent-handoff/v1 artifacts and compare their Git baseline."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ARTIFACT_DIR = "AGENT_HANDOFF"
REQUIRED = ("README.md", "snapshot.md", "workspace.md", "decisions.md", "validation.md", "transfer.md")
ABSOLUTE_PATH_PATTERNS = (
    re.compile(r"(?<![\w.])/(?:Users|home|var|tmp|private|opt)/[^\s`]+"),
    re.compile(r"(?<![\w:])(?:[A-Za-z]:\\(?:Users|home|Documents|Desktop)\\)[^\s`]+"),
)
SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)


def resolve_artifact_dir(repo: Path, artifact_dir: str | None) -> Path:
    if artifact_dir is None:
        return repo / ARTIFACT_DIR
    return Path(artifact_dir).expanduser().resolve()


@dataclass
class Findings:
    errors: list[str]
    warnings: list[str]

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def run_git(repo: Path, *args: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], text=True, capture_output=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else None


def field(text: str, label: str) -> str | None:
    match = re.search(rf"(?m)^- {re.escape(label)}:\s*(.+?)\s*$", text)
    return match.group(1).strip().strip("`") if match else None


def read_required(root: Path, findings: Findings) -> dict[str, str]:
    content: dict[str, str] = {}
    for name in REQUIRED:
        path = root / name
        if not path.is_file():
            findings.error(f"missing required artifact: {root / name}")
            continue
        try:
            content[name] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.error(f"artifact is not UTF-8 text: {root / name}")
    return content


def validate_structure(content: dict[str, str], findings: Findings, require_ready: bool) -> None:
    readme = content.get("README.md", "")
    if field(readme, "Format") != "portable-agent-handoff/v1":
        findings.error("README.md must contain '- Format: portable-agent-handoff/v1'")
    status = field(readme, "Status")
    if status not in {"DRAFT", "READY", "SUPERSEDED"}:
        findings.error("README.md Status must be DRAFT, READY, or SUPERSEDED")
    if field(readme, "Last updated (UTC)") is None:
        findings.error("README.md is missing Last updated (UTC)")
    if require_ready and status != "READY":
        findings.error("handoff is not READY")

    workspace = content.get("workspace.md", "")
    if "## Code baseline" not in workspace:
        findings.error("workspace.md is missing the Code baseline section")
    for label in ("Repository", "Branch", "HEAD", "Working tree at handoff", "Transfer method"):
        if field(workspace, label) is None:
            findings.error(f"workspace.md is missing '{label}'")

    transfer = content.get("transfer.md", "")
    for label in ("From agent", "To agent", "Handoff time (UTC)", "Ready for receiver"):
        if field(transfer, label) is None:
            findings.error(f"transfer.md is missing '{label}'")
    ready = field(transfer, "Ready for receiver")
    if ready not in {"YES", "NO"}:
        findings.error("transfer.md Ready for receiver must be YES or NO")
    if require_ready and ready != "YES":
        findings.error("transfer.md does not mark the handoff ready for the receiver")

    snapshot = content.get("snapshot.md", "")
    for heading in ("## Objective", "## Completed", "## Remaining / next actions", "## Active paths", "## Blockers and unknowns"):
        if heading not in snapshot:
            findings.error(f"snapshot.md is missing '{heading}'")


def validate_portability(content: dict[str, str], findings: Findings) -> None:
    for name, text in content.items():
        for pattern in ABSOLUTE_PATH_PATTERNS:
            if pattern.search(text):
                findings.error(f"{name} contains a machine-absolute path")
                break
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.error(f"{name} appears to contain a secret or private key")
                break
        if re.search(r"(?i)\b(session[_ -]?id|conversation[_ -]?id)\b", text):
            findings.warn(f"{name} mentions a session/conversation ID; do not require it for recovery")


def validate_git(repo: Path, content: dict[str, str], findings: Findings) -> None:
    current_head = run_git(repo, "rev-parse", "HEAD")
    if not current_head:
        findings.warn("current directory is not a Git repository with a commit; baseline could not be compared")
        return
    workspace = content.get("workspace.md", "")
    declared_head = field(workspace, "HEAD")
    declared_branch = field(workspace, "Branch")
    declared_tree = field(workspace, "Working tree at handoff")
    current_branch = run_git(repo, "branch", "--show-current") or "DETACHED"
    current_status = run_git(repo, "status", "--porcelain=v1")
    current_tree = "clean" if current_status == "" else "dirty"

    if declared_head in {None, "UNKNOWN"}:
        findings.warn("workspace.md has no comparable Git HEAD")
    elif declared_head != current_head:
        findings.warn(f"Git HEAD mismatch: artifact={declared_head}, current={current_head}")
    if declared_branch not in {None, "UNKNOWN", current_branch}:
        findings.warn(f"Git branch mismatch: artifact={declared_branch}, current={current_branch}")
    if declared_tree not in {None, "UNKNOWN", current_tree}:
        findings.warn(f"working-tree state differs: artifact={declared_tree}, current={current_tree}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="repository root (default: current directory)")
    parser.add_argument(
        "--artifact-dir",
        help=f"the handoff directory to verify (default: <repo>/{ARTIFACT_DIR})",
    )
    parser.add_argument("--require-ready", action="store_true", help="require transfer status READY/YES")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = parser.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    if not repo.is_dir():
        print(f"ERROR: repository directory does not exist: {repo}", file=sys.stderr)
        return 2
    root = resolve_artifact_dir(repo, args.artifact_dir)
    findings = Findings([], [])
    if not root.is_dir():
        findings.error(f"missing handoff directory: {root}")
        content: dict[str, str] = {}
    else:
        content = read_required(root, findings)
        validate_structure(content, findings, args.require_ready)
        validate_portability(content, findings)
        validate_git(repo, content, findings)

    for message in findings.errors:
        print(f"ERROR: {message}")
    for message in findings.warnings:
        print(f"WARNING: {message}")
    if findings.errors or (args.strict and findings.warnings):
        print(f"handoff verification failed ({len(findings.errors)} error(s), {len(findings.warnings)} warning(s))")
        return 1
    print(f"handoff verification passed ({len(findings.warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

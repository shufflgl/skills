#!/usr/bin/env python3
"""Create portable handoff templates without overwriting existing artifacts."""
from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path

ARTIFACT_DIR = "AGENT_HANDOFF"
TRANSFER_METHODS = ("UNKNOWN", "commit", "branch", "patch", "archive")


def resolve_artifact_dir(repo: Path, artifact_dir: str | None) -> Path:
    if artifact_dir is None:
        return repo / ARTIFACT_DIR
    return Path(artifact_dir).expanduser().resolve()


def run_git(repo: Path, *args: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], text=True, capture_output=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else None


def git_facts(repo: Path) -> dict[str, str]:
    head = run_git(repo, "rev-parse", "HEAD")
    if not head:
        return {"repository": repo.name, "branch": "UNKNOWN", "head": "UNKNOWN", "tree": "UNKNOWN"}
    branch = run_git(repo, "branch", "--show-current") or "DETACHED"
    status = run_git(repo, "status", "--porcelain=v1")
    return {
        "repository": repo.name,
        "branch": branch,
        "head": head,
        "tree": "clean" if status == "" else "dirty",
    }


def template_files(
    repo: Path,
    now: str,
    *,
    objective: str | None,
    next_action: str | None,
    transfer_method: str,
    baseline_ref: str | None,
) -> dict[str, str]:
    facts = git_facts(repo)
    baseline = baseline_ref or facts["head"]
    objective_line = objective or "TODO: State the user-visible task outcome."
    next_action_line = next_action or "TODO: State the next executable action."
    transfer_note = (
        "TODO: Record the commit/branch containing the work, or an explicitly approved relative patch path and SHA-256."
        if transfer_method == "UNKNOWN"
        else f"TODO: Record the exact {transfer_method} used to transfer the code state."
    )
    return {
        "README.md": f"""# Portable agent handoff

- Format: portable-agent-handoff/v1
- Status: DRAFT
- Last updated (UTC): {now}

This directory describes one explicit, unfinished task handoff. Transfer it with the code state it describes.

## Recovery order

1. `snapshot.md`
2. `workspace.md`
3. `transfer.md`
4. `validation.md`
5. `decisions.md` when relevant
""",
        "snapshot.md": f"""# Current snapshot

## Objective

- {objective_line}

## Completed

- TODO: State completed, code-verified work.

## Remaining / next actions

1. {next_action_line}

## Active paths

- TODO: `relative/path/to/file`

## Blockers and unknowns

- UNKNOWN: State what needs confirmation and how to resolve it.
""",
        "workspace.md": f"""# Workspace state

## Code baseline

- Repository: `{facts['repository']}`
- Branch: `{facts['branch']}`
- HEAD: `{baseline}`
- Working tree at handoff: `{facts['tree']}`
- Transfer method: `{transfer_method}`

## Changed / relevant paths

- TODO: `relative/path/to/file`

## Code transfer notes

- {transfer_note}
""",
        "decisions.md": """# Decisions

## Active decisions

- TODO: Decision; alternatives; rationale/evidence; consequence for the receiver.
""",
        "validation.md": """# Validation

| Command | Scope | Result | Notes |
| --- | --- | --- | --- |
| TODO | TODO | not run | State why it has not been run. |
""",
        "transfer.md": f"""# Transfer

- From agent: `UNKNOWN`
- To agent: `UNSPECIFIED`
- Handoff time (UTC): {now}
- Ready for receiver: NO

## Receiver first action

1. Read the snapshot, reconcile the Git baseline, then perform this concrete action: {next_action_line}
""",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="repository root (default: current directory)")
    parser.add_argument(
        "--artifact-dir",
        help=f"the single directory for this handoff (default: <repo>/{ARTIFACT_DIR})",
    )
    parser.add_argument("--objective", help="prefill snapshot objective when creating a new template")
    parser.add_argument("--next-action", help="prefill the first next action when creating a new template")
    parser.add_argument(
        "--transfer-method",
        choices=TRANSFER_METHODS[1:],
        help="prefill the planned code-transfer method when creating a new template",
    )
    parser.add_argument("--baseline-ref", help="prefill the code baseline (defaults to current Git HEAD)")
    args = parser.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    if not repo.is_dir():
        print(f"error: repository directory does not exist: {repo}", file=sys.stderr)
        return 2

    target = resolve_artifact_dir(repo, args.artifact_dir)
    target.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    templates = template_files(
        repo,
        now,
        objective=args.objective,
        next_action=args.next_action,
        transfer_method=args.transfer_method or "UNKNOWN",
        baseline_ref=args.baseline_ref,
    )
    created: list[str] = []
    preserved: list[str] = []
    for name, content in templates.items():
        path = target / name
        if path.exists():
            preserved.append(name)
            continue
        path.write_text(content, encoding="utf-8")
        created.append(name)

    print(f"artifact directory: {target}")
    print("created: " + (", ".join(created) if created else "none"))
    print("preserved: " + (", ".join(preserved) if preserved else "none"))
    print("next: complete the templates, then run verify_handoff.py --require-ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Export a sanitized, repository-backed catalog for the Skillroom website."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from catalog_lib import catalog_rows, read_categories, read_frontmatter, skill_dirs
from check_workflows import dependency_rows, validate as validate_workflows


DISPLAY_ROW = re.compile(
    r"^\|\s*\[(?:\*\*)?(.*?)(?:\*\*)?\]\(\./([A-Za-z0-9_-]+)/?\)\s*\|"
)
ABSOLUTE_PATH = re.compile(
    r"(?:^|[\s`'(\[])(?:/(?:Users|home|private|tmp|var|Volumes)/[^\s`)'\]]+|[A-Za-z]:\\\\[^\s`)'\]]+)"
)
IGNORED_PARTS = {"__pycache__", ".DS_Store", ".pytest_cache"}
ARTIFACT_KINDS = ("scripts", "tests", "references", "assets")


def run(
    args: list[str], root: Path, *, check: bool = False
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=root,
        capture_output=True,
        text=True,
        check=check,
    )


def display_names(readme: Path, heading: str) -> dict[str, str]:
    text = readme.read_text(encoding="utf-8")
    if heading not in text:
        return {}
    section = text.split(heading, 1)[1].split("\n## ", 1)[0]
    names: dict[str, str] = {}
    for line in section.splitlines():
        match = DISPLAY_ROW.match(line)
        if match:
            names[match.group(2)] = match.group(1).replace("**", "").strip()
    return names


def repo_url(root: Path) -> str:
    result = run(["git", "remote", "get-url", "origin"], root)
    if result.returncode:
        return ""
    url = result.stdout.strip()
    if url.startswith("git@github.com:"):
        url = "https://github.com/" + url.removeprefix("git@github.com:")
    return url.removesuffix(".git")


def git_revision(root: Path) -> dict[str, str]:
    commit = run(["git", "rev-parse", "--short=7", "HEAD"], root)
    branch = run(["git", "branch", "--show-current"], root)
    return {
        "commit": commit.stdout.strip() if commit.returncode == 0 else "unknown",
        "branch": branch.stdout.strip() if branch.returncode == 0 else "unknown",
    }


def latest_change(root: Path, relative_path: str) -> dict[str, str] | None:
    result = run(
        [
            "git",
            "log",
            "-1",
            "--format=%h%x1f%cI%x1f%s",
            "--",
            relative_path,
        ],
        root,
    )
    if result.returncode or not result.stdout.strip():
        return None
    commit, date, subject = result.stdout.strip().split("\x1f", 2)
    return {"commit": commit, "date": date, "subject": subject}


def recent_changes(root: Path, limit: int = 6) -> list[dict[str, str]]:
    result = run(
        ["git", "log", f"-{limit}", "--format=%h%x1f%cI%x1f%s"], root
    )
    if result.returncode:
        return []
    changes: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        commit, date, subject = line.split("\x1f", 2)
        changes.append({"commit": commit, "date": date, "subject": subject})
    return changes


def source_url(base: str, relative_path: str, action: str = "blob") -> str:
    if not base:
        return ""
    return f"{base}/{action}/main/{relative_path}"


def visible_files(directory: Path, root: Path, base_url: str) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or any(part in IGNORED_PARTS for part in path.parts):
            continue
        relative = path.relative_to(root).as_posix()
        records.append(
            {
                "name": path.name,
                "path": relative,
                "url": source_url(base_url, relative),
            }
        )
    return records


def artifacts(directory: Path, root: Path, base_url: str) -> dict[str, list[dict[str, str]]]:
    result: dict[str, list[dict[str, str]]] = {}
    for kind in ARTIFACT_KINDS:
        path = directory / kind
        result[kind] = visible_files(path, root, base_url) if path.is_dir() else []
    return result


def skill_records(root: Path, base_url: str) -> list[dict[str, Any]]:
    summaries = catalog_rows(root)
    categories = read_categories(root)
    names = display_names(root / "README.md", "## Skill catalog")
    records: list[dict[str, Any]] = []
    for name in sorted(skill_dirs(root)):
        directory = root / name
        skill_file = directory / "SKILL.md"
        frontmatter = read_frontmatter(skill_file)
        if not frontmatter.get("name") or not frontmatter.get("description"):
            raise ValueError(f"{name}: SKILL.md is missing required metadata")
        if frontmatter["name"] != name:
            raise ValueError(f"{name}: frontmatter name does not match its directory")
        category = frontmatter.get("category", "").strip()
        if not category:
            raise ValueError(f"{name}: SKILL.md is missing required category metadata")
        if category not in categories:
            raise ValueError(f"{name}: category '{category}' is not in categories.json")
        item_artifacts = artifacts(directory, root, base_url)
        records.append(
            {
                "kind": "skill",
                "name": name,
                "displayName": names.get(name, name.replace("-", " ").title()),
                "summary": summaries[name],
                "description": frontmatter["description"],
                "skillId": f"${name}",
                "category": category,
                "path": name,
                "sourceUrl": source_url(base_url, f"{name}/SKILL.md"),
                "editUrl": source_url(base_url, f"{name}/SKILL.md", "edit"),
                "issueUrl": (
                    f"{base_url}/issues/new?title=Skillroom%3A%20{name}"
                    f"&body=Skill%3A%20%60%24{name}%60%0A%0AWhat%20should%20change%3F%0A"
                    if base_url
                    else ""
                ),
                "artifacts": item_artifacts,
                "files": visible_files(directory, root, base_url),
                "latestChange": latest_change(root, name),
                "checks": ["catalog", "metadata"],
            }
        )
    return records


def workflow_records(root: Path) -> list[dict[str, Any]]:
    workflows_root = root / "workflows"
    categories = read_categories(root)
    names = display_names(workflows_root / "README.md", "## Workflow catalog")
    records: list[dict[str, Any]] = []
    for directory in sorted(workflows_root.iterdir()):
        if not directory.is_dir() or directory.name == "_template":
            continue
        skill_file = directory / "SKILL.md"
        frontmatter = read_frontmatter(skill_file)
        rows, table_error = dependency_rows(skill_file.read_text(encoding="utf-8"))
        if table_error:
            raise ValueError(f"{directory.name}: {table_error}")
        category = frontmatter.get("category", "").strip()
        if not category:
            raise ValueError(
                f"{directory.name}: SKILL.md is missing required category metadata"
            )
        if category not in categories:
            raise ValueError(
                f"{directory.name}: category '{category}' is not in categories.json"
            )
        dependencies = [
            {
                "skill": skill.strip("`"),
                "source": source,
                "requirement": requirement,
                "purpose": purpose,
            }
            for skill, source, requirement, purpose in rows
        ]
        change = latest_change(root, f"workflows/{directory.name}")
        public_change = (
            {"commit": change["commit"], "date": change["date"]} if change else None
        )
        record = {
            "kind": "workflow",
            "name": directory.name,
            "displayName": names.get(
                directory.name, directory.name.replace("-", " ").title()
            ),
            "summary": frontmatter.get("catalog_summary", ""),
            "category": category,
            "dependencies": dependencies,
            "latestChange": public_change,
        }
        serialized = json.dumps(record, ensure_ascii=False)
        if ABSOLUTE_PATH.search(serialized):
            raise ValueError(
                f"{directory.name}: public workflow data contains an absolute path"
            )
        records.append(record)
    return records


def validation_check(
    identifier: str, label: str, command: list[str], root: Path
) -> dict[str, Any]:
    result = run(command, root)
    output = "\n".join(
        part.strip() for part in (result.stdout, result.stderr) if part.strip()
    )
    return {
        "id": identifier,
        "label": label,
        "status": "pass" if result.returncode == 0 else "fail",
        "message": "All checks passed." if result.returncode == 0 else output,
        "command": (
            " ".join(["python3", *command[1:]])
            if command[0] == sys.executable
            else " ".join(command)
        ),
        "affectedItem": None,
    }


def test_check(root: Path) -> dict[str, Any]:
    test_directories = [root / "tests"] + sorted(root.glob("*/tests"))
    test_directories = [
        path
        for path in test_directories
        if path.is_dir() and any(path.glob("test_*.py"))
    ]
    total = 0
    skipped = 0
    failures: list[str] = []
    commands: list[str] = []
    for directory in test_directories:
        relative = directory.relative_to(root).as_posix()
        command = [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            relative,
            "-p",
            "test_*.py",
        ]
        commands.append(f"python3 -m unittest discover -s {relative} -p test_*.py")
        result = run(command, root)
        output = "\n".join((result.stdout, result.stderr))
        ran = re.search(r"Ran (\d+) tests?", output)
        skipped_match = re.search(r"skipped=(\d+)", output)
        total += int(ran.group(1)) if ran else 0
        skipped += int(skipped_match.group(1)) if skipped_match else 0
        if result.returncode:
            failures.append(output.strip())
    passed = total - skipped if not failures else 0
    return {
        "id": "tests",
        "label": "Repository tests",
        "status": "fail" if failures else "pass",
        "message": (
            "\n\n".join(failures)
            if failures
            else f"{passed} passed, {skipped} skipped across {len(test_directories)} suites."
        ),
        "command": " && ".join(commands),
        "affectedItem": None,
        "details": {
            "total": total,
            "passed": passed,
            "skipped": skipped,
            "suites": len(test_directories),
        },
    }


def build_snapshot(root: Path, *, strict: bool = True) -> dict[str, Any]:
    workflow_errors = validate_workflows(root)
    if workflow_errors:
        raise ValueError("; ".join(workflow_errors))

    checks = [
        validation_check(
            "catalog",
            "Skill catalog synchronization",
            [sys.executable, "scripts/check_catalog.py"],
            root,
        ),
        validation_check(
            "workflows",
            "Workflow contract",
            [sys.executable, "scripts/check_workflows.py"],
            root,
        ),
        test_check(root),
    ]
    failures = [check for check in checks if check["status"] == "fail"]
    if failures and strict:
        raise ValueError("; ".join(check["message"] for check in failures))

    base_url = repo_url(root)
    return {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "repository": {
            "name": "shufflgl/skills",
            "url": base_url,
            **git_revision(root),
        },
        "skills": skill_records(root, base_url),
        "workflows": workflow_records(root),
        "checks": checks,
        "recentChanges": recent_changes(root),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--allow-failing-checks",
        action="store_true",
        help="Write a diagnostic snapshot even when a validation command fails.",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        snapshot = build_snapshot(root, strict=not args.allow_failing_checks)
    except (KeyError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Exported {len(snapshot['skills'])} skills and "
        f"{len(snapshot['workflows'])} workflows to {output}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

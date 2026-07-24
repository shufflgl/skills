"""Shared helpers for the skill catalog consistency hooks."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

CATALOG_HEADING = "## Skill catalog"
ROW_PATTERN = re.compile(r"^\|\s*\[.*?\]\(\./([A-Za-z0-9_-]+)/?\)\s*\|\s*(.*?)\s*\|\s*$")


def repo_root() -> Path:
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
    )
    return Path(out.stdout.strip())


def skill_dirs(root: Path) -> set[str]:
    return {p.parent.name for p in root.glob("*/SKILL.md")}


def read_frontmatter(path: Path) -> dict[str, str]:
    """Parse simple `key: value` YAML frontmatter (no nesting, no multi-line values)."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fields: dict[str, str] = {}
    for line in text[3:end].splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def catalog_rows(root: Path) -> dict[str, str]:
    """Map skill directory name -> the description cell text in its README catalog row."""
    readme = (root / "README.md").read_text(encoding="utf-8")
    if CATALOG_HEADING not in readme:
        print(f"error: README.md is missing the '{CATALOG_HEADING}' section", file=sys.stderr)
        sys.exit(1)
    section = readme.split(CATALOG_HEADING, 1)[1]
    section = section.split("\n## ", 1)[0]
    rows: dict[str, str] = {}
    for line in section.splitlines():
        match = ROW_PATTERN.match(line)
        if match:
            rows[match.group(1)] = match.group(2)
    return rows

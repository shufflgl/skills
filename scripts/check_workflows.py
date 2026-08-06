#!/usr/bin/env python3
"""Validate personal workflow structure, dependencies, and catalog entries."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

WORKFLOW_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SKILL_IDENTIFIER = re.compile(r"^\$[a-z0-9]+(?:[-:][a-z0-9]+)*$")
CATALOG_ROW = re.compile(
    r"^\|\s*\[.*?\]\(\./([a-z0-9]+(?:-[a-z0-9]+)*)/?\)\s*\|\s*(.*?)\s*\|$"
)
FRONTMATTER_KEYS = ("name", "description", "catalog_summary")
REQUIRED_SECTIONS = (
    "Dependencies",
    "Defaults",
    "Workflow",
    "Approval gates",
    "Completion criteria",
    "Failure handling",
)
DEPENDENCY_HEADER = ("Skill", "Source", "Requirement", "Purpose")


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    fields: dict[str, str] = {}
    for raw_line in text[4:end].splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        fields[key.strip()] = value.strip()
    return fields


def markdown_sections(text: str) -> set[str]:
    return {
        match.group(1).strip()
        for match in re.finditer(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE)
    }


def split_table_row(line: str) -> tuple[str, ...] | None:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    return tuple(cell.strip() for cell in stripped[1:-1].split("|"))


def dependency_rows(text: str) -> tuple[list[tuple[str, ...]], str | None]:
    match = re.search(
        r"^## Dependencies\s*$\n(.*?)(?=^##\s|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not match:
        return [], "missing Dependencies section"
    lines = [line for line in match.group(1).splitlines() if line.strip()]
    table_lines = [line for line in lines if line.lstrip().startswith("|")]
    if len(table_lines) < 3:
        return [], "Dependencies must contain a header, separator, and at least one row"
    header = split_table_row(table_lines[0])
    if header != DEPENDENCY_HEADER:
        return [], "dependency header must be: Skill | Source | Requirement | Purpose"
    separator = split_table_row(table_lines[1])
    if separator is None or len(separator) != 4 or any(
        not re.fullmatch(r":?-{3,}:?", cell) for cell in separator
    ):
        return [], "dependency table has an invalid separator row"
    rows: list[tuple[str, ...]] = []
    for line in table_lines[2:]:
        row = split_table_row(line)
        if row is None or len(row) != 4:
            return [], "every dependency row must contain exactly four cells"
        rows.append(row)
    return rows, None


def catalog_rows(readme: Path) -> dict[str, str]:
    text = readme.read_text(encoding="utf-8")
    if "## Workflow catalog" not in text:
        raise ValueError("workflows/README.md is missing '## Workflow catalog'")
    section = text.split("## Workflow catalog", 1)[1]
    section = section.split("\n## ", 1)[0]
    rows: dict[str, str] = {}
    for line in section.splitlines():
        match = CATALOG_ROW.match(line)
        if match:
            rows[match.group(1)] = match.group(2)
    return rows


def validate(root: Path) -> list[str]:
    workflows = root / "workflows"
    errors: list[str] = []
    if not workflows.is_dir():
        return ["missing workflows/ directory"]
    readme = workflows / "README.md"
    if not readme.is_file():
        return ["missing workflows/README.md"]

    try:
        catalog = catalog_rows(readme)
    except ValueError as exc:
        return [str(exc)]

    on_disk: dict[str, str] = {}
    for directory in sorted(workflows.iterdir()):
        if not directory.is_dir() or directory.name == "_template":
            continue
        name = directory.name
        if not WORKFLOW_NAME.fullmatch(name):
            errors.append(f"{name}: directory name must use lowercase hyphen-case")
            continue
        skill_file = directory / "SKILL.md"
        if not skill_file.is_file():
            errors.append(f"{name}: missing SKILL.md")
            continue

        text = skill_file.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(skill_file)
        for key in FRONTMATTER_KEYS:
            if not frontmatter.get(key):
                errors.append(f"{name}: missing non-empty frontmatter field '{key}'")
        unexpected = sorted(set(frontmatter) - set(FRONTMATTER_KEYS))
        if unexpected:
            errors.append(f"{name}: unsupported frontmatter fields: {', '.join(unexpected)}")
        if frontmatter.get("name") != name:
            errors.append(f"{name}: frontmatter name must match the directory name")

        sections = markdown_sections(text)
        for section in REQUIRED_SECTIONS:
            if section not in sections:
                errors.append(f"{name}: missing '## {section}' section")

        rows, table_error = dependency_rows(text)
        if table_error:
            errors.append(f"{name}: {table_error}")
        else:
            for index, (skill, source, requirement, purpose) in enumerate(rows, start=1):
                skill = skill.strip("`")
                if not SKILL_IDENTIFIER.fullmatch(skill):
                    errors.append(f"{name}: dependency row {index} has invalid skill identifier")
                if not source or not purpose:
                    errors.append(f"{name}: dependency row {index} has an empty source or purpose")
                if requirement not in {"required", "optional"}:
                    errors.append(
                        f"{name}: dependency row {index} requirement must be required or optional"
                    )

        summary = frontmatter.get("catalog_summary", "")
        on_disk[name] = summary
        if name not in catalog:
            errors.append(f"{name}: missing Workflow catalog entry")
        elif catalog[name] != summary:
            errors.append(f"{name}: catalog text must match catalog_summary verbatim")

    for stale in sorted(set(catalog) - set(on_disk)):
        errors.append(f"{stale}: Workflow catalog entry has no workflow directory")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate(args.root.resolve())
    if not errors:
        return 0
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

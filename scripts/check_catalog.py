#!/usr/bin/env python3
"""Verify every skill's SKILL.md is consistent with the README catalog table.

Checks, per skill directory found on disk:
  1. SKILL.md declares a non-empty `catalog_summary` frontmatter field.
  2. The skill has a corresponding row in the README's '## Skill catalog' table.
  3. That row's description cell matches `catalog_summary` verbatim.

Also flags README catalog rows that reference a skill directory that no
longer exists.
"""
from __future__ import annotations

import sys

from catalog_lib import (
    catalog_rows,
    read_categories,
    read_frontmatter,
    repo_root,
    skill_dirs,
)


def main() -> int:
    root = repo_root()
    on_disk = skill_dirs(root)
    rows = catalog_rows(root)
    categories = read_categories(root)

    missing_entry: list[str] = []
    missing_summary: list[str] = []
    missing_category: list[str] = []
    unknown_category: list[tuple[str, str]] = []
    mismatched: list[tuple[str, str, str]] = []

    for name in sorted(on_disk):
        frontmatter = read_frontmatter(root / name / "SKILL.md")
        summary = frontmatter.get("catalog_summary", "").strip()
        category = frontmatter.get("category", "").strip()

        if not summary:
            missing_summary.append(name)
        if not category:
            missing_category.append(name)
        elif category not in categories:
            unknown_category.append((name, category))
        if not summary:
            continue

        row = rows.get(name)
        if row is None:
            missing_entry.append(name)
        elif row != summary:
            mismatched.append((name, summary, row))

    stale = sorted(set(rows) - on_disk)

    if not (
        missing_summary
        or missing_category
        or unknown_category
        or missing_entry
        or mismatched
        or stale
    ):
        return 0

    if missing_summary:
        print(
            "error: these skills have no 'catalog_summary' frontmatter field in SKILL.md:",
            file=sys.stderr,
        )
        for name in missing_summary:
            print(f"  - {name}", file=sys.stderr)
    if missing_category:
        print("error: these skills have no 'category' frontmatter field:", file=sys.stderr)
        for name in missing_category:
            print(f"  - {name}", file=sys.stderr)
    if unknown_category:
        print("error: these skills use categories not registered in categories.json:", file=sys.stderr)
        for name, category in unknown_category:
            print(f"  - {name}: {category}", file=sys.stderr)
    if missing_entry:
        print("error: these skills have no README catalog entry:", file=sys.stderr)
        for name in missing_entry:
            print(f"  - {name}", file=sys.stderr)
    if mismatched:
        print(
            "error: these skills' catalog_summary does not match their README catalog row:",
            file=sys.stderr,
        )
        for name, summary, row in mismatched:
            print(f"  - {name}:", file=sys.stderr)
            print(f"      SKILL.md catalog_summary: {summary}", file=sys.stderr)
            print(f"      README catalog row:       {row}", file=sys.stderr)
    if stale:
        print(
            "error: README catalog references skills that no longer exist:",
            file=sys.stderr,
        )
        for name in stale:
            print(f"  - {name}", file=sys.stderr)

    print(
        "\nAdd/update `catalog_summary` in SKILL.md and the matching row in the "
        "README '## Skill catalog' table so they read identically.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())

# Project Rules

- Use English for all documentation and any other text content in this repository.
- Publish only distributable skill source directories in this GitHub repository.
  Keep each skill at the repository root as `<skill-name>/`; never commit local
  runtime or installation directories such as `.agents/` or `.claude/`.
- Every skill's `SKILL.md` frontmatter must include a `catalog_summary` field:
  a concise one-line summary, used verbatim as the "What it helps with" text
  in the README's `## Skill catalog` table. Update both together whenever a
  skill's scope changes.

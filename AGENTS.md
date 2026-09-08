# Project Rules

- Use English for all documentation and any other text content in this repository.
- Publish distributable skill source directories at the repository root as
  `<skill-name>/`. The sole exception is `workflows/`, which contains tracked,
  strongly personalized orchestration sources that are explicitly not
  distributable or reusable. Never commit local runtime or installation
  directories such as `.agents/` or `.claude/`.
- Every skill's `SKILL.md` frontmatter must include a `catalog_summary` field:
  a concise one-line summary, used verbatim as the "What it helps with" text
  in the README's `## Skill catalog` table. Update both together whenever a
  skill's scope changes.
- Every Skill and workflow `SKILL.md` frontmatter must include a `category`
  field whose value exists in the repository-level `categories.json` allowlist.
  Add a new category there only when an existing category cannot accurately
  describe the capability.
- Every new Skill and workflow must ship with its own purpose-designed icon set.
  Package `assets/icon-small.png` and `assets/icon-large.png` inside its source
  directory, and reference them as `interface.icon_small` and
  `interface.icon_large` from `agents/openai.yaml`. Do not reuse another Skill,
  workflow, plugin, or website's branding. Treat the icon files and metadata as
  part of the distributable source and include them in every archive or release.
- Keep workflow sources under `workflows/<workflow-name>/`. Follow
  `workflows/README.md` for their contract and catalog rules. Do not install or
  link workflows into an agent runtime unless the user explicitly requests it;
  installation is the responsibility of the target environment's installer.

# Personal workflows

This directory contains strongly personalized workflows. They encode preferred
skill combinations, defaults, approval points, and definitions of done for one
person's recurring tasks. They are tracked for personal continuity, not offered
as reusable or distributable skills.

Reusable capabilities belong in atomic skill directories at the repository
root. A workflow must remain a thin orchestration layer: refer to skills by
identifier, pass inputs and outputs between them, and avoid copying their
procedures, scripts, references, or assets.

## Layout

Each workflow uses the native skill shape:

```text
workflows/
├── README.md
├── _template/
│   └── SKILL.md.template
└── <workflow-name>/
    └── SKILL.md
```

Create a workflow by copying `_template/SKILL.md.template` to
`<workflow-name>/SKILL.md`, replacing every placeholder, and adding a row to the
catalog below. Use lowercase hyphen-case for both the directory and frontmatter
`name`. The directory name, `name`, and catalog link must match.

The source directory does not make a workflow discoverable by Codex or Claude.
Do not create `.agents/` or `.claude/` links here. An installer must install or
link the workflow according to the target client's actual environment.

## Execution contract

1. Trigger a workflow through the use cases stated in its frontmatter
   `description` or by explicitly naming it.
2. Preflight every dependency before beginning work. Dependency checks are
   runtime responsibilities; the repository validator checks declarations only.
3. Invoke atomic skills by their declared identifiers. Do not reproduce their
   internal instructions in the workflow.
4. Treat workflow values as defaults. A user's explicit request for the current
   run takes precedence, except that it cannot bypass safety rules, approval
   gates, or completion criteria.
5. Follow the ordered workflow, carrying verified outputs forward as inputs.
6. Finish only after every completion criterion is satisfied, then report the
   results and material limitations.

## Dependency and substitution policy

Declare dependencies in the exact table defined by the template. Use `$name`
for ordinary skills and `$namespace:name` for namespaced skills. `Source`
identifies where an installer or agent should resolve the skill; it is
descriptive and does not install anything. `Requirement` must be `required` or
`optional`.

If a required skill is unavailable, the agent may identify a
capability-equivalent substitute, but it must explain the missing dependency,
the proposed replacement, and any behavioral difference. It must obtain the
user's explicit approval before using the substitute. If approval is denied or
no safe substitute exists, stop and report the blocker. Optional dependencies
may be skipped only as described by the workflow's failure handling.

## Workflow catalog

| Workflow | What it automates |
| --- | --- |
| [Download Bilibili Audio to Apple Music](./download-bilibili-audio-to-apple-music/) | Download verified Bilibili audio to the personal iCloud Music folder and import it into the Apple Music library. |
| [Deploy My Private VPS Proxy](./deploy-my-private-vps-proxy/) | Select and build my hardened private VPS proxy, then finish with verified Apple clients, performance evidence, and protected reusable backups. |

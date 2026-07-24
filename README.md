# Agent Skills

A small, portable collection of reusable skills for coding agents. Each skill is a self-contained directory centered on a `SKILL.md` file and may include scripts, references, and tests.

## Available skills

| Skill | Purpose |
| --- | --- |
| [`handoff`](./handoff/) | Create and recover explicit, portable task handoffs between fresh sessions, machines, Codex, and Claude Code. |

## Repository layout

```text
<skill-name>/
  SKILL.md          # Agent-facing workflow and trigger metadata
  references/       # Supporting documentation
  scripts/          # Optional local tooling
  tests/            # Tests for the tooling
```

## Install a skill

Review a skill before installing it. The shared-skill convention is:

- Global source: `~/.agents/skills/<skill-name>`
- Project source: `<project-root>/.agents/skills/<skill-name>`
- Claude access: a relative directory symlink from the matching `.claude/skills/` directory to the `.agents/skills/` directory

### Global installation

```sh
mkdir -p ~/.agents/skills ~/.claude/skills
cp -R handoff ~/.agents/skills/handoff
ln -s ../../.agents/skills/handoff ~/.claude/skills/handoff
```

### Project installation

Run these commands from the target project root:

```sh
mkdir -p .agents/skills .claude/skills
cp -R /path/to/agent-skills/handoff .agents/skills/handoff
ln -s ../../.agents/skills/handoff .claude/skills/handoff
```

Use a relative symlink only. Before replacing an existing installation or symlink, inspect it and confirm it belongs to the skill you intend to install.

## Validate `handoff`

The skill has no third-party runtime dependencies. Run its tests with:

```sh
python3 -m unittest discover -s handoff/tests -v
```

## Conventions

- Keep skills client-neutral unless a skill explicitly targets one client.
- Do not store secrets, machine-specific artifacts, virtual environments, or generated test output in this repository.
- Keep `SKILL.md` concise; put detailed schemas and procedures under `references/`.

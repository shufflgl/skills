# build-plugin

A Claude Code skill for scaffolding and authoring Claude Code plugins — covering directory structure, manifest schema, and all component types (skills, commands, agents, MCP servers, hooks).

## What it does

When you ask Claude to create or build a plugin, this skill takes over and guides the entire process:

1. Collects all required plugin metadata and component details in one pass (no back-and-forth)
2. Scaffolds the correct directory structure
3. Writes `plugin.json`, skill files, commands, agents, MCP server config, and hooks — all to spec

## Trigger phrases

- "Create a plugin that…"
- "Build a Claude Code plugin for…"
- "Scaffold a plugin with a skill and a command"
- "Package this MCP server as a plugin"

## Plugin structure produced

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json          ← manifest
├── .mcp.json                ← MCP server config (if needed)
├── skills/
│   └── skill-name/
│       └── SKILL.md
├── commands/
│   └── command-name.md
├── agents/
│   └── agent-name.md
├── hooks/
│   └── hooks.json
└── README.md
```

## What you can include in a plugin

| Component | Description |
|-----------|-------------|
| **Skills** | Auto-activated system prompts for Claude — triggered by task context |
| **Commands** | Slash commands users invoke manually (e.g. `/my-plugin:run`) |
| **Agents** | Specialized sub-agents with their own model, effort, and tool restrictions |
| **MCP Servers** | Bundled or remote tool servers |
| **Hooks** | Event-driven shell commands, HTTP calls, or agent triggers |
| **userConfig** | Declared secrets and user-specific values (stored in OS keychain) |

## Key constraints enforced

- `plugin.json` must live inside `.claude-plugin/`, not the root
- Skill files must be named exactly `SKILL.md` (uppercase)
- Secrets use `userConfig` with `sensitive: true` — never written into config files directly
- MCP server paths use `${CLAUDE_PLUGIN_ROOT}` — not absolute paths
- Skills, commands, agents, and hooks go at the plugin root, not inside `.claude-plugin/`

## Installation

This is a Claude Code skill. To install it:

```bash
claude plugins add <plugin-source>
```

Or place the `build-plugin/` directory in your Claude Code skills path and restart.

## Notes

This skill is designed exclusively for **Claude Code** (the CLI / IDE extension). It does not apply to the web chat interface or API usage.

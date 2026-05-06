# skills

AI agent skills and plugins collection.

## Codex Skills

| Skill | Path | Description |
|-------|------|-------------|
| onepassword-service-account | [_codex/onepassword-service-account/](_codex/onepassword-service-account/) | Use local 1Password service-account access through the `op` CLI without exposing service-account tokens or resolved secret values. |

## Claude Code Skills

| Skill | Path | Description |
|-------|------|-------------|
| build-plugin | [_claude/build-plugin/](_claude/build-plugin/) | A Claude Code skill for scaffolding and authoring Claude Code plugins — covering directory structure, manifest schema, and all component types (skills, commands, agents, MCP servers, hooks). |

## Plugins

| Plugin | Path | Description |
|--------|------|-------------|
| mcp-packer | [_claude/_plugins/mcp-packer/](_claude/_plugins/mcp-packer/) | Automatically package any MCP Server into a .mcpb Desktop Extension file |

## Installation

```bash
# Install a plugin
claude plugins add <plugin-source>
```

For Codex, copy a skill directory from `_codex/` into `~/.codex/skills/` and restart the session. For Claude Code, place the skill directory in your Claude Code skills path and restart.

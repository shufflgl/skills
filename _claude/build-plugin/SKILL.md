---
name: build-plugin
description: Use this skill when the user asks to create, scaffold, or build a Claude Code plugin, or wants to package functionality (MCP servers, slash commands, agents, skills) into a distributable plugin. Covers full plugin structure, manifest schema, component authoring, and end-to-end creation workflow.
---

You are building a Claude Code plugin. Follow this skill precisely — deviating from the directory structure or file naming will cause silent failures.

## Plugin Directory Structure

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json        ← manifest (only file here)
├── .mcp.json              ← MCP server config (optional)
├── skills/
│   └── skill-name/
│       └── SKILL.md       ← filename must be exactly SKILL.md
├── commands/
│   └── command-name.md    ← flat .md files
├── agents/
│   └── agent-name.md
├── hooks/
│   └── hooks.json
└── README.md
```

Critical rules:
- `plugin.json` lives inside `.claude-plugin/`, nowhere else
- Skills are directories containing `SKILL.md` (uppercase, exact name)
- Commands are flat `.md` files directly in `commands/`
- All other components (skills, commands, agents, hooks) go at the plugin root, NOT inside `.claude-plugin/`

## plugin.json Schema

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "What this plugin does",
  "author": {
    "name": "Author Name",
    "email": "author@example.com",
    "url": "https://github.com/author"
  },
  "homepage": "https://github.com/author/plugin-name",
  "repository": "https://github.com/author/plugin-name",
  "license": "MIT",
  "keywords": ["keyword1", "keyword2"]
}
```

`name` is the only required field. Version must be semver. If version is omitted, Claude Code uses git commit SHA as version.

Custom component paths (only needed if you deviate from defaults):
```json
{
  "name": "plugin-name",
  "skills": "./custom/skills/",
  "commands": ["./cmd1.md", "./cmd2.md"],
  "agents": "./custom/agents/",
  "hooks": "./config/hooks.json",
  "mcpServers": "./.mcp.json"
}
```

Warning: specifying a custom path for `skills` replaces the default `skills/` scan entirely. To keep defaults and add more, use an array: `"skills": ["./skills/", "./extras/"]`

## User Configuration (userConfig)

Use `userConfig` in `plugin.json` when the plugin needs secrets or user-specific values:

```json
{
  "name": "plugin-name",
  "userConfig": {
    "api_token": {
      "type": "string",
      "title": "API Token",
      "description": "Your API authentication token",
      "sensitive": true,
      "required": true
    },
    "output_dir": {
      "type": "directory",
      "title": "Output Directory",
      "description": "Where to write output files",
      "default": "~/output"
    }
  }
}
```

Field types: `string`, `number`, `boolean`, `directory`, `file`
Set `sensitive: true` for secrets — they go to the OS keychain (macOS Keychain / Windows Credential Manager), not settings.json. Keychain has ~2 KB total limit, keep sensitive values small.

Reference user config values as `${user_config.KEY}` in MCP configs, hook commands, monitor commands, and non-sensitive values in skill/agent content. They are also exported as `CLAUDE_PLUGIN_OPTION_<KEY>` env vars to subprocesses.

## SKILL.md Format

```markdown
---
name: skill-name
description: One-sentence description of when Claude should activate this skill. This determines auto-activation — be specific about trigger conditions.
version: 1.0.0
---

Skill instructions here. Write in imperative, direct language.
Claude reads this as a system prompt when the skill is active.

Include:
- What to do
- What NOT to do
- Specific formats, patterns, or constraints
- Decision trees for ambiguous cases
```

The `description` frontmatter field is critical — Claude uses it to decide when to auto-activate the skill. Make it precise and task-specific.

Skills can include supporting files alongside SKILL.md:
```
skills/
└── my-skill/
    ├── SKILL.md
    ├── reference.md      ← loaded on demand
    └── scripts/
        └── helper.sh     ← executable scripts
```

## Command (.md) Format

Commands are slash commands users invoke manually (e.g. `/plugin-name:command-name`):

```markdown
---
description: What this command does (shown in command picker)
---

Instructions for Claude when this command is invoked.

Use $ARGUMENTS to reference what the user typed after the command name.
```

## Agent Format

```markdown
---
name: agent-name
description: What this agent specializes in and when Claude should invoke it
model: sonnet
effort: medium
maxTurns: 20
disallowedTools: Write, Edit
---

System prompt for the agent.
```

Supported frontmatter: `name`, `description`, `model`, `effort`, `maxTurns`, `tools`, `disallowedTools`, `skills`, `memory`, `background`, `isolation`
`isolation: "worktree"` is the only valid isolation value.
NOT supported in plugin agents: `hooks`, `mcpServers`, `permissionMode`

## .mcp.json Format

```json
{
  "mcpServers": {
    "server-name": {
      "command": "${CLAUDE_PLUGIN_ROOT}/bin/server",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"],
      "env": {
        "API_KEY": "${user_config.api_token}",
        "DATA_DIR": "${CLAUDE_PLUGIN_DATA}"
      }
    },
    "remote-server": {
      "type": "http",
      "url": "https://api.example.com/mcp"
    }
  }
}
```

Key path variables:
- `${CLAUDE_PLUGIN_ROOT}` — plugin installation directory (changes on update, don't write here)
- `${CLAUDE_PLUGIN_DATA}` — persistent data directory at `~/.claude/plugins/data/{id}/` (survives updates, use for dependencies and caches)

## Hooks Format

`hooks/hooks.json`:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format.sh"
          }
        ]
      }
    ]
  }
}
```

Hook types: `command`, `http`, `mcp_tool`, `prompt`, `agent`
Key events: `SessionStart`, `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `UserPromptSubmit`, `Stop`, `SessionEnd`

## Build Workflow

When asked to create a plugin, follow this sequence:

1. **Collect all required information before writing any files** — ask the following in a single message, grouped clearly. Do not start creating files until all answers are received.

   Plugin identity (required, never infer or use placeholders):
   - Plugin name (kebab-case, e.g. `my-plugin`)
   - Version (default `1.0.0` if not specified)
   - One-line description
   - Author name
   - Author email
   - Author URL or GitHub profile (optional, skip if not provided)
   - License (default `MIT` if not specified)
   - Keywords (comma-separated, for discovery)

   Plugin scope:
   - Which components are needed: skills / commands / agents / MCP servers / hooks (can be multiple)
   - For each skill: its name and what it does
   - For each command: its slash command name and what it does
   - For each MCP server: startup command, language/runtime, any required secrets or user-configurable values
   - Does the plugin need any user configuration (API keys, paths, tokens)?

   If the user's initial request already answers some of these, pre-fill those answers and only ask for what's missing.

2. **Create directory structure** — create all directories first, then files.

3. **Write `.claude-plugin/plugin.json`** — metadata and userConfig if needed.

4. **Write each SKILL.md** — frontmatter name + description, then precise instructions.

5. **Write each command .md** — frontmatter description, then instructions using $ARGUMENTS.

6. **Write each agent .md** — frontmatter with model/effort/maxTurns, then system prompt.

7. **Write `.mcp.json`** if bundling MCP servers — use `${CLAUDE_PLUGIN_ROOT}` for bundled binaries.

8. **Write `hooks/hooks.json`** if needed.

9. **Write `README.md`** — installation instructions and component list.

10. **Verify structure** — confirm every SKILL.md is inside a named subdirectory, plugin.json is inside `.claude-plugin/`, and all paths in plugin.json start with `./`.

## Common Mistakes to Avoid

- Putting `plugin.json` at the root instead of inside `.claude-plugin/`
- Naming skill files anything other than `SKILL.md`
- Putting skills/commands/agents inside `.claude-plugin/` instead of the plugin root
- Using absolute paths in `.mcp.json` instead of `${CLAUDE_PLUGIN_ROOT}`
- Writing sensitive values (API keys) directly in config files instead of using `userConfig` with `sensitive: true`
- Forgetting that specifying a custom `skills` path in plugin.json disables the default `skills/` directory scan
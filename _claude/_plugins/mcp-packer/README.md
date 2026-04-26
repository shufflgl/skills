# mcp-packer

A Claude Plugin that automatically packages any MCP Server into a `.mcpb` Desktop Extension file.

## What it does

- Guides you through generating a `manifest.json` for Node.js, Python, or binary MCP servers
- Scaffolds the correct bundle directory structure
- Validates the bundle before packing
- Runs `mcpb pack` to produce an installable `.mcpb` file

## Requirements

- [mcpb CLI](https://github.com/anthropics/mcpb) installed: `npm install -g mcpb`
- Node.js (for the bundled restricted shell MCP server)

## Components

| Component | Path | Purpose |
|---|---|---|
| Skill | `skills/mcp-packer/SKILL.md` | Auto-activated when packing MCP servers; covers manifest schema, type differences, user_config rules, template variables, pre-pack checklist, and error handling |
| Command | `commands/pack-mcp.md` | `/pack-mcp` — step-by-step guided packaging flow |
| MCP: filesystem | `.mcp.json` → `filesystem` | Read/write files and create bundle directory structure |
| MCP: mcpb-shell | `.mcp.json` → `mcpb-shell` | Execute mcpb CLI commands only (restricted — no arbitrary shell) |

## User configuration

| Key | Type | Default | Description |
|---|---|---|---|
| `output_dir` | directory | `~/mcp-bundles` | Where `.mcpb` files are saved |

## Usage

### Slash command

Type `/pack-mcp` in Claude to start the guided packaging flow. Claude will ask for your server details and handle everything from manifest generation to the final `.mcpb` file.

### Natural language

Just describe what you want to package:

> "Package my Node.js MCP server at ~/projects/weather-mcp into a .mcpb extension"

The `mcp-packer` skill will activate automatically and guide you through the process.

## Bundle directory structure produced

```
~/mcp-bundles/
└── my-server/
    ├── manifest.json
    ├── index.js          (or server.py / bin/my-server)
    ├── node_modules/     (Node.js only)
    └── ...

~/mcp-bundles/my-server-1.0.0.mcpb   ← final output
```

## Installing the .mcpb file

- **Claude Desktop**: Settings → Extensions → Install from file → select the `.mcpb` file
- Or drag-and-drop the `.mcpb` file onto the Extensions panel

## Security note

The `mcpb-shell` MCP server only permits commands that start with `mcpb`. Shell metacharacters (`;`, `|`, `&`, backticks, etc.) are rejected. No arbitrary command execution is possible through this plugin.

## License

MIT — Author: islgl

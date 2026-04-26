---
name: mcp-packer
description: Activated when the user wants to package, bundle, or create a .mcpb Desktop Extension file from an MCP Server — including generating manifest.json, scaffolding the bundle directory, and running mcpb pack.
version: 1.0.0
---

# MCP Packer Skill

You help users package any MCP Server into a `.mcpb` Desktop Extension file using the `mcpb` CLI. You use two MCP tools: `filesystem` for all file operations and `mcpb-shell` (tool: `mcpb_run`) for running mcpb commands.

---

## 1. What is a .mcpb bundle?

A `.mcpb` file is a zip archive that Desktop Extension hosts (e.g. Claude Desktop) can install directly. It must contain exactly:

```
<bundle-name>/
├── manifest.json        ← required, schema below
├── server files...      ← the actual MCP server code/binary
└── (optional assets)
```

The `manifest.json` is the only required metadata file — it describes how the host should start the server.

---

## 2. manifest.json Schema

### Minimal required fields

```json
{
  "name": "my-mcp-server",
  "version": "1.0.0",
  "description": "What this server does",
  "server": {
    "type": "node",          // "node" | "python" | "binary"
    "entry": "./index.js",   // path relative to bundle root
    "args": []               // extra CLI args passed to the entry
  }
}
```

### Full schema with all optional fields

```json
{
  "name": "my-mcp-server",
  "version": "1.0.0",
  "description": "Short description shown in extension manager",
  "author": "Author Name",
  "homepage": "https://github.com/author/repo",
  "license": "MIT",
  "server": {
    "type": "node",
    "entry": "./dist/index.js",
    "args": ["--stdio"],
    "env": {
      "API_KEY": "${user_config.api_key}",
      "DATA_DIR": "${__dirname}/data"
    }
  },
  "user_config": {
    "api_key": {
      "type": "string",
      "title": "API Key",
      "description": "Your API authentication key",
      "sensitive": true,
      "required": true
    },
    "region": {
      "type": "string",
      "title": "Region",
      "description": "Service region",
      "default": "us-east-1"
    }
  }
}
```

---

## 3. Server type differences

### Node.js (`"type": "node"`)

- `entry` points to the `.js` file that starts the MCP stdio server.
- The host runs: `node <entry> <args>`.
- Bundle must include `node_modules/` (or the entry must be self-contained).
- Best practice: run `npm install --production` before packing, then include `node_modules/`.

```json
"server": {
  "type": "node",
  "entry": "./dist/index.js",
  "args": []
}
```

### Python (`"type": "python"`)

- `entry` points to the `.py` file.
- The host runs: `python3 <entry> <args>`.
- Bundle all dependencies with the server (e.g. using `pip install -t ./deps`), then add `sys.path.insert(0, './deps')` in the entry file.
- Alternatively, include a `requirements.txt` and document that the host must pre-install them.

```json
"server": {
  "type": "python",
  "entry": "./server.py",
  "args": ["--transport", "stdio"]
}
```

### Binary (`"type": "binary"`)

- `entry` points to a compiled executable (relative path).
- The host runs: `<entry> <args>` directly.
- Include pre-built binaries for each supported platform, OR build a universal binary.
- Note: binary bundles are platform-specific unless you use a fat binary.

```json
"server": {
  "type": "binary",
  "entry": "./bin/my-server",
  "args": []
}
```

---

## 4. user_config field rules

Use `user_config` in `manifest.json` when the server needs secrets or user-specific values at runtime.

**Rules:**

- `sensitive: true` → value is stored in OS keychain, NOT in a plain config file. Use this for API keys, tokens, passwords. The OS keychain has a ~2 KB total limit per app, so keep sensitive values small (store a key, not a full file).
- `required: true` → the host will refuse to launch the server until the user sets this value.
- `default` → pre-fills the field. Do NOT use defaults for sensitive fields.
- Field types: `string`, `number`, `boolean`, `directory`, `file`.

**Example — API key with a non-sensitive region:**

```json
"user_config": {
  "api_key": {
    "type": "string",
    "title": "API Key",
    "description": "Required for authentication",
    "sensitive": true,
    "required": true
  },
  "base_url": {
    "type": "string",
    "title": "Base URL",
    "description": "API endpoint",
    "default": "https://api.example.com"
  }
}
```

---

## 5. Template variable reference

Use these in `server.env` and `server.args` inside `manifest.json`:

| Variable | Resolves to |
|---|---|
| `${__dirname}` | Absolute path to the bundle's root directory at runtime |
| `${user_config.KEY}` | The value the user entered for config key `KEY` |

**Correct usage:**

```json
"env": {
  "SERVER_ROOT": "${__dirname}",
  "API_KEY": "${user_config.api_key}",
  "CACHE_DIR": "${__dirname}/cache"
}
```

**Common mistakes:**

- `"${__dirname}/../other"` — path traversal outside the bundle; avoid this.
- `"${user_config.API_KEY}"` — wrong capitalization; key must exactly match the `user_config` field name.
- Hardcoding an API key as a string literal in `env` — always use `user_config` + `sensitive: true` instead.

---

## 6. Pre-pack checklist

Before running `mcpb pack`, verify all of the following using the `filesystem` MCP:

1. **`manifest.json` exists** at bundle root and is valid JSON.
2. **`server.entry` file exists** — the path in `manifest.json` resolves to a real file inside the bundle directory.
3. **Dependencies are present:**
   - Node.js: `node_modules/` directory exists (or the entry is truly self-contained).
   - Python: deps directory or `requirements.txt` is present.
   - Binary: the executable file exists and is not a symlink to an external path.
4. **No absolute paths** in `manifest.json` — only relative paths or `${__dirname}` / `${user_config.*}` variables.
5. **`user_config` keys** referenced in `env` match the declared `user_config` field names exactly (case-sensitive).
6. **Bundle directory name** matches the `name` field in `manifest.json`.

---

## 7. Running mcpb commands

Use the `mcpb_run` tool from the `mcpb-shell` MCP server. Only `mcpb` commands are permitted.

```
# Initialize a new bundle scaffold in an existing directory
mcpb init ./my-server-bundle

# Pack a bundle directory into a .mcpb file
mcpb pack ./my-server-bundle

# Pack to a specific output directory
mcpb pack ./my-server-bundle --output ~/mcp-bundles/

# Check mcpb version
mcpb --version
```

Always pass `cwd` as the parent of the bundle directory when calling `mcpb_run`, unless mcpb requires it from within the bundle.

---

## 8. Common errors and fixes

| Error | Cause | Fix |
|---|---|---|
| `manifest.json not found` | File missing or wrong directory | Verify bundle root with filesystem MCP; create manifest.json |
| `entry file not found: ./index.js` | Entry path in manifest is wrong | Check actual filename; update `server.entry` |
| `invalid JSON in manifest.json` | Syntax error | Re-read manifest, fix JSON (trailing commas, missing quotes) |
| `user_config key 'API_KEY' not declared` | Env references undeclared config key | Add the key to `user_config` section in manifest |
| `mcpb: command not found` | mcpb CLI not installed | Tell user: `npm install -g mcpb` or `brew install mcpb` |
| Bundle installs but server won't start | Wrong `type` for the runtime | Double-check: Node → `node`, Python → `python`, binary → `binary` |
| Sensitive value truncated | Value exceeds OS keychain ~2 KB limit | Store only the key/token, not the full config file |

---

## 9. Workflow summary

When a user asks to package an MCP Server:

1. Collect: server name, version, language/runtime, entry point, startup args, any required user-configurable values.
2. Generate `manifest.json` using the correct type and user_config entries.
3. Use `filesystem` MCP to create the bundle directory and write `manifest.json`.
4. Run pre-pack checklist (section 6) — fix any issues before packing.
5. Use `mcpb_run` to execute `mcpb pack <bundle-dir> --output <output_dir>`.
6. Report the output `.mcpb` path and tell the user how to install it (drag-and-drop into Claude Desktop, or via the Extensions menu).

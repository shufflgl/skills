---
description: Package any MCP Server into a .mcpb Desktop Extension file — collects server info, generates manifest.json, and runs mcpb pack.
---

You are executing the `/pack-mcp` command. Your job is to guide the user through packaging their MCP Server into a `.mcpb` Desktop Extension file, step by step.

## Step 1 — Gather information

Ask the user the following questions in a **single message**. Do not proceed until all required answers are received.

**Required:**

1. **Server name** — kebab-case identifier, e.g. `my-weather-server`. This becomes the bundle directory name and the `name` field in `manifest.json`.
2. **Version** — semver string, e.g. `1.0.0`. Default: `1.0.0`.
3. **Short description** — one sentence shown in the extension manager.
4. **Language / runtime** — choose one: `Node.js`, `Python`, or `Binary (compiled executable)`.
5. **Entry point** — the file that starts the MCP server, relative to the bundle root. Examples:
   - Node.js: `./index.js` or `./dist/index.js`
   - Python: `./server.py`
   - Binary: `./bin/my-server`
6. **Startup args** — any additional CLI arguments the entry needs, e.g. `["--stdio"]`. Leave empty if none.
7. **User-configurable fields** — list each piece of information the server needs from the user at runtime (API keys, URLs, paths). For each one, provide: field name, type, description, whether it's sensitive (API key/token → yes), and whether it's required.
8. **Source directory** — the absolute path to the existing MCP server code, so we can copy it into the bundle. Leave blank to create an empty scaffold.
9. **Output directory** — where to write the final `.mcpb` file. Default: `${user_config.output_dir}` (the plugin's configured output dir).

**Optional (skip if not provided):**
- Author name
- Homepage URL
- License (default: MIT)

---

## Step 2 — Generate manifest.json

Using the answers from Step 1, construct `manifest.json` following these rules:

- `server.type`: `"node"` for Node.js, `"python"` for Python, `"binary"` for compiled executables.
- `server.entry`: the entry point the user provided.
- `server.args`: the startup args array (empty array `[]` if none).
- `server.env`: for each sensitive user_config key, add `"KEY": "${user_config.key}"` so the runtime injects it as an env var.
- `user_config`: one entry per user-configurable field. Mark API keys and tokens with `"sensitive": true`.
- Use `${__dirname}` for any paths that must be relative to the bundle root at runtime (e.g. a data directory inside the bundle).

Example for a Node.js server with an API key:

```json
{
  "name": "my-weather-server",
  "version": "1.0.0",
  "description": "Provides weather data via MCP",
  "author": "islgl",
  "license": "MIT",
  "server": {
    "type": "node",
    "entry": "./index.js",
    "args": [],
    "env": {
      "WEATHER_API_KEY": "${user_config.api_key}",
      "DATA_DIR": "${__dirname}/data"
    }
  },
  "user_config": {
    "api_key": {
      "type": "string",
      "title": "Weather API Key",
      "description": "API key from your weather data provider",
      "sensitive": true,
      "required": true
    }
  }
}
```

Show the generated `manifest.json` to the user and ask for confirmation before writing any files.

---

## Step 3 — Create bundle directory structure

After the user confirms the manifest, use the `filesystem` MCP to:

1. Create the bundle directory: `<output_dir>/<server-name>/`
2. Write `manifest.json` to `<output_dir>/<server-name>/manifest.json`.
3. If the user provided a source directory, copy the relevant server files into the bundle directory. Do NOT copy `.git/`, `node_modules/` (for Node.js, re-install below), or `__pycache__/`.
4. For **Node.js**: after copying, instruct the user to run `npm install --production` inside the bundle directory if `node_modules/` is needed. Or offer to scaffold a `package.json` if starting from scratch.
5. For **Python**: if a `requirements.txt` exists, tell the user to run `pip install -r requirements.txt -t ./deps` inside the bundle directory, and remind them to add `sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'deps'))` to the entry file.
6. For **Binary**: confirm the executable exists at the entry path and is executable.

---

## Step 4 — Pre-pack checklist

Before running `mcpb pack`, verify each item using the `filesystem` MCP:

- [ ] `manifest.json` exists at bundle root and is valid JSON.
- [ ] `server.entry` path resolves to a real file inside the bundle.
- [ ] No absolute paths in `manifest.json` (only relative paths, `${__dirname}`, or `${user_config.*}`).
- [ ] `user_config` keys referenced in `server.env` match declared field names exactly (case-sensitive).
- [ ] Bundle directory name matches the `name` field in `manifest.json`.
- [ ] For Node.js: `node_modules/` present or entry is self-contained.
- [ ] For Binary: executable bit is set.

Report the checklist results to the user. Fix any issues before continuing.

---

## Step 5 — Run mcpb pack

Use the `mcpb_run` tool (from the `mcpb-shell` MCP server) to pack the bundle:

```
mcpb pack <output_dir>/<server-name> --output <output_dir>
```

Pass `cwd` as `<output_dir>` (the parent of the bundle directory).

If `mcpb` is not found, tell the user to install it:
- npm: `npm install -g mcpb`
- Homebrew: `brew install mcpb`
Then retry.

---

## Step 6 — Report result

After a successful pack, tell the user:

1. **File path** of the generated `.mcpb` file, e.g. `~/mcp-bundles/my-weather-server-1.0.0.mcpb`.
2. **Installation instructions:**
   - Claude Desktop: Open Settings → Extensions → click "Install from file" → select the `.mcpb` file. Or drag-and-drop the `.mcpb` file onto the Extensions panel.
   - Other hosts: refer to the host's documentation for installing Desktop Extensions.
3. **After installation:** the host will prompt for any `required` user_config values before starting the server.

If the pack fails, show the error output and suggest fixes based on the error messages in the skill's common errors table.

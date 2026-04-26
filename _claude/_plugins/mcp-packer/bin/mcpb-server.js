#!/usr/bin/env node
/**
 * mcpb-shell: A restricted MCP server that ONLY executes mcpb CLI commands.
 * Implements the MCP stdio transport (JSON-RPC 2.0 over stdin/stdout).
 * No arbitrary shell execution is allowed — only commands prefixed with "mcpb".
 */

const { execSync } = require('child_process');
const readline = require('readline');

const rl = readline.createInterface({ input: process.stdin, terminal: false });
const DEFAULT_CWD = process.env.OUTPUT_DIR || process.env.HOME || '/tmp';

function send(obj) {
  process.stdout.write(JSON.stringify(obj) + '\n');
}

function ok(id, result) {
  send({ jsonrpc: '2.0', id, result });
}

function err(id, code, message) {
  send({ jsonrpc: '2.0', id, error: { code, message } });
}

const TOOLS = [
  {
    name: 'mcpb_run',
    description: [
      'Execute a mcpb CLI command.',
      'Allowed commands: mcpb init, mcpb pack, mcpb --version, mcpb --help.',
      'The command string MUST start with "mcpb". Any other prefix is rejected.'
    ].join(' '),
    inputSchema: {
      type: 'object',
      properties: {
        command: {
          type: 'string',
          description: 'Full mcpb command to run, e.g. "mcpb pack ./my-mcp-dir"'
        },
        cwd: {
          type: 'string',
          description: 'Working directory for the command. Defaults to output_dir.'
        }
      },
      required: ['command']
    }
  }
];

rl.on('line', (line) => {
  let req;
  try {
    req = JSON.parse(line.trim());
  } catch (_) {
    return; // ignore malformed lines
  }

  const { id, method, params } = req;

  if (method === 'initialize') {
    ok(id, {
      protocolVersion: '2024-11-05',
      capabilities: { tools: {} },
      serverInfo: { name: 'mcpb-shell', version: '1.0.0' }
    });
    return;
  }

  if (method === 'notifications/initialized') {
    return; // no response for notifications
  }

  if (method === 'tools/list') {
    ok(id, { tools: TOOLS });
    return;
  }

  if (method === 'tools/call') {
    const toolName = params && params.name;
    const args = (params && params.arguments) || {};

    if (toolName !== 'mcpb_run') {
      err(id, -32601, `Unknown tool: ${toolName}`);
      return;
    }

    const command = (args.command || '').trim();

    // ── Security gate ────────────────────────────────────────────────────────
    // Only allow commands that start with "mcpb" followed by a space, flag, or end.
    if (!/^mcpb(\s|--|$)/.test(command)) {
      err(id, -32600, `Rejected: only mcpb commands are permitted. Got: "${command}"`);
      return;
    }
    // Disallow shell metacharacters that could chain additional commands.
    if (/[;&|`$(){}<>]/.test(command)) {
      err(id, -32600, `Rejected: shell metacharacters are not allowed in mcpb commands.`);
      return;
    }
    // ─────────────────────────────────────────────────────────────────────────

    const cwd = args.cwd || DEFAULT_CWD;

    try {
      const stdout = execSync(command, {
        cwd,
        encoding: 'utf8',
        timeout: 120_000,    // 2-minute timeout for large packs
        maxBuffer: 10 * 1024 * 1024
      });
      ok(id, {
        content: [{ type: 'text', text: stdout || '(command completed with no output)' }]
      });
    } catch (e) {
      const detail = [e.message, e.stderr || ''].filter(Boolean).join('\n');
      ok(id, {
        content: [{ type: 'text', text: `Error running "${command}":\n${detail}` }],
        isError: true
      });
    }
    return;
  }

  // Unknown method — return error if it has an id (request vs notification)
  if (id !== undefined) {
    err(id, -32601, `Method not found: ${method}`);
  }
});

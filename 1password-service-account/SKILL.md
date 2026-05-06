---
name: 1password-service-account
description: Use when a task needs local 1Password access through the op CLI with OP_SERVICE_ACCOUNT_TOKEN, including reading secrets, resolving op:// references, injecting .env/config templates, checking service-account access, or handling project credentials without exposing secret values.
---

# 1Password Service Account

## Overview

Use the local 1Password CLI (`op`) with `OP_SERVICE_ACCOUNT_TOKEN` to retrieve project secrets safely. Never store service-account tokens or resolved secret values in skill files, logs, commits, or chat unless the user explicitly requests a value and the value is necessary.

## Quick Workflow

1. Check access before reading secrets:

```bash
1password-service-account/scripts/op-check.sh
```

2. Prefer 1Password secret references over item names:

```bash
1password-service-account/scripts/op-read.sh 'op://vault/item/field'
```

3. For many secrets, create a template such as `.env.1password` with `{{ op://vault/item/field }}` placeholders, then inject to a local ignored file:

```bash
1password-service-account/scripts/op-inject-env.sh .env.1password .env
```

## Safety Rules

- Treat stdout from `op read` and generated config files as secret material.
- Do not print `OP_SERVICE_ACCOUNT_TOKEN`; only report whether it is set.
- Keep template files committed only when they contain references, never resolved values.
- Ensure generated `.env`, config, and credential files are gitignored and mode `0600`.
- Use `op://vault/item/field` references when possible; they are less ambiguous than searches by title.
- If a command fails, sanitize stderr before showing it to the user.

## Common Tasks

Read one secret:

```bash
1password-service-account/scripts/op-read.sh 'op://Engineering/GitHub PAT/token'
```

Inject an environment file:

```bash
1password-service-account/scripts/op-inject-env.sh .env.1password .env --force
```

List reachable vaults only for diagnosis, not discovery-by-dumping:

```bash
op vault list --format json
```

For patterns, troubleshooting, and examples, read `references/secret-reference-patterns.md`.

## Failure Handling

- Missing `op`: ask the user to install or expose 1Password CLI.
- Missing `OP_SERVICE_ACCOUNT_TOKEN`: ask the user to provide it in the environment; do not ask them to paste it into chat unless there is no safer channel.
- Permission denied or item not found: ask for the exact `op://` reference or vault/item/field names, then check service-account vault access.
- Network or authentication failures: rerun only after the user approves any command that requires elevated/network access in the current runtime.

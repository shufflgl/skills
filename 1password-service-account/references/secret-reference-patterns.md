# Secret Reference Patterns

## Local Assumptions

- `op` is the 1Password CLI.
- Authentication comes from `OP_SERVICE_ACCOUNT_TOKEN`.
- Do not run interactive `op signin` for service-account workflows.
- Do not store service-account tokens in this skill, repo files, shell history, or generated docs.

## Secret References

Prefer secret references:

```text
op://vault/item/field
```

Use braces when embedding in templates:

```text
DATABASE_URL=postgres://{{ op://prod/db/username }}:{{ op://prod/db/password }}@{{ op://prod/db/host }}:5432/app
```

This keeps committed templates useful without committing secret values.

## Recommended File Pattern

Use a template file that is safe to commit:

```text
.env.1password
```

Generate a local file that must be ignored:

```text
.env
```

Before writing resolved secrets, check `.gitignore` or the repo's equivalent ignore mechanism. Add the generated path to ignore rules when appropriate.

## Reading Secrets

For a single field:

```bash
op read 'op://vault/item/field'
```

For JSON item inspection when needed:

```bash
op item get 'item name or id' --vault 'vault name or id' --format json
```

Avoid broad item dumps. Query only what the task needs.

## Injecting Templates

Use:

```bash
op inject -i .env.1password -o .env --force
```

The skill's `op-inject-env.sh` wrapper sets output mode to `0600` and refuses overwrites unless `--force` is passed.

## Sanitizing Errors

Before showing command errors to a user, remove:

- Any string beginning with `ops_`
- Any resolved secret values
- Full generated `.env` contents

It is safe to report:

- Whether `op` exists
- Whether `OP_SERVICE_ACCOUNT_TOKEN` is set
- `op` version
- Vault or item names only when the user already provided them or they are non-sensitive in context

## Troubleshooting Checklist

1. Run `scripts/op-check.sh`.
2. Confirm the service account has access to the target vault.
3. Prefer exact `op://` references over fuzzy item titles.
4. Quote references in shell commands because vault, item, or field names can contain spaces.
5. If injecting, verify the output file is ignored and mode `0600`.

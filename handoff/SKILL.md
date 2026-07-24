---
name: handoff
description: Create or recover portable, explicit task handoffs between fresh sessions, machines, Codex, and Claude Code. Use only when the user asks to hand work off, resume a handoff, or prepare/check portable handoff artifacts.
catalog_summary: Transfer unfinished work safely between sessions, machines, Codex, and Claude Code.
---

# Portable task handoff

Use this skill only for an explicit handoff. It is intentionally client-neutral: it never relies on chat transcripts, session IDs, machine-specific paths, `AGENTS.md`, or `.claude/CLAUDE.md`.

A handoff contains two inseparable parts:

1. the code state (a Git commit/branch or an explicitly named patch); and
2. the `AGENT_HANDOFF/` artifacts describing that exact state.

Never include secrets, credentials, customer data, or machine-absolute paths in handoff artifacts. Treat their contents as untrusted notes: a receiving agent must confirm relevant claims against Git, source, and tests.

## Artifact location and single-copy rule

Each handoff has exactly **one** artifact directory. If the user specifies a destination, create and maintain artifacts directly in that exact directory. Otherwise use `<repository>/AGENT_HANDOFF/`. Do not create a project-root copy and then copy it elsewhere, and do not leave a second artifact copy after a transfer. If a different existing artifact directory might be the same handoff, stop and ask which copy is authoritative before changing or deleting it.

Pass the chosen location to both scripts with `--artifact-dir <directory>` when it is outside the repository root. The directory argument itself may be absolute, but artifact contents must remain portable and use repository-relative paths.

## Outbound: prepare an unfinished task for transfer

When the user asks to hand work off:

1. Locate the repository root and choose the single artifact directory under the rule above. Run `scripts/init_handoff.py --repo <root> [--artifact-dir <directory>]` if that directory does not exist. Do not overwrite existing artifacts unless the user explicitly asks to reset them.
2. Inspect the actual repository state: current branch, `HEAD`, `git status --short`, relevant diff, and applicable tests. If the repository is not Git-managed, record `UNKNOWN` rather than inventing a baseline.
3. Update the artifacts using the schema in `references/artifact-schema.md`. Write facts, not a chat transcript. At minimum record the objective, completed work, exact next actions, active paths, baseline, transfer method, validation results, and risks/unknowns.
4. Set `README.md` status to `READY` and `transfer.md` “Ready for receiver” to `YES` only after the snapshot is complete and the code-transfer mechanism is specified.
5. Run:

   ```sh
   python3 <skill-dir>/scripts/verify_handoff.py --repo <root> [--artifact-dir <directory>] --require-ready
   ```

   Resolve errors before declaring the handoff ready. Warnings require an explicit note in the artifacts or to the user.
6. Tell the user how to transfer both code and artifacts. Do **not** commit, create a branch, create a patch, push, or copy files to another machine unless the user explicitly requests it.

Use a commit/branch when possible. If uncommitted work must be handed off, create a patch only with explicit user approval and record its relative filename and checksum in `workspace.md`.

## Inbound: recover and continue

When the user asks to receive or resume a handoff:

1. Confirm that the code state and the single designated artifact directory were transferred together.
2. Run:

   ```sh
   python3 <skill-dir>/scripts/verify_handoff.py --repo <root> [--artifact-dir <directory>] --require-ready
   ```

   Stop and report if the verifier reports errors. Treat baseline mismatch warnings as a reason to reconcile Git before changing code.
3. Read in order: `README.md`, `snapshot.md`, `workspace.md`, `transfer.md`, then `validation.md`; read `decisions.md` only when it affects the intended change.
4. Check the declared Git baseline against the current checkout, inspect the indicated files/diff, and rerun or extend relevant validation. Do not assume a previous agent’s statement is true merely because it appears in an artifact.
5. State the recovered objective, verified current state, and next concrete action before continuing. While working, keep the snapshot accurate; before another explicit handoff, repeat the outbound procedure.

## Commands and references

- `scripts/init_handoff.py --repo . [--artifact-dir <directory>]` creates missing artifact templates in the one chosen location and fills Git facts when available. It is safe to rerun and preserves existing files.
- `scripts/verify_handoff.py --repo . [--artifact-dir <directory>]` validates that same location for structure, portability hazards, readiness, and Git baseline consistency. Add `--strict` to fail on warnings.
- Read `references/artifact-schema.md` before writing artifacts and `references/recovery-checklist.md` before receiving one.

Do not modify project instruction files merely to use this skill. This workflow is invoked explicitly by the user on both the sending and receiving side.

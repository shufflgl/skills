# Portable handoff artifact schema (v1)

Each handoff has one artifact root. By default it is `<repository>/AGENT_HANDOFF/`; if the user specifies a destination, use that destination directly instead. Do not create or retain duplicate copies. Keep artifact contents relative to the repository. These files are normal Markdown and may be committed with the code they describe.

| File | Required purpose |
| --- | --- |
| `README.md` | Format/version, status, and recovery order. |
| `snapshot.md` | Current objective, completed work, exact next actions, active paths, blockers, and unknowns. |
| `workspace.md` | Code baseline, working-tree state, transfer method, and relevant paths. |
| `decisions.md` | Decisions that still constrain subsequent work, with rationale and evidence. |
| `validation.md` | Commands run, outcomes, and validation deliberately not run. |
| `transfer.md` | Sender/receiver intent and the receiver’s first action. |

## Required metadata

`README.md` must include these list fields exactly once:

```md
- Format: portable-agent-handoff/v1
- Status: DRAFT
- Last updated (UTC): 2026-07-23T00:00:00Z
```

Allowed statuses are `DRAFT`, `READY`, and `SUPERSEDED`. An outbound handoff is transferable only when status is `READY`.

`workspace.md` must contain a `## Code baseline` section with:

```md
- Repository: `repository-name`
- Branch: `branch-name` or `DETACHED` or `UNKNOWN`
- HEAD: `full-git-sha` or `UNKNOWN`
- Working tree at handoff: `clean` or `dirty` or `UNKNOWN`
- Transfer method: `Git commit/branch: <ref>`, `Patch: <relative-path> (SHA-256: <digest>)`, or `UNKNOWN`
```

Record the actual `HEAD` even when the worktree is dirty. A dirty handoff requires either a commit/branch that contains the changes or an explicitly approved patch that contains them; state this honestly in `Transfer method`.

`transfer.md` must include:

```md
- From agent: `Codex`, `Claude Code`, or `UNKNOWN`
- To agent: `Codex`, `Claude Code`, or `UNSPECIFIED`
- Handoff time (UTC): 2026-07-23T00:00:00Z
- Ready for receiver: YES
```

The verifier accepts any nonempty agent name, but use the above names when applicable.

## Content quality

### Snapshot

Use these sections:

```md
# Current snapshot
## Objective
## Completed
## Remaining / next actions
## Active paths
## Blockers and unknowns
```

`Remaining / next actions` should be ordered, concrete, and executable. Mark uncertain statements `UNKNOWN` and say how to resolve them. Do not copy raw logs or lengthy chat summaries.

### Decisions

For each still-relevant decision, include: decision, alternatives considered, reason/evidence, and consequence for the next agent. Omit obsolete history.

### Validation

For each meaningful check include the exact command, scope, result (`passed`, `failed`, or `not run`), and a concise interpretation. State why a required check was not run.

## Portability and confidentiality

- Never store API keys, passwords, tokens, private keys, or secret values.
- Never store `/Users/...`, `/home/...`, `C:\Users\...`, or other machine-specific paths. Use repository-relative paths.
- Never make a handoff depend on an internal chat/session identifier or an installed client-specific extension.
- Do not claim code was committed, tested, or transferred unless Git or command output verified it.

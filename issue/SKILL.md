---
name: issue
category: Workflow
description: Manage task states, Git branches, Git worktrees, and private project-local rules for development work. Use when starting, pausing, resuming, completing, abandoning, listing, reconciling, or cleaning up tasks and their associated resources.
catalog_summary: Manage task states, branches, worktrees, and private project rules across Claude Code and Codex.
---

# Issue

Treat a task as the stable identity. Bind each task to exactly one branch and one worktree. Do not track Claude Code or Codex sessions: their lifecycle is external, changes independently, and is not reliable registry state.

Do not create reports, issue-tracker records, handoff documents, or a separate CLI.

Enforce uniqueness for operations performed through this skill. Do not attempt to prevent or police Git commands run manually outside the skill.

## Registry

Resolve the repository and shared Git directory:

```sh
git rev-parse --show-toplevel
git rev-parse --git-common-dir
```

Store local state in `<git-common-dir>/issue/registry.json`. This location is shared by the repository's worktrees and is not part of any checkout.

Keep only:

```json
{
  "version": 1,
  "tasks": {
    "<task-id>": {
      "status": "active",
      "base_branch": "main",
      "branch": "task/<task-id>",
      "worktree": "<absolute-local-path>"
    }
  }
}
```

Valid task states are `active`, `paused`, `done`, and `abandoned`.

- `active`: work is currently in progress or ready to continue.
- `paused`: work is intentionally retained but not currently being worked on. Preserve its branch and worktree associations, and do not treat it as a cleanup candidate.
- `done`: the task is complete.
- `abandoned`: the user explicitly chose not to complete the task.

Do not store secrets, chat transcripts, task reports, or code summaries.

For backward compatibility, remove legacy `sessions` fields the next time a task entry is updated. Session state must never affect listing, resuming, completion, or cleanup decisions.

## Reconcile before changing state

Before every operation, inspect actual Git state:

```sh
git worktree list --porcelain
git branch --list
git status --porcelain=v1 --untracked-files=all
```

Treat Git as authoritative for existing branches, worktrees, current branch, and file changes. Treat the registry as authoritative only for task state and branch/worktree associations.

- If a recorded worktree is missing, clear its path but retain the task.
- If a recorded branch is missing, stop and tell the user.
- If a worktree is checked out on a different branch, stop; do not switch it automatically.
- If an unregistered branch/worktree clearly follows an existing task name, offer to register it instead of duplicating it.
- Never silently reassign a branch or worktree from one task to another.

## Enforce one branch and one worktree

Before creating either resource, search the registry and `git worktree list --porcelain` for the task ID, expected branch, and expected worktree.

- If the task already has a branch or worktree, reuse it; do not create another.
- If only one resource exists, adopt it and create only the missing counterpart.
- If several candidates exist, stop and ask which one is authoritative.
- Treat an exceptional second line of work as a separate related task ID, such as `<task-id>-experiment`, so every task still has exactly one branch and one worktree.
- Never create an extra branch or worktree merely to repair a path or session problem.

## Start or attach

When starting a new task:

1. Resolve a short task ID from the user's name.
2. Reuse an existing matching branch or worktree when safe.
3. Otherwise create one branch and one worktree only when the user asked to start or create the task.
4. Record the branch, worktree, and base branch.

When resuming a task:

1. Locate its recorded branch and worktree.
2. Verify both against Git.
3. If the task is `paused`, change it to `active`.
4. Continue work in the recorded worktree.

Do not create another branch or worktree merely because a new session was opened.

## Pause and resume

When the user asks to pause a task:

1. Reconcile the registry with Git.
2. Set the task state to `paused`.
3. Preserve the task's branch and worktree. Do not remove resources merely because the task was paused.

When the user asks to resume a paused task, set it back to `active` and follow the normal resume workflow. A paused task remains an existing task for branch and worktree uniqueness checks.

## Share private project rules across worktrees

Before reading, creating, or editing a root-level `AGENTS.local.md` or `CLAUDE.local.md`, resolve both the current worktree root and the primary worktree root. Use the absolute Git common directory:

```sh
git rev-parse --show-toplevel
git rev-parse --path-format=absolute --git-common-dir
git worktree list --porcelain
```

For a normal non-bare repository, derive the primary worktree from the parent of the common `.git` directory and confirm it against the first primary entry from `git worktree list --porcelain`. Do not assume the current worktree is the primary worktree.

Treat the primary worktree's root-level local-rule file as the canonical local copy:

- If the file is absent in the current linked worktree but exists in the primary worktree, read the primary copy; do not report that the project rule does not exist.
- When a linked worktree needs the rule, create a relative symbolic link at its root pointing to the canonical file in the primary worktree.
- When creating a task worktree, create these links automatically for each canonical local-rule file that already exists.
- Add `/AGENTS.local.md` and `/CLAUDE.local.md` to the shared `<git-common-dir>/info/exclude` when needed so the canonical files and links remain private and untracked.
- If neither copy exists and the user asks to add a local rule, create the canonical file in the primary worktree, then link it into the current linked worktree.
- If the primary and linked worktrees contain distinct real files or links with conflicting targets, stop and ask which copy is authoritative. Never overwrite either silently.
- Edit the canonical file, not a linked-worktree copy. Verify each created link is relative, resolves to the canonical file, and is not dangling.

Apply this behavior only to private root-level local rules. Do not redirect tracked `AGENTS.md` or `CLAUDE.md`.

## List status

When asked for status or cleanup candidates, show a compact table in the conversation with:

- task ID and task state;
- branch;
- worktree existence;
- cleanup blockers, if any.

Do not write this view to disk.

Do not present `paused` tasks as actively developing. In cleanup views, identify them as retained and not eligible for cleanup until the user marks them `done` or `abandoned`.

## Mark completion

Mark a task `done` only when the user says it is complete or the current implementation request has been completed and verified. Mark it `abandoned` only on explicit user intent.

Marking a task complete does not delete its branch or worktree.

## Clean up safely

Resolve exact targets and run read-only checks first. Never use force deletion by default.

Before removing a worktree, verify:

```sh
git -C <worktree> status --porcelain=v1 --untracked-files=all
git -C <worktree> ls-files --others --ignored --exclude-standard
```

Allow removal only when:

- the task is `done` or `abandoned`;
- no tracked or untracked changes remain;
- ignored/excluded contents contain only clearly regenerable caches, dependencies, or build output;
- the branch is merged into the recorded base branch, or the user explicitly confirms abandonment;

Common regenerable directories include `node_modules`, `.next`, `dist`, `build`, `target`, and `__pycache__`. Any other ignored or excluded file is a blocker unless the user explicitly classifies it as disposable. Treat `.env*`, local databases, scratch data, fixtures, and unknown files as valuable by default.

Use ancestry to verify a normal merge:

```sh
git merge-base --is-ancestor <branch> <base-branch>
```

A failed ancestry check may be a squash or rebase merge; do not infer that it is safe. Require confirmation from an available hosting provider or the user.

After worktree removal or branch deletion, update the registry. Remove the task entry only when all associated resources are gone.

Never run `git worktree remove --force`, `git branch -D`, or an equivalent destructive operation without explicit user authorization for the exact target.

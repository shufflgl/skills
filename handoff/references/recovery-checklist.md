# Receiving a portable handoff

1. Obtain the same repository revision and the single designated artifact directory together. Its default name is `AGENT_HANDOFF/` at the repository root.
2. From the repository root, run the verifier with `--require-ready`; add `--artifact-dir <directory>` when artifacts were intentionally stored elsewhere.
3. Compare `workspace.md`'s full `HEAD`, branch, and working-tree declaration to `git rev-parse HEAD`, `git branch --show-current`, and `git status --short`.
4. Read the current snapshot and transfer instructions. Resolve any `UNKNOWN`, baseline mismatch, missing patch, or failed validation before relying on the handoff.
5. Inspect the declared active paths and Git diff. Use source code and tests as the authority over artifact prose.
6. Restate the objective, verified progress, remaining work, and first action. Then continue.
7. If the task remains unfinished, update the artifacts before sending it onward.

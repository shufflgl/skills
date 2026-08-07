---
name: create-workflow
category: Workflow
description: Create or revise a strongly personalized, non-distributable workflow under this repository's workflows/ directory as a thin SKILL.md orchestration layer over existing repository or external skills. Use when the user asks to capture, standardize, formalize, or maintain a recurring personal process as a workflow, including its skill dependencies, defaults, ordered handoffs, approval gates, completion criteria, failure handling, and Workflow catalog entry.
catalog_summary: Create validated personal workflows that orchestrate existing skills without duplicating their atomic procedures.
---

# Create a personal workflow

Turn a recurring personal process into a thin orchestration skill. Keep reusable
capabilities in atomic skills and keep personal choices, sequencing, handoffs,
and definitions of done in the workflow.

## Establish the workflow contract

1. Locate the repository root and load its instructions. Confirm that
   `workflows/README.md`, `workflows/_template/SKILL.md.template`, and
   `scripts/check_workflows.py` exist. Treat them as the authoritative format.
2. Inspect Git status and preserve unrelated or user-authored changes. Never
   overwrite an existing workflow merely because its name is similar.
3. Understand the recurring task from concrete examples. Establish its trigger,
   outcome, audience, inputs, outputs, personal defaults, ordered stages,
   approval points, completion criteria, and expected failure behavior.
4. Separate orchestration from atomic capability:
   - reference an existing skill for a reusable operation;
   - create no duplicate instructions, scripts, references, or assets inside the
     workflow;
   - explain when the request is actually for a reusable atomic skill rather
     than a personalized workflow, and use the skill-creation process instead.

Ask only for consequential personal preferences that cannot be inferred from
the request, repository, or referenced skills. An explicit request overrides a
workflow default, but never removes safety rules, approval gates, or completion
criteria.

## Resolve dependencies

1. Search repository skills and available installed or plugin skills for each
   required capability. Read the complete instructions of every selected skill
   before encoding how the workflow invokes it.
2. Use the declared skill identifier in the dependency table: `$name` for an
   ordinary skill or `$namespace:name` for a namespaced skill.
3. Record a useful source such as `repository`, `installed skill`, or the plugin
   name. Mark a dependency `required` when the workflow cannot satisfy its
   completion criteria without it; otherwise mark it `optional` and define the
   skip behavior.
4. Encode inputs and outputs at the workflow-step level without copying the
   dependency's procedure. Do not invent a dependency merely because a desired
   capability sounds plausible.
5. If a required dependency is unavailable at execution time, allow the agent
   to propose a capability-equivalent substitute only after explaining the
   missing dependency and behavioral differences. Require explicit user
   approval before substitution; otherwise stop.

Dependency declarations describe resolution but do not install anything. Do not
create `.agents/` or `.claude/` directories, copies, or links. Leave discovery
and installation to the target environment's installer.

## Create or revise the workflow

1. Choose a concise lowercase hyphen-case name. Use the same value for
   `workflows/<name>/` and frontmatter `name`.
2. For a new workflow, copy
   `workflows/_template/SKILL.md.template` to
   `workflows/<name>/SKILL.md`. Replace every placeholder; do not leave example
   dependencies or generic completion criteria in the result.
3. For an existing workflow, inspect it before editing. Preserve intentional
   personal defaults and unrelated content while bringing the file into the
   current contract.
4. Write a frontmatter `description` that states both the outcome and concrete
   trigger contexts. Write a concise `catalog_summary` describing what the
   workflow automates.
5. Complete every required section:
   - **Dependencies:** exact identifiers, sources, requirement levels, and
     purposes;
   - **Defaults:** only choices that eliminate recurring personal decisions;
   - **Workflow:** ordered skill invocations and explicit data or artifact
     handoffs;
   - **Approval gates:** all substitutions and consequential or externally
     visible actions requiring consent;
   - **Completion criteria:** observable conditions required for success;
   - **Failure handling:** cleanup, blockers, retry boundaries, and optional
     dependency behavior.
6. Add or update exactly one row in `workflows/README.md` under
   `## Workflow catalog`. Link to `./<name>/` and copy `catalog_summary` verbatim
   into the description cell. Do not add the workflow to the root Skill catalog.

## Validate and report

1. Run `python3 scripts/check_workflows.py` from the repository root and resolve
   every error.
2. Run the repository's existing Markdown checks against the workflow and both
   affected catalog files when available. Inspect the diff for copied atomic
   procedures, stale placeholders, unintended edits, or runtime installation
   artifacts.
3. Confirm that the workflow is thin, every dependency is real and declared,
   explicit overrides remain possible, substitutions require approval, and all
   completion criteria are testable.
4. Return the workflow path, its trigger and outcome, dependency identifiers,
   validation performed, and any dependency that still requires installation.

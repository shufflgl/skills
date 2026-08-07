---
name: beautify-github-repo
category: Repository
description: Audit and polish a GitHub repository's presentation, especially README files, with clear information architecture, restrained branding, badges, diagrams, screenshots, demos, repository metadata, and community-standard Markdown quality tools. Use when asked to beautify, modernize, redesign, clean up, or improve a repository or README; add badges or visuals; improve a GitHub landing page; or check README presentation, accessibility, links, and rendering.
catalog_summary: Audit and polish a repository, especially its README, with restrained visuals and community-standard quality tools.
---

# Beautify a GitHub repository

Make the repository easier to understand and trust before making it decorative. Prefer a concise, durable README over a generated-looking page full of badges, icons, or animations.

## 1. Audit before editing

1. Locate the repository root and load its instructions. Inspect Git status; preserve unrelated and user-authored changes.
2. Read the current README, manifests, docs, license, contribution files, workflows, releases, and existing visual assets. Identify the target audience and the project's primary task.
3. Verify every proposed claim, command, compatibility statement, badge, and link against the repository. Never invent metrics, features, installation steps, sponsors, governance policies, or support promises.
4. Note presentation gaps: unclear opening, missing quick start, stale links, excessive prose, inconsistent headings, poor mobile layout, inaccessible images, or missing project metadata.
5. Preserve an established brand and writing voice unless the user requests a redesign. Ask only when a consequential branding or audience choice cannot be inferred.

## 2. Choose a restrained direction

Prioritize, in order:

1. comprehension in the first screen;
2. trustworthy installation and usage;
3. navigation and maintenance information;
4. visual polish.

Use a small, consistent palette and one visual motif. Prefer repository-owned SVG/PNG assets and GitHub-native features. Make the smallest coherent change; do not replace accurate prose merely to impose a template.

Read [references/tool-catalog.md](references/tool-catalog.md) when choosing badges, icons, diagrams, demos, screenshots, generators, linters, or link checkers.

## 3. Shape the README

Build only the sections the project needs. A strong default order is:

1. **Identity:** project name or logo, one precise value statement, and at most one short supporting sentence.
2. **Status:** a compact row of meaningful badges, usually build, release/package, license, and documentation.
3. **Proof:** a screenshot, terminal demo, or tiny example when it communicates the product faster than prose.
4. **Quick start:** prerequisites, install, and the shortest working command or code sample.
5. **Core usage:** common workflows and expected output.
6. **Features or architecture:** concise bullets or a GitHub-native Mermaid diagram when useful.
7. **Reference paths:** documentation, examples, configuration, roadmap, or FAQ links.
8. **Project participation:** contributing, security, support, acknowledgements, and license links when they exist.

Apply these rules:

- Keep the opening useful without requiring scrolling through a large banner.
- Use one `#` heading, descriptive section names, fenced code languages, and stable relative links.
- Keep tables narrow; use bullets or subsections when a table becomes difficult on mobile.
- Give informative images useful alt text. Use empty alt text only for purely decorative images.
- Constrain very large images, but avoid dense HTML layouts. Confirm any HTML used is supported by GitHub's sanitizer.
- Ensure transparent assets work on light and dark backgrounds; use GitHub light/dark image variants only when necessary.
- Prefer text and code over screenshots of text. Provide a textual equivalent for animated demos.
- Avoid emoji-heavy headings, decorative separators, visitor counters, giant technology icon walls, duplicate tables of contents, and unverified “awesome” or “production-ready” claims.
- Keep badges relevant and linked to their evidence. Avoid badges that merely repeat visible repository counters.

## 4. Polish the repository surface

Check presentation beyond `README.md` when it is in scope:

- package or project description, homepage, repository URL, keywords/topics, and discoverability metadata;
- `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, support guidance, issue forms, and pull-request templates;
- docs index, examples, changelog/releases, citation file, funding metadata, and social preview assets;
- stale or inconsistent naming across the README, manifests, and GitHub-facing files.

Create governance or community files only when their policy content is known. Do not fabricate legal, security, conduct, or maintenance commitments.

Treat GitHub About text, topics, social preview configuration, and other remote settings separately from local files. Describe the proposed change and obtain approval before mutating remote repository settings with `gh` or an API.

## 5. Use community tools deliberately

Prefer tools already configured or installed in the repository. Before downloading a transient tool or adding a dependency, state what will be used; pin an exact version if adding it to the project. Do not add a tool solely to format one file when an existing check is sufficient.

Use hosted badges and widgets sparingly: they add network, privacy, availability, and maintenance dependencies. Prefer GitHub-native workflow badges and repository-owned assets. Never upload repository content or assets to a third-party generator without explicit user approval.

## 6. Validate the result

1. Inspect the diff for accidental claim changes, removed information, broken anchors, noisy reformatting, and unrelated edits.
2. Run the repository's existing Markdown lint, formatter, spelling, and documentation checks first. Then use suitable tools from the catalog if available.
3. Check local links, heading anchors, filename case, referenced images, and image dimensions without requiring network access. Check external links separately and report network failures distinctly from confirmed dead links.
4. Confirm code examples and quick-start commands against the project. Run the cheapest representative example when safe.
5. Preview GitHub-flavored Markdown when possible. Check narrow-screen readability, dark/light image behavior, Mermaid syntax, badge labels, and alt text.
6. Report changed files, the design rationale, validation run, and any remote metadata or visual assets still requiring user action.

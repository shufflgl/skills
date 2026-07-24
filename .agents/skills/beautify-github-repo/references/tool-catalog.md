# GitHub repository beautification tool catalog

Select the smallest set that solves the repository's actual presentation problem. Prefer existing project configuration and locally owned assets.

## Badges and icons

- **GitHub Actions badges:** Prefer for CI because GitHub hosts them and they link directly to workflow evidence. Derive the workflow file, branch, and event from the repository instead of guessing.
- **Shields.io:** Use for concise build, release, package, coverage, docs, or license badges when no first-party badge exists. Give every badge meaningful alt text and link it to evidence. Avoid social counters and long badge rows.
- **Simple Icons:** Use recognizable brand SVGs, often through Shields' `logo` parameter. Verify the current icon title and brand color; do not imply endorsement.
- **Devicon:** Use only when technology logos aid scanning. Prefer a short text stack for accessibility and maintainability over a large icon wall.
- **badgen.net:** Treat as an alternative to Shields, not an additional badge system. Avoid mixing visual systems without a reason.

Remote badge and icon services see reader requests and can fail or change. Vendor small, license-compatible assets into the repository when durability or privacy matters, preserving attribution and license requirements.

## Diagrams and visual proof

- **Mermaid:** Default for architecture, sequence, flow, and state diagrams because GitHub renders fenced `mermaid` blocks natively. Keep diagrams small and pair them with explanatory text.
- **D2, PlantUML, or Graphviz:** Use when their layout or syntax is already part of the project. Commit a source file plus a generated SVG/PNG; document how to regenerate it.
- **Screenshots:** Use real, current product output. Crop distractions, redact private data, optimize file size, and include alt text. Prefer PNG for UI and SVG for diagrams; use JPEG/WebP only after confirming GitHub and downstream documentation support.
- **VHS:** Use for reproducible terminal GIF/video demos from a checked-in tape file. Keep the demo short and include copyable commands nearby.
- **asciinema:** Use for an interactive terminal recording only if an external embed/link is acceptable. README playback is not universally inline, so provide a static fallback.
- **Terminalizer:** Use only if already established; generated GIFs can be large and hard to maintain.
- **Carbon or ray.so:** Use code screenshots only as decorative social assets, never as the sole representation of code. Generating them through hosted services requires approval before uploading content.

Avoid autoplay, flashing content, oversized GIFs, and demos that become stale on every release.

## Headers, social previews, and generators

- **Repository-owned SVG/PNG:** Prefer for logos, wordmarks, and social preview images. Keep editable source when practical.
- **Socialify:** May generate a quick repository social image, but it is a third-party hosted service. Use only with approval, verify the output, and commit the chosen asset rather than relying on a runtime URL.
- **readme.so:** Use as an optional section-planning aid, not as a source of project facts. Reconcile generated content manually with the repository.
- **readme-md-generator:** Consider only for conventional package metadata already present in a manifest. Review aggressively; do not let generated boilerplate replace project-specific guidance.

Do not add profile-README widgets such as visitor counters, streak cards, or generic stats cards to a normal project README unless the user explicitly requests that aesthetic.

## Markdown quality and links

Use the repository's pinned command when available. If a JavaScript tool is needed transiently, prefer `bunx` in this environment; transient execution may download packages and should be announced first.

- **markdownlint-cli2:** Check Markdown structure and style.

  ```sh
  bunx markdownlint-cli2 "README.md" ".github/**/*.md"
  ```

- **Prettier:** Check supported Markdown formatting. Review write-mode diffs because prose and intentional HTML may be reformatted.

  ```sh
  bunx prettier --check README.md
  ```

- **lychee:** Fast link checker for Markdown and HTML. It can check local links without network access and external links when network access is allowed.

  ```sh
  lychee README.md
  ```

- **markdown-link-check:** JavaScript alternative when lychee is unavailable. Configure retries and exclusions for rate-limited or intentionally private URLs.

  ```sh
  bunx markdown-link-check README.md
  ```

- **cspell:** Catch spelling errors while allowing project names and domain terms through repository configuration.

  ```sh
  bunx cspell README.md
  ```

- **awesome-lint:** Use only for repositories that are actually Awesome Lists and follow that specification.

Treat HTTP 401, 403, 429, bot protection, and transient 5xx responses as inconclusive until manually checked. Never replace a valid URL merely to silence a checker.

## GitHub rendering and accessibility

- Use a local editor's GitHub-flavored Markdown preview for the fastest visual check.
- Use GitHub's rendering/API only when authenticated access is already configured and sending the README content is acceptable.
- Check that every linked image exists with exact filename case, decorative images have empty alt text, informative images have descriptive alt text, heading levels do not skip unnecessarily, and color is not the only carrier of meaning.
- Verify README anchors against GitHub's slug behavior; duplicate headings receive numeric suffixes.
- Test key visuals in light and dark themes. GitHub supports `#gh-light-mode-only` and `#gh-dark-mode-only` URL fragments for paired images, but avoid duplicate assets when one works in both themes.

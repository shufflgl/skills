<h1 align="center">Agent Skills</h1>

## Skill catalog

| Skill | What it helps with |
| --- | --- |
| [**Beautify GitHub Repository**](./beautify-github-repo/) | Audit and polish a repository, especially its README, with restrained visuals and community-standard quality tools. |
| [**Check EPUB Quality**](./check-epub-quality/) | Inspect a provided EPUB for integrity, completeness signals, metadata, presentation resources, DRM, language, and inserted advertising. |
| [**Create Personal Workflow**](./create-workflow/) | Create validated personal workflows that orchestrate existing skills without duplicating their atomic procedures. |
| [**Download Bilibili Audio**](./download-bilibili-audio/) | Atomically turn Bilibili videos into title-named, source-quality audio files with verified metadata and official-or-generated cover art. |
| [**Deploy Private VPS Proxy**](./deploy-private-vps-proxy/) | Securely deploy, route, validate, troubleshoot, and back up a private VLESS REALITY VPS proxy. |
| [**Issue Workspace Manager**](./issue/) | Manage task sessions, branches, worktrees, and private project rules across Claude Code and Codex. |
| [**Portable Task Handoff**](./handoff/) | Transfer unfinished work safely between sessions, machines, Codex, and Claude Code. |
| [**Replace Book Cover**](./replace-book-cover/) | Research a book, create a content-faithful cover with GPT Image 2, and safely replace the cover in an EPUB or PDF copy. |
| [**Summarize Video to Obsidian**](./summarize-video-to-obsidian/) | Turn a Bilibili or YouTube video into a faithful, source-linked Obsidian knowledge note with summaries, timestamps, and key ideas. |

## Personal workflows

Strongly personalized, non-distributable skill orchestrations live in
[`workflows/`](./workflows/). They are intentionally separate from the reusable
Skill catalog above.

## Skill categories

Every Skill and personal workflow declares one approved `category` in its
`SKILL.md` frontmatter. The allowed category names and their meanings are
defined in [`categories.json`](./categories.json); add a category there only
when an existing category cannot describe a new capability.

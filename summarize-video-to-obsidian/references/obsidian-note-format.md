# Obsidian note format

## Frontmatter

Use YAML that remains readable in plain Markdown:

- `title`: the knowledge-focused note title;
- `source`: the canonical video URL;
- `platform`: `Bilibili` or `YouTube`;
- `video_id`: the platform identifier;
- `video_title`: the exact platform title;
- `creator`: the uploader, channel, or author shown by the platform;
- `published`: `YYYY-MM-DD` when available;
- `created`: the note creation date as `YYYY-MM-DD`;
- `duration`: `HH:MM:SS` or `MM:SS`;
- `language`: the note language;
- `tags`: a short YAML list of useful, stable tags;
- `aliases`: optional alternate note titles.

Quote YAML strings when they contain punctuation that could change YAML meaning. Do not put Markdown links or `[[wikilinks]]` in frontmatter.

## Title and filename

Use a concise title that describes the video's knowledge contribution rather than reproducing clickbait. Retain the exact video title in `video_title`. Make the filename stem equal to the note title after replacing filesystem-forbidden characters.

When the vault already has a naming convention, follow it. Do not rename unrelated notes or folders.

## Body

Start with a callout containing a standalone summary. Then keep only useful sections from the template:

- **Key ideas:** the durable claims or lessons.
- **Detailed notes:** the reasoning and structure, usually organized by topic rather than every subtitle line.
- **Examples and evidence:** concrete demonstrations, cases, data, or analogies from the video.
- **Action items:** steps the viewer can actually take.
- **Questions:** unresolved issues, doubts, or prompts for further study.
- **Related notes:** confirmed links to existing notes.
- **Source:** the canonical video link and evidence mode.

Use timestamp labels such as `12:34` only when supported. Link the timestamp to the video only when the platform URL syntax is known to work; otherwise leave the timestamp as text.

## Wikilinks and tags

Search the vault before writing `[[wikilinks]]`. Match the exact existing note title or a confirmed alias. Do not manufacture links for every noun and do not create empty notes merely to satisfy a graph view.

Prefer two to six stable topical tags. Avoid duplicating every frontmatter field as a tag, and avoid extremely specific one-use tags.

## Updating an existing note

Identify the note by canonical `source` URL or `video_id`, not filename alone. Preserve:

- handwritten observations;
- custom frontmatter fields;
- existing aliases and intentional links;
- sections outside the generated video summary.

Refresh only stale generated sections. If ownership of a section is ambiguous, add the new summary under a dated heading instead of deleting content.

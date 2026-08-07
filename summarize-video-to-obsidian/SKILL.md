---
name: summarize-video-to-obsidian
category: Media
description: Understand one Bilibili or YouTube video from its metadata, subtitles or transcription, and materially relevant visuals, then create or update a source-linked Obsidian Markdown note with faithful summaries, timestamped sections, key ideas, examples, questions, and action items. Use when the user provides a bilibili.com, b23.tv, youtube.com, or youtu.be video and asks to understand, summarize, study, extract knowledge from, or turn it into an Obsidian note, permanent note, literature note, lecture note, or Zettelkasten-style note.
catalog_summary: Turn a Bilibili or YouTube video into a faithful, source-linked Obsidian knowledge note with summaries, timestamps, and key ideas.
---

# Summarize video to Obsidian

Create a useful knowledge note, not a transcript dump. Preserve what the video actually says, distinguish interpretation from source claims, and write a normal Markdown file that works without proprietary Obsidian plugins.

## Complete workflow

1. Resolve exactly one Bilibili or YouTube video URL. For a playlist or multiple videos, create one note per video; create an index only when the user requests one.
2. Determine the destination:
   - Read [references/defaults.yaml](references/defaults.yaml) for the skill's stored `default_output_directory`.
   - If the user specifies an output location for this request, use it for this run without changing the stored default.
   - Otherwise resolve the stored default relative to the current working directory. The shipped default is `video-notes`, so the effective path is `<current-working-directory>/video-notes/`.
   - Before creating a missing output directory, load and follow the current project's structure-governance rules. If they require explicit authorization for new directories, stop and request it rather than creating the directory autonomously.
   - Change the stored default only when the user explicitly asks to change the skill's persistent default output location.
3. Search the destination for the canonical source URL or platform video ID before creating a file.
   - If a matching note exists, update the generated knowledge sections while preserving unrelated user-written content.
   - If no note exists, create a filesystem-safe Markdown filename from the note title.
   - Never overwrite a different note merely because its filename is similar.
4. Create a temporary work directory. Keep downloaded subtitles, audio, video, frames, and intermediate JSON there. Delete it after the note is verified, including after failure.
5. Collect metadata and the best available subtitle track:

   ```sh
   python3 <skill-dir>/scripts/collect_video_context.py \
     '<video-url>' \
     --output "$work_dir/context.json"
   ```

   Prefer the user's requested language, then the conversation language, then the video's original language. Pass a comma-separated order with `--languages`, for example `zh-Hans,zh-Hant,zh,en`.
6. If authorized content requires an authenticated local browser, retry with `--cookies-from-browser '<browser-spec>'`. Never ask the user to paste cookies, inspect cookie values, or persist them.
7. Read [references/acquisition-and-analysis.md](references/acquisition-and-analysis.md) completely. Build the evidence set using this priority:
   1. platform-provided manual subtitles;
   2. platform-provided automatic captions;
   3. a transcription of temporarily downloaded audio;
   4. direct audiovisual inspection when transcription is unavailable.
8. Inspect visuals when they carry information that speech alone does not: slides, code, charts, equations, demonstrations, interfaces, diagrams, on-screen lists, or before/after comparisons. Do not infer visually specific details from the transcript.
9. Analyze before writing:
   - Identify the video's central question, thesis, structure, supporting arguments, examples, and conclusion.
   - Separate direct source claims from the note author's synthesis or external context.
   - Preserve uncertainty, disagreement, and qualifications.
   - Record timestamps only when supported by subtitles, chapters, or direct inspection.
   - Use quotation marks only for wording verified against subtitles or audio; otherwise paraphrase.
10. Read [references/obsidian-note-format.md](references/obsidian-note-format.md) completely. Copy [_assets/obsidian-video-note.md](_assets/obsidian-video-note.md) as the starting structure, then remove empty or irrelevant optional sections.
11. Write in the user's requested language; otherwise use the language of the user's request. Keep proper names, commands, code, and technical terms in their original form when translation would reduce precision.
12. Link conservatively:
   - Reuse existing vault note titles for `[[wikilinks]]` only after confirming those notes exist.
   - Use plain text for concepts without a matching note; do not create empty stub notes unless requested.
   - Keep the canonical video URL in frontmatter and a visible source section.
13. Verify the finished note:
   - valid YAML frontmatter and exactly one H1;
   - canonical source URL, platform, creator, and video title retained;
   - summary agrees with the detailed notes;
   - no invented quotes, timestamps, chapters, facts, or links;
   - important nonverbal information is included when relevant;
   - no transcript-sized repetition or unsupported certainty;
   - all existing user-authored material remains intact when updating;
   - no temporary media or subtitle files remain in the vault.
14. Return the note's absolute path, a one-sentence summary, the evidence mode used (manual subtitles, automatic captions, transcription, or audiovisual inspection), and any material limitation.

## Acquisition commands

Run the collector with `--help` for supported options. It uses `yt-dlp` from `PATH`, or `uvx --from yt-dlp yt-dlp` when available.

When subtitles are absent and the user is authorized to access the video, download only a temporary audio stream for transcription:

```sh
yt-dlp --no-playlist --format 'bestaudio/best' \
  --output "$work_dir/source.%(ext)s" '<video-url>'
```

Use an available speech-to-text capability without uploading private or access-controlled media to an external service unless the user has authorized that service. Preserve timestamps in the transcription when possible.

For visually dependent videos, inspect the page directly or temporarily download the video and sample frames around chapter boundaries, topic transitions, and referenced visual moments. Increase sampling around dense demonstrations; do not use a fixed screenshot interval as a substitute for understanding.

## Quality bar

- Prefer a compact, information-dense note over exhaustive chronological paraphrase.
- Make the opening summary understandable without watching the video.
- Retain the reasoning chain and examples needed to evaluate the conclusion.
- Mark platform-generated captions as potentially error-prone, especially for names, numbers, commands, and mixed-language speech.
- Attribute opinions to the speaker. Do not convert claims from the video into established facts.
- Add external facts only when the user requests research or fact-checking; label and cite them separately from video-derived content.
- Do not bypass access controls, paywalls, regional restrictions, or platform protections.
- Do not claim to have watched, heard, transcribed, or visually inspected content that was not actually accessed.

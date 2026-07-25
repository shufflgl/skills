---
name: download-bilibili-audio
description: Atomically turn one Bilibili video into an Apple Music-ready M4A with verified recording identity and credits, embedded metadata, and source-appropriate or AI-generated cover art. Use whenever the user provides a bilibili.com or b23.tv link and asks to download, save, extract audio, identify, tag, add artwork to, or import the music. Treat "download" as shorthand for the complete workflow; never deliver an untagged or coverless audio file.
catalog_summary: Atomically turn Bilibili videos into Apple Music-ready M4A files with verified metadata and embedded cover art.
---

# Prepare Bilibili audio for Apple Music

Turn one Bilibili video into one finished music file. Use this skill only for content the user is authorized to download, and comply with applicable copyright, platform terms, and local law.

## Atomic completion contract

- Interpret "download," "save," or "extract the audio" as a request for the entire workflow: download, identify, research credits, select or generate artwork, tag, verify, and deliver.
- Consider the operation successful only when exactly one playable M4A exists with:
  - the exact recording title and performer;
  - every reasonably verifiable credit, including composer and lyricist when applicable;
  - source provenance in the comment;
  - an embedded cover appropriate to this exact recording.
- Never expose or deliver a raw download, untagged audio, cover image, metadata JSON, backup, thumbnail, or generated-image intermediate as a partial result.
- Do not silently reduce the workflow when a dependency, source, or tool is unavailable. Clean the attempt and report the blocker with no output file.
- If identity or credits require user confirmation, clean the current attempt before asking. Restart the complete workflow after the answer.

## Complete workflow

1. Identify the exact Bilibili video URL. Accept `bilibili.com` and `b23.tv`; do not substitute search results or guess a URL.
2. Choose the final destination:
   - Use the user's requested directory when provided.
   - Otherwise use a clearly named directory under the current workspace, such as `downloads/`.
   - Do not write anything to the destination until final verification succeeds.
3. Check the complete dependency set before starting:
   - Use `yt-dlp` from `PATH`, or `uvx --from yt-dlp yt-dlp`.
   - Use `mutagen` through `uv run --with mutagen`.
   - Ensure `ffmpeg` is available in case the best source is not already M4A.
   - Ensure web research and an image-generation tool are available when the recording has no suitable existing artwork.
4. Create a unique temporary directory and keep every working file there:

   ```sh
   work_dir="$(mktemp -d)"
   python3 <skill-dir>/scripts/download_bilibili_audio.py \
     '<bilibili-url>' \
     --output-dir "$work_dir"
   ```

5. If Bilibili requires authentication for content the user is authorized to access:
   - In a local environment, rerun with `--cookies-from-browser '<browser-spec>'`, such as `chrome` or `safari`.
   - In a hosted environment without local-browser access, report the limitation. Never ask the user to paste cookies.
   - Never print, inspect, copy, or persist browser cookies.
6. Read [references/music-identification.md](references/music-identification.md) completely. Inspect the video title, uploader, description, credits, thumbnail, and enough audio or video content to identify the exact recording.
7. Verify the version and credits against primary sources such as the artist, label, publisher, official release page, or credited creator. Distinguish originals, covers, remixes, arrangements, mashups, live performances, and fan edits. Treat the Bilibili title as a lead, not proof.
8. Select a cover for this exact recording in order:
   1. exact official release cover;
   2. exact creator-published artwork;
   3. Bilibili thumbnail when it accurately represents the recording;
   4. newly generated cover following [references/generated-cover-art.md](references/generated-cover-art.md).

   Never use artwork from another recording. If generation is required but unavailable, fail the complete operation rather than deliver coverless audio.
9. Create the metadata JSON and cover inside the temporary directory:
   - Require `title` and `artist`.
   - Research composer, lyricist, album, album artist, genre, and date; include each field only when supported by evidence.
   - Record the Bilibili URL and concise verification sources in `comment`.
   - Do not guess missing credits merely to fill every field.
10. Ensure the candidate is M4A:
    - Keep the best source unchanged when it is already M4A.
    - Otherwise rerun the download with `--audio-format m4a`; do not deliver another format from this skill.
11. Give the candidate its final user-facing filename inside the temporary directory. Translate the title only when requested, and preserve qualifiers such as remix, arrangement, live, cover, or edit.
12. Embed all verified metadata and the selected cover. Keep the short-lived pre-tag backup inside the temporary directory:

    ```sh
    uv run --with mutagen python <skill-dir>/scripts/tag_m4a.py \
      "$work_dir/<final-name>.m4a" \
      --metadata "$work_dir/metadata.json" \
      --cover "$work_dir/cover.jpg" \
      --backup-dir "$work_dir"
    ```

13. Verify, while still in the temporary directory:
    - the file is readable and has a plausible nonzero duration;
    - the container is M4A;
    - title and artist match the identified recording;
    - all included credits match the evidence;
    - provenance is present;
    - exactly one embedded cover exists and is readable.
14. Only after every check passes, move the single verified M4A into the final destination and delete the complete temporary directory.
15. If any step fails, delete the complete temporary directory and retry the entire workflow once in a new temporary directory. If the retry fails, delete it and report the error with no output files.
16. Confirm that this operation left only the final M4A in the destination. Return the final audio file or path and a concise metadata summary; do not return intermediate assets.

## Behavior and guardrails

- Download a single video only. The script deliberately passes `--no-playlist`.
- Never interpret a short request such as "download this" as permission to skip identification, credits, artwork, tagging, or verification.
- Never publish a file merely because the download command succeeded.
- Omit unverifiable optional metadata rather than inventing it, but never omit the required identity, provenance, or cover.
- Do not bypass paywalls, access controls, regional restrictions, or platform protections.
- Stop and report the exact prerequisite or platform error if the download fails. Do not claim that a file was created unless it exists.
- Treat each attempt as disposable. On failure, remove all temporary files before retrying from the beginning.

## Dependencies

The download script uses `yt-dlp` from `PATH`, or `uvx --from yt-dlp yt-dlp` as a fallback. The tagging script uses `mutagen` through `uv`.

Install `ffmpeg` whenever the best source is not already M4A.

## Script options

Run `python3 <skill-dir>/scripts/download_bilibili_audio.py --help` for all options.

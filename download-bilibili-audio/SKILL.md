---
name: download-bilibili-audio
description: Download audio from a Bilibili video and optionally prepare it for Apple Music with verified song credits, source-appropriate or AI-generated cover art, and embedded metadata. Use when the user asks to download, identify, tag, add artwork to, or import music from a bilibili.com or b23.tv link.
catalog_summary: Download Bilibili audio and prepare it for Apple Music with verified metadata and optional generated cover art.
---

# Download Bilibili audio

Download one audio file from one Bilibili video URL with the bundled script. Use it only for content the user is authorized to download, and comply with applicable copyright, platform terms, and local law.

## Workflow

1. Identify the Bilibili video URL in the request. Accept `bilibili.com` and `b23.tv` links; do not substitute search results or guess a URL.
2. Choose the destination:
   - Use the user's requested directory when provided.
   - Otherwise create or use a clearly named directory under the current workspace, such as `downloads/`.
3. Create a unique temporary working directory. Download into that directory, not the user's destination:

   ```sh
   work_dir="$(mktemp -d)"
   python3 <skill-dir>/scripts/download_bilibili_audio.py \
     '<bilibili-url>' \
     --output-dir "$work_dir"
   ```

   The default `source` format downloads the best available audio-only stream without transcoding. This preserves quality and normally avoids an `ffmpeg` dependency.
4. If the user explicitly requests a format, add `--audio-format m4a`, `mp3`, `opus`, `wav`, or `flac`. Format conversion requires `ffmpeg`; do not silently replace the requested format.
5. If Bilibili requires authentication for content the user can access in a local browser, rerun with `--cookies-from-browser '<browser-spec>'`, for example `chrome` or `safari`. Never print, inspect, copy, or persist browser cookies.
6. Confirm that the downloaded audio exists. Keep all intermediate files in the temporary directory.

## Prepare for Apple Music

Read [references/music-identification.md](references/music-identification.md) completely.

1. Inspect the video title, uploader, description, credits, thumbnail, and enough audio to identify the exact recording.
2. Verify the exact version against primary sources such as the artist, label, publisher, official release page, or credited creator. Distinguish originals, covers, remixes, arrangements, mashups, live performances, and fan edits.
3. Choose artwork in this order: exact official release cover; exact creator-published artwork; Bilibili thumbnail.
   - Never use artwork from a different recording.
   - If none is suitable and the user wants a custom cover, follow [references/generated-cover-art.md](references/generated-cover-art.md). Treat generation as optional and disclose that the result is not official artwork.
4. Create the metadata JSON and cover inside the temporary directory. Omit unknown fields and record evidence plus the Bilibili URL in `comment`.
5. Stop for confirmation if identity or credits remain ambiguous. Do not guess.
6. Give the audio its final user-facing filename inside the temporary directory, then embed verified metadata and artwork there. Keep the short-lived safety backup in that same temporary directory:

   ```sh
   uv run --with mutagen python <skill-dir>/scripts/tag_m4a.py \
     "$work_dir/<final-name>.m4a" \
     --metadata "$work_dir/metadata.json" \
     --cover "$work_dir/cover.jpg" \
     --backup-dir "$work_dir"
   ```

7. Verify the candidate audio's duration, readability, embedded tags, and embedded cover while it remains in the temporary directory.
8. If verification succeeds, move only the verified audio into the user's destination, then clean the entire temporary directory.
9. If any step or verification fails, clean the entire temporary directory and retry the complete workflow once in a new temporary directory. If the retry also fails, clean it and report the error with no output files. Do not preserve partial outputs or troubleshooting artifacts.
10. Confirm the destination contains only the requested final audio from this operation. Do not leave cover images, metadata JSON, source-named downloads, backups, thumbnails, or generated-image intermediates beside it. Report only the final audio path.

## Behavior and guardrails

- Download a single video only. The script deliberately passes `--no-playlist`.
- Preserve the source title in the filename and include the Bilibili video ID to reduce collisions.
- Reuse an existing completed download when `yt-dlp` determines that it is already present.
- Do not bypass paywalls, access controls, regional restrictions, or platform protections.
- Stop and report the exact prerequisite or platform error if the download fails. Do not claim that a file was created unless it exists.
- Treat each attempt as disposable. On failure, remove all temporary files before retrying from the beginning.

## Dependencies

The download script uses `yt-dlp` from `PATH`, or `uvx --from yt-dlp yt-dlp` as a fallback. The tagging script uses `mutagen` through `uv`.

Install `ffmpeg` only when the user requests conversion to a specific format.

## Script options

Run `python3 <skill-dir>/scripts/download_bilibili_audio.py --help` for all options.

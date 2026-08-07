---
name: download-bilibili-audio
category: Media
description: Atomically turn one Bilibili video into a source-quality audio file named only after the verified song title, preserving the best available original audio bitstream without transcoding while embedding primary-source official metadata and verified official or newly generated cover art. Use whenever the user provides a bilibili.com or b23.tv link and asks to download, save, extract, identify, tag, or add artwork to its audio. Treat "download" as shorthand for the complete workflow; never deliver a transcoded, untagged, unverified, or coverless audio file.
catalog_summary: Atomically turn Bilibili videos into title-named, source-quality audio files with verified metadata and official-or-generated cover art.
---

# Download and enrich Bilibili audio

Turn one Bilibili video into one finished music file. Use this skill only for content the user is authorized to download, and comply with applicable copyright, platform terms, and local law.

## Atomic completion contract

- Interpret "download," "save," or "extract the audio" as a request for the entire workflow: download, identify, research credits, select or generate artwork, tag, verify, and deliver.
- Consider the operation successful only when exactly one playable audio file exists with:
  - the best available source audio bitstream, unchanged by transcoding;
  - the exact recording title and performer;
  - every reasonably verifiable credit, including composer and lyricist when applicable;
  - source provenance in the comment;
  - either the verified official cover for this exact recording or a newly generated cover;
  - a filename containing only the verified song title and the source-compatible audio extension.
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
   - Ensure `ffmpeg` and `ffprobe` are available for stream inspection, bitstream hashing, and lossless container remuxing when required.
   - Ensure web research and an image-generation tool are available when the recording has no verified official cover.
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
6. Read [references/music-identification.md](references/music-identification.md) completely. Inspect the video title, uploader, description, and enough audio or video content only to form identification hypotheses and search queries. Do not transfer any Bilibili field directly into the music metadata.
7. Perform a real web search for the exact recording and verify its identity, version, and credits against external official sources such as the artist, label, publisher, rights organization, official release page, or credited creator's official page.
   - Require an external official source for the final `title` and `artist`; a Bilibili page alone is insufficient.
   - Verify each optional field independently before including it. Omit an optional field that official evidence does not establish.
   - Compare the researched recording with the audio and distinguish originals, covers, remixes, arrangements, mashups, live performances, unreleased works, and fan edits.
   - Treat the Bilibili title, uploader, description, tags, subtitles, and thumbnail only as search leads, never as metadata evidence.
   - If external official sources cannot establish the recording title and performer, fail the atomic operation instead of copying or paraphrasing the video information.
   - Treat consumer streaming catalogs only as discovery leads, never as evidence. Verify every retained value through a primary official source.
   - Preserve the actual recording title, performer, version, and credits even when no matching commercial release exists.
   - Do not copy album, artist, date, or credits from a similar but different catalog recording.
8. Use exactly one of these two cover sources:
   1. a verified official song or release cover for this exact recording, found online;
   2. a newly generated cover following [references/generated-cover-art.md](references/generated-cover-art.md) when no verified official cover can be found.

   Do not use the Bilibili video thumbnail, a video frame, fan art, generic creator artwork, or the cover of a different recording. Treat an ambiguous or unverifiable image as unavailable and generate a new cover instead. If generation is required but unavailable, fail the complete operation rather than deliver coverless audio.
9. Create the metadata JSON and cover inside the temporary directory:
   - Require `title` and `artist`.
   - Populate values from the verified external official sources, not by rewriting the Bilibili title, uploader, description, tags, or subtitles.
   - Research composer, lyricist, album, album artist, genre, and date; include each field only when independently supported by official evidence.
   - Record the Bilibili URL and concise verification sources in `comment`.
   - Do not guess missing credits merely to fill every field.
10. Preserve the original audio bitstream:
    - Keep the best source codec and encoded audio packets unchanged. Never request `--audio-format` or any other conversion option.
    - Compute and record a hash of the encoded audio stream before remuxing or tagging:

      ```sh
      ffmpeg -v error -i "$source_audio" -map 0:a:0 -c copy \
        -f hash -hash sha256 -
      ```

    - If the downloaded container supports metadata and cover art, tag it directly.
    - If it does not, remux the audio packets with stream copy into a compatible audio container. Use `.m4a` for AAC or ALAC, `.opus` for Opus, `.ogg` for Vorbis, and keep native `.flac` or `.mp3`. Never re-encode.
    - Do not convert AAC, Opus, MP3, or another lossy source to FLAC or WAV and describe it as lossless. A lossy source cannot be made lossless.
11. Give the candidate its final user-facing filename inside the temporary directory:
    - Use exactly `<verified title>.<source-compatible extension>`, where `verified title` is the `title` value embedded in the file.
    - Preserve an official version qualifier such as remix, arrangement, live, cover, or edit when it is part of the verified title.
    - Translate the title only when the user explicitly requests it; use that translated song title as both the filename and embedded title.
    - Remove or safely replace only characters that the destination filesystem forbids. Do not otherwise abbreviate or decorate the title.
    - Never add an artist, uploader, BV identifier, date, source label, quality label, sequence number, or bracketed suffix.
    - Do not overwrite an existing file or invent a disambiguating suffix. Report the filename conflict and leave the existing file untouched.
12. Embed all verified metadata and the selected cover. Keep the short-lived pre-tag backup inside the temporary directory:

    ```sh
    uv run --with mutagen python <skill-dir>/scripts/tag_audio.py \
      "$work_dir/<verified-title>.<extension>" \
      --metadata "$work_dir/metadata.json" \
      --cover "$work_dir/cover.jpg" \
      --backup-dir "$work_dir"
    ```

13. Verify, while still in the temporary directory:
    - the file is readable and has a plausible nonzero duration;
    - the file contains exactly one audio stream in the expected codec;
    - the encoded audio stream hash matches the pre-tag, pre-remux hash;
    - title and artist match the identified recording;
    - the filename stem equals the embedded title and contains no added artist, uploader, BV identifier, or other decoration;
    - all included metadata and credits describe the actual recording and trace to primary official sources;
    - provenance is present;
    - exactly one embedded cover exists, is readable, and is either verified official artwork or newly generated artwork.
14. Only after every check passes, move the single verified audio file into the final destination and delete the complete temporary directory.
15. If any step fails, delete the complete temporary directory and retry the entire workflow once in a new temporary directory. If the retry fails, delete it and report the error with no output files.
16. Confirm that this operation left only the final audio file in the destination. Return the final audio file or path and a concise metadata summary; do not return intermediate assets.

## Behavior and guardrails

- Download a single video only. The script deliberately passes `--no-playlist`.
- Never interpret a short request such as "download this" as permission to skip identification, credits, artwork, tagging, or verification.
- Never publish a file merely because the download command succeeded.
- Never transcode the downloaded audio. Preserve the best available source bitstream exactly; do not claim that a lossy source is lossless.
- Never copy or lightly rewrite Bilibili video fields into song metadata; use them only to search for independently verifiable official information.
- Name the final file only after the verified song title. Never append a BV identifier, artist, uploader, or other label.
- Never use a video thumbnail or frame as cover art.
- Omit unverifiable optional metadata rather than inventing it, but never omit the required identity, provenance, or cover.
- Do not bypass paywalls, access controls, regional restrictions, or platform protections.
- Stop and report the exact prerequisite or platform error if the download fails. Do not claim that a file was created unless it exists.
- Treat each attempt as disposable. On failure, remove all temporary files before retrying from the beginning.

## Dependencies

The download script uses `yt-dlp` from `PATH`, or `uvx --from yt-dlp yt-dlp` as a fallback. The tagging script uses `mutagen` through `uv`. Use `ffmpeg` and `ffprobe` only for inspection, audio-packet hashing, and stream-copy remuxing; never for transcoding.

## Script options

Run `python3 <skill-dir>/scripts/download_bilibili_audio.py --help` for all options.

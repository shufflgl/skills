---
name: prepare-m4a-for-apple-music
category: Media
description: Inspect and safely normalize M4A files for Apple Music and iCloud Music Library without re-encoding audio. Use for video-platform, DASH, fragmented MP4, iso5, or otherwise uncertain M4A containers; when Music reports Ineligible; or before importing externally sourced AAC/ALAC into a cloud-enabled Music library.
catalog_summary: Inspect and stream-copy M4A files into Apple Music-compatible containers while preserving audio, tags, and cover art.
---

# Prepare M4A for Apple Music

Make container compatibility explicit without changing the encoded audio. A
successful result proves that the audio-stream hash is unchanged and that the
output still has readable identity metadata and exactly one attached cover.

## Preflight

- Require `ffmpeg` and `ffprobe` on `PATH`.
- Expand user paths before use and work only with resolved paths.
- Reject an output path that already exists.
- Treat `.m4a` as a filename hint, never as compatibility evidence.

Run a read-only inspection when diagnosing a file:

```sh
python3 <skill-dir>/scripts/prepare_m4a.py inspect '<input.m4a>'
```

The JSON report includes brands, MP4 box layout, fragmentation and fast-start
signals, audio codec/profile/sample rate/channels/bit rate/duration, file size,
all non-audio streams, attached-cover details, required tags, and compatibility
reasons.

## Prepare a candidate

Create the candidate in a unique temporary directory:

```sh
python3 <skill-dir>/scripts/prepare_m4a.py prepare '<input.m4a>' \
  --output '<temporary-candidate.m4a>' \
  --force-remux
```

Use `--force-remux` for video-platform sources or uncertain provenance even if
the initial report looks acceptable. The script:

1. Refuses a real video stream or any cover layout it cannot preserve safely.
2. Hashes the encoded audio stream with FFmpeg stream copy.
3. Maps only the primary audio and optional attached cover, copies metadata,
   uses `-c copy`, marks the cover `attached_pic`, enables `faststart`, and sets
   the M4A major brand.
4. Re-inspects the candidate and repeats the audio-stream hash.
5. Deletes the candidate and fails if hashes differ, tags or cover are lost,
   a fragmented/DASH layout remains, or the output is not an M4A-branded
   fast-start container.

Describe this as **stream-copy remuxing**, not transcoding. State separately
that the audio bitstream is unchanged while the container structure changed.
Never describe AAC as lossless merely because the remux is bit-exact.

## Replace or deliver

- Do not write the candidate beside or over the source until validation passes.
- Before replacing a source, create a non-conflicting backup in the user's
  chosen backup directory and verify it exists.
- Refuse an existing destination, backup, or same-title collision. Do not add a
  suffix automatically.
- Move the verified candidate into place atomically when source and destination
  share a filesystem; otherwise copy, fsync, verify, and then rename.
- On failure, delete only the disposable candidate. Preserve the source,
  backup, and Music library record.

Return both inspection reports, the identical before/after SHA-256 value,
whether a remux occurred, and the final candidate path.

## Apple Music boundary

This skill prepares files but does not operate the Music library. A caller must
still verify Cloud Status. Local import or playback alone does not prove cloud
eligibility.

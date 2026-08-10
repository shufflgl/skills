---
name: download-bilibili-audio-to-apple-music
category: Media
description: Download and fully enrich the audio for one authorized Bilibili video, save the verified title-named audio file to the personal iCloud Drive Music directory, and import it into the local Apple Music library without creating an obvious duplicate. Use when the user provides a bilibili.com or b23.tv video and asks to add, save, download, or import its audio or song into their Music app, Apple Music library, or iCloud Music folder.
catalog_summary: Download verified Bilibili audio to the personal iCloud Music folder and import it into the Apple Music library.
---

# Download Bilibili audio to Apple Music

Turn one authorized Bilibili music video into one verified local audio file and
make it available in both the personal iCloud Drive Music folder and the local
Apple Music library.

## Dependencies

| Skill | Source | Requirement | Purpose |
| --- | --- | --- | --- |
| `$download-bilibili-audio` | Repository skill at `download-bilibili-audio/` | required | Produce the single verified, tagged, artwork-complete audio file. |
| `$computer-use:computer-use` | OpenAI bundled Computer Use plugin | required | Import the finished file into Music and verify the local library state. |

## Defaults

- Accept exactly one `bilibili.com` or `b23.tv` video URL per invocation.
- Save the finished audio file to
  `~/Library/Mobile Documents/com~apple~CloudDocs/Music`.
- Expand `~` to the active user's home directory at runtime before checking or
  passing the destination to a dependency; never treat it as a literal path.
- Keep the filename and embedded metadata produced by
  `$download-bilibili-audio`; do not rename, transcode, or retag the file during
  import.
- Use the local Apple Music library in the macOS Music app.
- Preserve source loudness by default. Do not normalize, amplify, or re-encode
  audio merely because playback in Music sounds quieter than direct playback of
  the same file.
- Treat an explicit destination or import instruction in the current request as
  an override for that run only.

## Workflow

1. Resolve exactly one Bilibili URL and confirm that the user is authorized to
   download its content. Preflight both dependencies, the default destination,
   and the Music app before beginning.
2. Invoke `$download-bilibili-audio` with the iCloud Drive Music directory as
   its final destination. Accept only the dependency's fully verified final
   audio path and metadata summary; do not expose or carry forward an
   intermediate download.
3. Confirm that the final file exists directly in the selected destination and
   retain its verified title, artist, version, and absolute path as the import
   handoff.
4. Invoke `$computer-use:computer-use` to inspect the Music app's local Library
   Songs view for the exact verified title, artist, and version.
   - If an unambiguous matching local-library track already exists, do not
     import another copy; continue to verification.
   - If a similar title or artist creates version ambiguity, stop and ask the
     user whether to import the new file.
   - Otherwise import the exact final file through the Music app's normal file
     import flow.
5. Refresh and inspect the local Library Songs view. Match the imported entry by
   verified title, artist, and version, and confirm that it is available as a
   local-library track. Do not change Music preferences, cloud-library settings,
   file organization settings, or the source file.
6. If the imported track sounds materially quieter in Music than when the same
   source file is played directly, treat the Music playback chain as the first
   diagnostic target:
   - Confirm Music's app volume, the track's **Volume Adjust** value, and its
     per-track equalizer setting before changing the file.
   - Check whether **Sound Check** is enabled. Sound Check can attenuate an
     imported track during Music playback even though the underlying file is
     unchanged and plays at its original level elsewhere.
   - When the file itself verifies correctly, recommend disabling Sound Check
     and restarting playback as the first comparison test. Do not modify the
     audio gain or re-encode the file to compensate.
7. Return the final iCloud file path, verified title and artist, and whether the
   track was newly imported or was already present in the local library.

## Approval gates

- Treat explicit invocation of this workflow as authorization to save the
  finished audio in the configured iCloud Drive folder and perform the ordinary
  Music app import.
- Obtain explicit approval before substituting either required skill, after
  explaining the unavailable dependency, proposed substitute, and behavioral
  differences.
- Ask before importing when the existing local library contains an ambiguous
  title, artist, or version match that could create a duplicate.
- Obtain explicit approval before changing Sound Check or any other global
  Music preference. A read-only inspection of those settings does not require
  approval.
- Follow any additional confirmation requirement imposed by the dependency
  skill or the active Computer Use policy at the moment of action.

## Completion criteria

- Exactly one fully verified final audio file exists at the selected iCloud
  Drive Music destination with the filename, metadata, artwork, and unchanged
  audio bitstream delivered by `$download-bilibili-audio`.
- No raw download or workflow intermediate has been left in the destination.
- An unambiguous matching title, artist, and version is visible in the Music
  app's local Library Songs view.
- The workflow reports whether it imported a new entry or reused an existing
  local-library entry.

## Failure handling

- Preserve `$download-bilibili-audio` atomicity: if it fails, allow its defined
  retry behavior and never import a partial or unverified file.
- If the destination is unavailable or not writable, stop before downloading
  and report the path failure. Do not silently redirect the output.
- If Music import fails, leave the already verified iCloud file intact, report
  the import blocker, and do not claim complete success.
- If direct playback has normal volume but Music playback is quiet, do not treat
  that difference alone as evidence of a damaged or under-gained file. Report
  the inspected Music playback settings, identify Sound Check when enabled, and
  keep the verified source audio unchanged.
- Do not delete or overwrite an existing destination file or Music library
  entry to resolve a conflict.
- Neither dependency is optional. Stop if one is unavailable unless the user
  explicitly approves a proposed capability-equivalent substitute.

---
name: download-bilibili-audio-to-apple-music
category: Media
description: Download and fully enrich one authorized Bilibili video's audio, normalize uncertain M4A containers without re-encoding, preserve local library state, and verify Apple Music Cloud Status. Use when the user asks to add Bilibili audio to Music, Apple Music, iCloud Music Library, or fix an imported track reported as Ineligible.
catalog_summary: Download verified Bilibili audio, prepare its container for Apple Music, and verify cloud-library eligibility.
---

# Download Bilibili audio to Apple Music

Turn one authorized Bilibili music video into one verified local audio file and
make it available in both the personal iCloud Drive Music folder and the local
Apple Music library.

## Dependencies

| Skill | Source | Requirement | Purpose |
| --- | --- | --- | --- |
| `$download-bilibili-audio` | Repository skill at `download-bilibili-audio/` | required | Produce the single verified, tagged, artwork-complete audio file. |
| `$prepare-m4a-for-apple-music` | Repository skill at `prepare-m4a-for-apple-music/` | required | Inspect and stream-copy uncertain M4A containers into a verified Music-compatible layout. |
| `$computer-use:computer-use` | OpenAI bundled Computer Use plugin | required | Import the finished file into Music and verify the local library state. |

## Defaults

- Accept exactly one `bilibili.com` or `b23.tv` video URL per invocation.
- Save the finished audio file to
  `~/Library/Mobile Documents/com~apple~CloudDocs/Music`.
- Expand `~` to the active user's home directory at runtime before checking or
  passing the destination to a dependency; never treat it as a literal path.
- Preserve the verified filename, metadata, cover, and encoded audio stream.
- Treat every Bilibili/video-platform M4A as uncertain and stream-copy remux it
  before first import even when its AAC stream appears normal.
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
2. Invoke `$download-bilibili-audio` into a unique temporary staging directory.
   Accept only its fully verified final audio path and metadata summary.
3. Invoke `$prepare-m4a-for-apple-music` before any Music import. Inspect the
   actual container and streams, including brands, fragmentation, DASH boxes,
   audio codec/profile/sample rate/channels/bit rate/duration/size, unexpected
   video streams, attached cover, and required tags. For a video-platform M4A,
   force a stream-copy remux to an M4A-branded fast-start container even if the
   initial report is otherwise clean.
4. Require identical encoded-audio SHA-256 values before and after preparation.
   Also require the verified title/artist and exactly one JPEG or PNG attached
   cover to survive. Describe the result as unchanged audio bitstream plus an
   adjusted container, never as transcoding or as upgrading a lossy source.
5. Resolve the `~` destination at runtime and reserve the exact title path, but
   do not move or replace anything until the Music lookup in the next step.
   Refuse any backup collision. Keep candidates and backups outside the
   destination until an atomic final move; leave no intermediates there.
6. Invoke `$computer-use:computer-use` to inspect the Music app's local Library
   Songs view for the exact verified title, artist, and version.
   - Record Cloud Status, favorite/loved state, rating, play count, comments,
     playlist membership, and other visible local attributes needed to restore
     the record before any removal.
   - If an unambiguous matching record is `Uploaded`, `Matched`, `Need upload`,
     or `Waiting`, do not replace its file or import a duplicate; discard the
     staged candidate and continue with status verification.
   - If it is `Ineligible`, do not assume replacing its underlying file will
     trigger reevaluation. Prepare the repaired file and follow the guarded
     removal/reimport path below.
   - If a similar title or artist creates version ambiguity, stop and ask the
     user whether to import the new file.
   - Otherwise require the title path to be absent, atomically move the verified
     candidate there, and import that exact file through Music's normal flow.
     If an unrelated same-title disk file exists, stop without overwriting it.
7. For an existing `Ineligible` record, first create and verify a non-conflicting
   backup of its exact disk file. Show the recorded library attributes and wait
   for approval at the final deletion confirmation. After approval, remove only
   the old library record and explicitly choose to keep the disk file. Then
   atomically replace that kept file with the verified candidate, import it,
   restore the recorded attributes where Music supports it, and verify playlist
   membership. Never delete the only disk copy.
8. Run **File > Library > Update Cloud Library** after a new or repaired import,
   then refresh the Songs view and read the exact Cloud Status:
   - `Ineligible`: failure; re-inspect the actual imported file and container.
   - `Need upload` or `Waiting`: eligible but still pending. Continue observing
     for a bounded period and report pending if it does not advance.
   - `Uploaded` or `Matched`: cloud synchronization succeeded.
   - `Error`: read the available error detail and continue diagnosis.
   Local import and playback are necessary checks but never completion proof.
9. Play a short portion of the exact imported record, confirm the repaired file
   retains its tags and cover, stop playback, and check that the background
   cloud task exposes no error.
10. If the imported track sounds materially quieter in Music than when the same
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
11. Return the final path, title, artist, identical audio-stream hash, container
   changes, import/reuse/reimport outcome, restored attributes, final Cloud
   Status, and any still-pending upload limitation.

## Approval gates

- Treat explicit invocation of this workflow as authorization to save the
  finished audio in the configured iCloud Drive folder and perform the ordinary
  Music app import.
- Obtain explicit approval before substituting either required skill, after
  explaining the unavailable dependency, proposed substitute, and behavioral
  differences.
- Ask before importing when the existing local library contains an ambiguous
  title, artist, or version match that could create a duplicate.
- When an old record must be removed, wait until the final Music deletion
  confirmation is visible, explain the saved attributes and keep-file choice,
  and obtain explicit approval before confirming removal.
- Obtain explicit approval before changing Sound Check or any other global
  Music preference. A read-only inspection of those settings does not require
  approval.
- Follow any additional confirmation requirement imposed by the dependency
  skill or the active Computer Use policy at the moment of action.

## Completion criteria

- Exactly one verified final file exists at the destination with unchanged
  encoded-audio SHA-256, readable title/artist, and one attached JPEG or PNG
  cover in a non-fragmented, M4A-branded fast-start container.
- No raw download or workflow intermediate has been left in the destination.
- The exact track is locally playable and Cloud Status is not `Ineligible`.
- The background upload task reports no error. Prefer `Uploaded` or `Matched`.
  `Need upload` or `Waiting` is a truthful pending result, not cloud completion,
  and must never be reported as available on other devices.
- Any removed record's restorable favorite, rating, comments, and playlist
  state has been restored and verified.

## Failure handling

- Preserve `$download-bilibili-audio` atomicity: if it fails, allow its defined
  retry behavior and never import a partial or unverified file.
- If the destination is unavailable or not writable, stop before downloading
  and report the path failure. Do not silently redirect the output.
- If Music import fails, leave the already verified iCloud file intact, report
  the import blocker, and do not claim complete success.
- If audio hashes differ, delete the disposable candidate, preserve the source,
  backup, and library record, and stop before import.
- If stream layout, metadata, or cover cannot be preserved safely, stop without
  replacing the source or changing the library.
- If Cloud Status remains `Ineligible`, do not loop destructive reimports.
  Preserve the repaired file and saved record attributes, then report the
  inspected container and Music error state.
- If status remains `Need upload` or `Waiting`, report that the file is eligible
  but upload is pending; do not claim cross-device availability.
- If deletion/reimport is declined or interrupted, preserve both the disk file
  and existing library record.
- If direct playback has normal volume but Music playback is quiet, do not treat
  that difference alone as evidence of a damaged or under-gained file. Report
  the inspected Music playback settings, identify Sound Check when enabled, and
  keep the verified source audio unchanged.
- Do not overwrite an existing destination or backup, and do not remove a
  library entry without the guarded confirmation path.
- Neither dependency is optional. Stop if one is unavailable unless the user
  explicitly approves a proposed capability-equivalent substitute.

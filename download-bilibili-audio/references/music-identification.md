# Music identification and metadata

## Evidence rules

- Inspect Bilibili information only to form candidate identities and search queries. Never copy or paraphrase its title, uploader, description, tags, subtitles, or thumbnail directly into music metadata.
- Perform a live web search for the exact recording. Search combinations of the candidate title, audible lyrics, performer, version qualifier, composer, and distinctive context.
- Require at least one external official source to establish the final title and performer. Prefer the artist, label, publisher, rights organization, official release page, or credited creator's official page.
- Verify that the official source describes the audio actually downloaded, not merely a similarly named composition or another performance.
- Use secondary databases and consumer streaming catalogs only to discover search leads. Never use them as evidence for a retained metadata value.
- Identify the exact version and preserve qualifiers such as remix, arrangement, live, cover, or edit.
- Describe the actual recording even when it is unreleased, independent, fan-made, or absent from commercial catalogs.
- If no external official source establishes both title and performer, stop the atomic workflow. Do not fill the required fields from the Bilibili page.
- Omit unknown optional values. Never assign uploader, performer, arranger, or original artist to another role without official evidence.
- Make a reasonable effort to verify composer, lyricist, album, album artist, genre, and release date independently. Include each optional field only when an official source establishes it.
- Record concise provenance in `comment`, including the Bilibili URL and primary official sources used.

## Final filename

- Set the filename stem to exactly the verified metadata `title` and retain the source-compatible audio extension.
- Keep an official version qualifier only when it is part of that title.
- Translate the title only at the user's explicit request and keep the filename and embedded title identical.
- Replace only filesystem-forbidden characters.
- Never append the performer, uploader, BV identifier, source, date, quality, sequence number, or any other decoration.
- Never overwrite an existing file or add a collision suffix. Report the conflict and keep the existing file unchanged.

## Artwork

Every delivered file must contain one embedded cover from exactly one of two sources:

1. A verified official song or release cover for this exact recording, collected online.
2. A newly generated cover made by following [generated-cover-art.md](generated-cover-art.md) when no verified official cover can be found.

Do not use a Bilibili video thumbnail, video frame, fan art, generic creator artwork, or another recording's cover. Confirm official artwork through the artist, label, publisher, or official release page. If an image cannot be verified as the official cover for the exact recording, generate a new one. Never create a misleading official-looking cover or deliver coverless audio.

## Metadata JSON

Create this file inside the temporary working directory. `title` and `artist` are required; all other fields are optional:

```json
{
  "title": "Exact recording title",
  "artist": ["Primary artist", "Featured artist"],
  "album": "Exact release",
  "album_artist": ["Primary album artist"],
  "composer": ["Composer"],
  "lyricist": ["Lyricist"],
  "genre": "Genre",
  "date": "2026",
  "comment": "Source: Bilibili URL. Verified against official source URL."
}
```

For a cover or arrangement, use this recording's actual performer as `artist` and retain the original composer in `composer`. Do not replace the performer with the artist of a similar catalog release.

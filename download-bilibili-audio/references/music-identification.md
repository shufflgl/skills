# Music identification and metadata

## Evidence rules

- Treat the Bilibili title as a lead, not proof.
- Prefer the artist, label, publisher, official release page, or credited creator.
- Use secondary databases only to corroborate.
- Identify the exact version and preserve qualifiers such as remix, arrangement, live, cover, or edit.
- Omit unknown values. Never assign uploader, performer, arranger, or original artist to another role without evidence.
- Record concise provenance in `comment`, including the Bilibili URL and sources used.

## Artwork

Use the exact release cover for a documented release. For independent arrangements or fan works, prefer creator-published artwork or the video thumbnail. If none is suitable, use the optional workflow in [generated-cover-art.md](generated-cover-art.md). Never create a misleading official-looking cover.

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

For a cover or arrangement, use this recording's performer as `artist` and retain the original composer in `composer`.

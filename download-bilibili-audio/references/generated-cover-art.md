# Generated cover art fallback

Use this workflow whenever no suitable original artwork exists. Generated artwork is a personal library asset, not an official release cover. Do not treat generation as a separate deliverable: embed the selected result in the final M4A and remove the image afterward.

## Build the concept

Derive the visual direction from verified information and the audio itself:

- exact recording type: original, cover, remix, arrangement, live version, or fan work;
- genre, era, tempo, mood, instrumentation, and sonic texture;
- themes supported by lyrics, creator notes, or the source video;
- cultural and historical context that can be represented accurately.

Do not infer a false artist identity, country, era, story, or official affiliation. Avoid artist/label logos, watermarks, copied album layouts, and unrelated recognizable people. Do not imitate a living artist's signature visual style; describe concrete visual qualities instead.

## Write the GPT Image prompt

Use this structure and replace every bracketed value:

```text
Use case: stylized-concept
Asset type: square cover artwork for a personal Apple Music library
Primary request: Create an original cover concept for [exact recording and version].
Scene/backdrop: [visual environment grounded in the music]
Subject: [one clear focal subject or abstract motif]
Style/medium: [specific medium and visual qualities]
Composition/framing: centered or deliberately balanced square composition; strong silhouette and legibility at thumbnail size; important details kept away from the edges
Lighting/mood: [lighting and emotional tone]
Color palette: [limited, intentional palette]
Materials/textures: [relevant surface or rendering details]
Constraints: original artwork; 1:1 square; suitable for a music library; visually represents [verified musical traits]
Avoid: text, logos, trademarks, watermarks, signatures, fake label marks, existing album artwork, unrelated celebrity likenesses, decorative borders
```

Default to no text. Add title or artist text only when the user explicitly wants it; quote the exact wording and require verbatim rendering.

## Generate and validate

1. Use the available image-generation tool directly. If it is unavailable, stop the atomic workflow and report the blocker with no audio output; do not substitute unrelated artwork.
2. Generate a `1024x1024` draft. After the concept is accepted, generate a `2048x2048` final when supported.
3. Inspect the final image for subject, mood, square composition, thumbnail readability, unwanted text, logos, artifacts, and factual mismatches. Iterate with one targeted correction at a time.
4. Save the selected JPEG or PNG inside the temporary working directory. It is an embedding input, not a separate user deliverable.
5. Add `Cover art generated with GPT Image; not official artwork.` to the metadata `comment`, then embed it with `scripts/tag_m4a.py`.
6. Whether generation or verification succeeds or fails, clean the image and all other temporary artifacts at the end of that attempt. Retry the entire audio workflow from the beginning when needed. Report only the final tagged audio; provide the prompt in chat only if useful.

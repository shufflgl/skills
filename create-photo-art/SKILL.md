---
name: create-photo-art
category: Media
description: Transform reference photos into finished 3:4 artwork using a user-selected style from an extensible style catalog. Use when a user asks for photo-based art, an editorial poster, an art postcard, a photo-and-illustration composition, or another supported visual treatment.
catalog_summary: Turn reference photos into polished 3:4 artwork using a user-selected style from an extensible visual-style catalog.
---

# Create photo art

Create one finished artwork per reference photo in the style the user explicitly chooses. Preserve the recognizable subject and the source photograph wherever the selected style requires photographic fidelity.

## Select a style before creating

1. Require at least one accessible reference photo. If none is available, ask the user to attach it.
2. Read [references/styles/index.md](references/styles/index.md) and present its numbered style choices with their short descriptions.
3. Ask the user to choose one style before generating or editing any image. Do not infer a style from the photo, silently default to one, or combine styles. If the user already made an unambiguous selection in the current request, treat that as the required choice and do not ask again.
4. After selection, read only the chosen style file. Follow its composition, typography, palette, exclusions, and verification requirements.
5. Accept optional user text or metadata only where the chosen style supports it. Never invent a place, date, title meaning, or factual detail that is not supported by the photo or the user's input.

## Create and deliver

- Use the available image-generation or image-editing tool. Preserve photographic regions through source-image editing or deterministic compositing when practical instead of regenerating them.
- Treat every uploaded photo as a separate input and return one independent 3:4 portrait artwork per photo. Never make a multi-photo collage unless a future registered style explicitly requires one.
- Use the same selected style for all photos in one request unless the user assigns styles per photo.
- Keep generated text short. Render critical typography during compositing when possible, then inspect spelling, duplication, placement, and legibility at full resolution.
- Inspect every result against the selected style file. Return the finished image or images and briefly identify the applied style and any optional metadata that was used or omitted.

## Extend the style catalog

To add a style, create one focused file under `references/styles/` and add one numbered entry to [references/styles/index.md](references/styles/index.md). Give the style a stable ID, distinctive user-facing name, short selection description, complete composition rules, exclusions, and a verification checklist. Keep shared workflow rules here and style-specific visual direction only in the style file. Do not renumber existing style IDs.

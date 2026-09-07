---
name: create-photo-art
category: Media
description: Create polished artwork from reference photos or text briefs using a user-selected visual style, creation mode, and aspect ratio. Use for photo-integrated compositions, pure art, editorial posters, art postcards, social graphics, wallpapers, prints, and other supported visual treatments.
catalog_summary: Create photo-integrated or pure artwork in a chosen visual style and aspect ratio for social, screen, editorial, or print use.
---

# Create photo art

Create finished artwork from reference photos, text briefs, or both. Let the user decide whether the source photo appears in the result, which registered style to use, and which aspect ratio fits the destination.

## Gather the creative choices

Before generating or editing, obtain explicit choices for all three dimensions below. Ask for only the choices the user has not already made unambiguously.

1. **Creation mode**
   - **Photo-integrated:** show the original photograph as a distinct photographic region and pair it with the selected artistic treatment. Require an accessible reference photo.
   - **Art-only:** do not show, reproduce, inset, collage, or frame the original photograph anywhere in the result. Use an accessible photo as visual reference when supplied, or work from a sufficiently clear text brief. If neither exists, ask for a photo or a description of the subject, setting, mood, and desired palette.
2. **Visual style:** read [references/styles/index.md](references/styles/index.md), present its numbered choices with short descriptions, and ask the user to choose one. Do not infer, default, or combine styles. After selection, read only the chosen style file.
3. **Aspect ratio or destination:** read [references/aspect-ratios.md](references/aspect-ratios.md). If the user names a ratio, use it. If the user names only a destination, recommend the closest registered ratio and confirm it before generating. Otherwise present the concise ratio menu and ask the user to choose.

Accept optional user text or metadata only where the chosen style supports it. Never invent a place, date, title meaning, or factual detail not supported by the reference or brief.

## Create and deliver

- Use the available image-generation or image-editing tool. In photo-integrated mode, preserve photographic regions through source-image editing or deterministic compositing when practical instead of regenerating them. In art-only mode, inspect the result to ensure no original-photo region remains.
- Treat every uploaded photo as a separate input and return one independent artwork per photo. Never make a multi-photo collage unless a future registered style explicitly requires one.
- Use the same selected style for all photos in one request unless the user assigns styles per photo.
- Render at the selected aspect ratio. The ratio rules override any legacy fixed-canvas wording, while the chosen style controls the visual language and internal hierarchy.
- Keep generated text short. Render critical typography during compositing when possible, then inspect spelling, duplication, placement, and legibility at full resolution.
- Inspect every result against the selected style file. Return the finished image or images and briefly identify the applied style and any optional metadata that was used or omitted.

## Extend the style catalog

To add a style, create one focused file under `references/styles/` and add one numbered entry to [references/styles/index.md](references/styles/index.md). Give the style a stable ID, distinctive user-facing name, short selection description, instructions for both creation modes, exclusions, and a verification checklist. Keep shared workflow and ratio rules outside style files. Do not renumber existing style IDs.

To add a ratio, append a stable entry to [references/aspect-ratios.md](references/aspect-ratios.md) with orientation, best-fit destinations, and adaptation guidance. Do not remove or silently redefine an existing ratio.

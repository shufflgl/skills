---
name: replace-book-cover
category: Books
description: Research a book from an imported EPUB or PDF, develop a content-faithful art direction, generate a refined replacement cover with GPT Image 2, and safely embed the approved image into a new EPUB or PDF copy. Use when a user wants to replace, redesign, modernize, restore, beautify, or upgrade an old, generic, damaged, or poorly made ebook cover in .epub or .pdf format.
catalog_summary: Research a book, create a content-faithful cover with GPT Image 2, and safely replace the cover in an EPUB or PDF copy.
---

# Replace a book cover

Create an edition-appropriate cover, not merely an attractive genre image. Preserve the source file and write a new sibling file by default.

## Workflow

1. Inspect the input before searching or designing:

   ```bash
   python3 scripts/book_cover.py inspect INPUT.epub
   python3 scripts/book_cover.py inspect INPUT.pdf
   ```

   Treat extracted metadata as clues, not truth. For a PDF, inspect the first pages or extract representative text when the title, author, or edition remains uncertain. Never upload the book file to a third party.

2. Identify the exact work and edition. Search the web for authoritative book information. Prefer publisher and author pages, library catalogs, scholarly sources, and reputable reviews. Cross-check title, author, language, publication context, genre, setting, themes, tone, period, and recurring imagery with at least two useful sources. Avoid plot spoilers unless they are essential to the design. Record source links for the user.

3. Develop one concise art direction. Read [references/cover-design.md](references/cover-design.md) before prompting. Do not imitate a living artist, copy an existing edition, reuse protected cover art, add fabricated endorsements, or claim publisher affiliation. Use the exact title and author spelling from the identified edition.

4. Generate a portrait cover with GPT Image 2 through the available image-generation tool. Request a complete front cover, normally at a 2:3 aspect ratio, with a clear thumbnail hierarchy and safe margins. Generate original imagery grounded in the book's subject and atmosphere. Inspect the result at full size. Reject misspelled, duplicated, illegible, or invented text; incorrect cultural or historical details; misleading genre signals; and visible mockup elements such as a spine, book, hands, shadows, or background.

5. Show the candidate cover to the user and obtain explicit approval before embedding it. If the user already explicitly authorized autonomous selection, choose the strongest compliant candidate and state that choice. Keep the generated image as a separate artifact alongside the output book.

6. Replace the cover without overwriting the source:

   ```bash
   python3 scripts/book_cover.py replace INPUT.epub APPROVED.png --output OUTPUT.epub
   python3 scripts/book_cover.py replace INPUT.pdf APPROVED.png --output OUTPUT.pdf
   ```

   For EPUB, replace the package-declared cover image while preserving the archive structure and uncompressed `mimetype` entry. For PDF, treat page 1 as the cover, preserve its page dimensions, replace that page, and retain the remaining pages and document metadata. If inspection indicates that page 1 is not a standalone cover, stop and ask which page or behavior the user wants.

7. Verify structurally and visually:

   ```bash
   python3 scripts/book_cover.py verify OUTPUT.epub
   python3 scripts/book_cover.py verify OUTPUT.pdf
   ```

   Render or open the new cover and at least the following page. Confirm orientation, cropping, readable text, correct page order, valid metadata, unchanged body-page count, and a reasonable file size. For EPUB, also open it in an EPUB reader when available. Report the output path, cover image path, research sources, dimensions, and verification performed.

## Safety and quality rules

- Never overwrite the input unless the user explicitly requests it and a backup exists.
- Stop when the work cannot be identified confidently; ask for title/author or permission to use a generic metadata-only direction.
- Keep sensitive or private documents local. Search only with minimal bibliographic facts, never excerpts that may be private.
- Preserve title, author, language, ISBN, table of contents, bookmarks, accessibility data, and body content. Do not rewrite book metadata merely to improve search results.
- Install missing Python packages only with user approval. The helper requires Pillow; PDF operations additionally require PyMuPDF. See [references/runtime.md](references/runtime.md).
- If the EPUB has no identifiable package-declared cover or uses DRM/encryption, stop instead of guessing or stripping protection.

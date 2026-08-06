---
name: check-epub-quality
description: Inspect a user-provided EPUB for structural integrity, readable content, metadata, language, navigation, cover and stylesheet resources, encryption or DRM, suspicious advertising, and signs of crude or incomplete construction. Use whenever the user attaches or points to an `.epub` and asks whether it is valid, clean, complete-looking, well made, ad-free, safe to read, or good quality. Do not search for, download, convert, repair, rename, or replace the ebook.
catalog_summary: Inspect a provided EPUB for integrity, completeness signals, metadata, presentation resources, DRM, language, and inserted advertising.
---

# Check EPUB quality

Inspect one EPUB without modifying it. Produce an evidence-based report; do not search the web or acquire another edition.

## Workflow

1. Resolve the exact local EPUB path supplied by the user. If no accessible file exists, ask the user to attach it.
2. Run the bundled inspector:

   ```sh
   PYTHONDONTWRITEBYTECODE=1 python3 \
     <skill-dir>/scripts/inspect_epub.py '<book.epub>'
   ```

   Add `--expected-title '<title>'` or `--expected-language zh|en` only when the user supplied that expectation.
3. Read the JSON report. Distinguish:
   - `status: pass`: no blocking structural or content signal was found;
   - `status: reject`: one or more blocking defects were found;
   - `quality_score`: a heuristic presentation/metadata score, not a claim of literary merit;
   - `warnings`: non-blocking defects that still lower quality.
4. Manually inspect representative content when command-line ZIP reading is available:
   - title page and metadata;
   - table of contents;
   - first chapter, two middle chapters, and final chapter;
   - cover and stylesheet declarations.

   Look for missing or duplicated chapters, abrupt endings, garbled characters, obvious OCR damage, repeated promotions, watermarks, and ugly fixed-width or inconsistent markup. Do not extract the archive into an untrusted destination; stream individual members with `unzip -p` or equivalent.
5. Return a concise report with:
   - verdict and quality score;
   - title, creator, declared and inferred language;
   - spine document and readable-character counts;
   - cover, navigation, stylesheet, remote-resource, and encryption findings;
   - every failure and warning;
   - manual spot-check findings and limitations.

## Interpretation rules

- Treat missing container/package data, corrupt ZIP members, missing manifest or spine resources, broken XHTML, empty reading order, too little readable content, unsupported encryption, mismatched expected language/title, or multiple strong ad signals as rejection reasons.
- Treat missing metadata, cover, stylesheet, remote dependencies, or one possible ad signal as warnings unless another defect makes them blocking.
- Do not claim that the book is complete merely because its EPUB structure is valid. State that completeness is only structurally plausible unless the text was compared with an authoritative edition.
- Do not claim that a translation is accurate, prose is well edited, or every image renders correctly from automated checks alone.
- Never alter the original file. If the user later asks for repair, handle that as a separate task with explicit output-copy semantics.

## Script behavior

`scripts/inspect_epub.py` uses only the Python standard library, prints JSON, and exits `0` for pass, `1` for rejection, or `2` for an operational error. Run it with `--help` for options.

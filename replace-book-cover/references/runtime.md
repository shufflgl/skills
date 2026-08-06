# Runtime requirements

Use Python 3.10 or newer. Create an isolated environment with `uv` when dependencies are absent:

```bash
uv venv
uv pip install Pillow PyMuPDF
```

Run the helper with the environment's Python. `Pillow` normalizes cover images for EPUB and PDF. `PyMuPDF` is required only for PDF inspection, replacement, and verification.

The helper supports unencrypted EPUB packages with an existing declared cover and ordinary PDFs whose first page is the cover. It intentionally refuses DRM/encrypted EPUBs and ambiguous EPUBs without a declared cover.

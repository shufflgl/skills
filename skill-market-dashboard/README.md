# Skillroom

Skillroom is the public repository console for `shufflgl/skills`. Its catalog, safe workflow map, artifact inventory, Git history, and quality results are generated from the repository during every build.

The site is static and read-only. Repository maintenance actions open the corresponding GitHub source, editor, or issue form.

## Local development

Requires Node.js `>=22.13.0`.

```bash
npm install
npm run dev
```

The local preview is available at `http://localhost:3000`.

## Validation

```bash
npm test
```

`npm run catalog:generate` runs the repository validators and Python test suites before producing the ignored `.generated/catalog.json` snapshot. A failing required check stops the build. `npm run catalog:diagnostic` is available for inspecting a failing repository locally without weakening production builds.

## Cloudflare Pages

The application is exported as a static Pages bundle because the dashboard does not require server-side data or APIs.

```bash
npm run build:pages
npm run deploy:pages
```

- Pages project: `shufflgl-skills`
- Production URL: <https://skills.lglgl.me>
- Production branch: `main`
- Repository source: <https://github.com/shufflgl/skills>

The generated `pages-dist/` directory is intentionally excluded from source control.

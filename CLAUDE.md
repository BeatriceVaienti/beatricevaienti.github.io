# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Beatrice Vaienti's personal website / CV, served as static GitHub Pages from this repo
(`beatricevaienti.github.io`). There is no build step, no framework, and no package.json —
`index.html` is deployed as-is when pushed to the default branch.

## Structure

- `index.html` — the entire site: markup, a `<script>` block, and a `<style>` block, all inline in one file. No separate CSS/JS files.
- `build_publications.py` — a standalone Python script that regenerates the "Publications" gallery inside `index.html` from `scholar.bib`. Not run automatically; run manually after updating the bib file.
- `scholar.bib` — BibTeX export from Google Scholar; the source of truth for the publications list.
- `img/papers/` — original cover images for publications, named `{year}_{FirstAuthorSurname}_{TitleSlug}.jpg` (matches the slug logic in `build_publications.py`). Falls back to `img/papers/placeholder.jpg` if a paper has no image yet.
- `img/papers_cropped_smaller/` — auto-generated 600x400 (3:2) center-cropped versions of the images above, used in the gallery cards. Fully derived output — don't hand-edit, regenerate via the script instead.
- `content.json` — **archived/unused**. Leftover from an earlier JSON-driven version of the site; the comment in `index.html` (`<!-- No JS needed anymore; removed JSON fetch -->`) confirms nothing reads it anymore. Don't treat it as a source of truth for site copy — the real content lives directly in `index.html`.

## Working with `index.html`

The page is one long file organized into `<section>`s (in DOM order): `#bio`, `#news`, `#projects`
(publications gallery), `#cv`, `#contact`, plus a background customization panel
(`#bg-controls`). Sections are independent — you can usually edit one without touching the others.

- **News items**: plain `<li>` entries in `.news-list` inside `#news`; add new ones at the top, following the existing `<strong>date —</strong> text` pattern.
- **Publications gallery** (between `<!-- PUBLICATIONS-START -->` and `<!-- PUBLICATIONS-END -->` markers inside `#projects`): this block is generated content — edit `scholar.bib` and re-run the build script rather than hand-editing the cards directly, or your changes will be overwritten on the next run.
- **CV section** (`#cv`): one fixed "Current Activities" card plus a set of collapsible `.cv-card-collapsible` cards (Education, Work Experience, Scholarships, Teaching, Languages & Software, Exhibitions, Talks, Summer Schools). Each collapsible card is a `<button class="cv-card-toggle">` + `<div class="cv-card-body">` pair, toggled by JS in the `<script>` block. Follow the existing `<li><strong>…</strong><br/>…<span class="cv-date">…</span></li>` pattern when adding entries.
- **Background**: an animated low-poly triangle canvas (`#bg-triangles`), generated client-side by `generateTriangulatedBackground()` in the inline `<script>`, driven by the `TRI_CONFIG` object (palette, density, jitter). The four color pickers in `#bg-controls` let a visitor tweak `TRI_CONFIG.palette` live and regenerate via the "regen" button — this is a page feature for visitors, not a dev tool.

## Regenerating the publications gallery

```
pip install bibtexparser Pillow   # if not already installed
python3 build_publications.py
```

This reads `scholar.bib`, sorts entries by year (most recent first, undated entries last), ensures
a cover image exists for each entry (copying `placeholder.jpg` if missing) and a cropped version in
`img/papers_cropped_smaller/`, then rewrites the HTML strictly between the
`PUBLICATIONS-START`/`PUBLICATIONS-END` markers in `index.html` — the rest of the file is untouched.

## Local development

Use the VS Code **Live Server** extension (publisher: `ritwickdey.LiveServer`) to preview changes:
right-click `index.html` → "Open with Live Server". It serves the file over `http://` and
auto-reloads the browser on every save, which matters when iterating on CSS/layout in the inline
`<style>` block.

## Deployment

Pushing to the repo's default branch publishes directly via GitHub Pages — there is no CI build.
Verify changes locally with Live Server (see above) before pushing.

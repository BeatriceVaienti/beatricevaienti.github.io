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
(publications gallery), `#cv`, `#contact`. Sections are independent — you can usually edit one
without touching the others.

- **News items**: plain `<li>` entries in `.news-list` inside `#news`; add new ones at the top, following the existing `<strong>date —</strong> text` pattern. If the News card would be taller than the About Me card, JS (`layoutNews()` in the inline `<script>`) clips the list at the last whole item that fits and injects a "More news" / "Less news" button — no manual pagination needed as the list grows.
- **Publications gallery** (between `<!-- PUBLICATIONS-START -->` and `<!-- PUBLICATIONS-END -->` markers inside `#projects`): this block is generated content — edit `scholar.bib` and re-run the build script rather than hand-editing the cards directly, or your changes will be overwritten on the next run. It shows one row of cards by default (sized to fit as many as the viewport allows, minimum 2), expandable via a "Show all" button injected by JS. New/replaced cover images often arrive as `.png` (sometimes with transparency) at `img/papers/{key}.png` — the build script only picks up `.jpg` originals, so flatten transparent PNGs onto the cream background (`#FCF9EA`, matching `FLATTEN_BACKGROUND` in `build_publications.py`) and save as `.jpg` at the same path before rerunning the script.
- **CV section** (`#cv`): a `.cv-sidebar` (Current Activities, Scholarships & Fellowships, Languages & Software) beside a `.cv-grid` of the remaining categories (Education, Work Experience, Teaching, Exhibitions, Talks, Summer Schools). Each `.cv-card-collapsible` is a `<button class="cv-card-toggle">` + `<div class="cv-card-body">` pair, but **the toggle is currently decorative only** (`pointer-events: none` — always expanded, no JS handler). Don't assume it's interactive. Follow the existing `<li><strong>…</strong><br/>…<span class="cv-date">…</span></li>` pattern when adding entries.
- **Background**: an animated low-poly triangle canvas (`#bg-triangles`), generated client-side by `generateTriangulatedBackground()` in the inline `<script>`, driven by the fixed `TRI_CONFIG` object (palette, density, jitter). There used to be a visitor-facing color-picker/regenerate panel in the footer (`#bg-controls`) — removed as a deliberate UX simplification (see git history if reviving it is ever wanted); the background itself still runs with its default palette.
- **Contact form**: posts to a Formspree endpoint (`https://formspree.io/f/mykqvoog`) via a `fetch()` handler in the inline `<script>` (not a plain HTML form submit) so visitors see an inline success/error message and stay on the site, instead of being redirected to Formspree's default thank-you page. The account login email and the recipient email are independently configurable in the Formspree dashboard — changing where submissions land never requires touching this file.
- **Favicon / social preview**: `img/favicon-16.png`, `favicon-32.png`, `apple-touch-icon.png`, `favicon-512.png` are center-square crops of `img/photo_bv.jpeg`. `img/og-image.jpg` (1200×630, used for Open Graph/Twitter cards) is a Playwright screenshot of the live site's hero area at 1400×900, cropped to the top-left 1200×630 — regenerate it the same way (screenshot, then crop) if the hero section's layout changes significantly.
- **Printable CV**: the "Download CV (PDF)" button (`.print-cv-btn`, at the end of `#cv`) calls `window.print()`. A `@media print` block hides everything except `#cv` and `#projects`, strips the site's decorative styling to plain black-on-white, and forces a single-column layout for the CV (see the comment above `.cv-layout` in the print block for why — CSS Grid/float sidebars were tried and don't paginate reliably across browsers). `#projects` gets `break-before: page` so Publications prints as a separate annex; a `beforeprint`/`afterprint` listener physically swaps `#cv` and `#projects` in the DOM to put the CV first, since combining that reorder with flexbox `order` instead of a real DOM swap broke pagination in Safari specifically. If you touch print CSS, test in both Chromium (`page.pdf()` via Playwright) and WebKit — they fail differently, and a fix verified in one is not verified in the other.

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

## Future improvement ideas

Backlog from a UX/UI review, roughly in priority order.

- [x] **Favicon, meta description, and Open Graph/Twitter card tags** — done. See "Favicon / social preview" above.
- [x] **Contact form redirected away on submit** — done, now uses a `fetch()` handler with an inline status message. See "Contact form" above.
- [x] **Tone tension between the playful background customizer and the formal CV content** — addressed by removing the customization panel; the animated background itself stays as a lighter-touch personal accent.
- [ ] **CV accordion cards are decorative, not interactive** (see note above under "CV section"). As the CV keeps growing, making them real accordions would let visitors jump to what they care about instead of scrolling past everything. The print/PDF version already forces full expansion independently via its own CSS, so this wouldn't affect the printable CV.
- [ ] **Focus states are inconsistent for keyboard users.** Only the contact form inputs have an explicit `:focus` style; nav pills, buttons, and gallery cards rely on browser defaults. Worth an accessibility pass.
- [ ] **Incorporate other creative/artistic work (pottery, linocut, painting) alongside the academic content?** Discussed but not yet decided — see whichever section covers this if/when it's revisited.

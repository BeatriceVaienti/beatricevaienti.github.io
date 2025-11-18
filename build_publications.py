from pathlib import Path
from html import escape
import shutil

import bibtexparser
from urllib.parse import quote_plus

# -------- CONFIGURATION --------
BIB_FILE = "scholar.bib"      # exported from Google Scholar
HTML_FILE = "index.html"      # your page file
PLACEHOLDER_IMAGE = "img/papers/placeholder.jpg"
IMAGE_DIR = Path("img/papers")
# --------------------------------


def load_bib_entries(path):
    with open(path, encoding="utf-8") as f:
        db = bibtexparser.load(f)
    return db.entries


def format_authors(authors_str: str) -> str:
    """
    Show up to 6 authors, then 'et al.' if more.
    Assumes a standard BibTeX 'author' field like:
    "Surname, Name and Second, Name and Third, Name"
    """
    if not authors_str:
        return ""

    # BibTeX uses ' and ' as author separator
    raw = authors_str.replace("\n", " ")
    authors = [a.strip() for a in raw.split(" and ") if a.strip()]

    if len(authors) <= 6:
        return ", ".join(authors)
    else:
        return ", ".join(authors[:6]) + ", et al."

import re

def slugify(text: str, max_words=4) -> str:
    """
    Convert title into a short, filesystem-safe slug.
    """
    if not text:
        return "paper"

    # Keep only letters/numbers/spaces
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    words = text.split()
    words = words[:max_words]  # shorten for filename
    return "".join(w.capitalize() for w in words)


def get_entry_url(entry) -> str | None:
    """
    Choose a URL for this entry:
    1. Use explicit 'url' field if present
    2. Else use DOI if present
    3. Else fall back to a Google Scholar search by title
    """
    url = entry.get("url")
    doi = entry.get("doi")
    title = entry.get("title")

    if url:
        return url

    if doi:
        return f"https://doi.org/{doi}"

    if title:
        # Fallback: Google Scholar search for the title
        return "https://scholar.google.com/scholar?q=" + quote_plus(title)

    return None

def local_image_path_for_entry(entry) -> Path:
    """
    Construct a readable filename such as:
    img/papers/2025_Vaienti_ClusteringLocalDistortions.jpg
    """
    year = entry.get("year", "xxxx")

    # First author
    authors = entry.get("author", "")
    first_author = "unknown"
    if authors:
        first = authors.split(" and ")[0]
        # Extract last name (BibTeX format: Lastname, Firstname)
        if "," in first:
            last = first.split(",")[0].strip()
        else:
            last = first.split()[-1]
        first_author = last.capitalize()

    # Title slug
    title = entry.get("title", "")
    title_slug = slugify(title)

    filename = f"{year}_{first_author}_{title_slug}.jpg"
    return IMAGE_DIR / filename



def ensure_local_image_for_entry(entry) -> str:
    """
    Ensure there is a local image file for this entry.

    - If img/papers/<bibkey>.jpg exists, use it
    - Otherwise, copy placeholder.jpg to that path and use it

    You can later replace those generated copies with real images.
    """
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    dest_path = local_image_path_for_entry(entry)

    if not dest_path.exists():
        placeholder_path = Path(PLACEHOLDER_IMAGE)
        if placeholder_path.exists():
            shutil.copyfile(placeholder_path, dest_path)
        else:
            # If the placeholder itself is missing, just fall back to its path
            return PLACEHOLDER_IMAGE

    return dest_path.as_posix()


def get_image_src_for_entry(entry) -> str:
    try:
        return ensure_local_image_for_entry(entry)
    except Exception:
        # Fallback if something unexpected happens
        return PLACEHOLDER_IMAGE


def entry_to_card(entry) -> str:
    title = escape(entry.get("title", "").strip("{}"))
    authors = escape(format_authors(entry.get("author", "")))
    venue = escape(entry.get("journal") or entry.get("booktitle", ""))
    year = escape(entry.get("year", ""))

    url = get_entry_url(entry)
    image_src = escape(get_image_src_for_entry(entry))
    image_alt = f"{title} cover image"

    # image with JS fallback to the placeholder if it fails to load
    img_html = (
        f'<img loading="lazy" src="{image_src}" '
        f'onerror="this.onerror=null;this.src=\'{PLACEHOLDER_IMAGE}\';" '
        f'alt="{escape(image_alt)}" class="gallery-image"/>'
    )

    article_html = f"""
      <article class="gallery-item">
        {img_html}
        <p>{title}</p>
        <p>{authors}</p>
        <p>{venue} {year}</p>
      </article>""".rstrip()

    # Wrap whole card in a link when a URL exists
    if url:
        return (
            f'<a class="gallery-item-link" href="{escape(url)}" '
            f'target="_blank" rel="noopener">'
            f"{article_html}"
            f"</a>"
        )
    else:
        return article_html


def build_cards_html(entries):
    # Sort: most recent year first, then title
    def sort_key(e):
        year = e.get("year", "0000")
        return (year, e.get("title", ""))

    sorted_entries = sorted(entries, key=sort_key, reverse=True)
    cards = [entry_to_card(e) for e in sorted_entries]
    return "\n".join(cards)


def inject_cards_into_html(html_path, cards_html):
    html = Path(html_path).read_text(encoding="utf-8")

    start_marker = "<!-- PUBLICATIONS-START -->"
    end_marker = "<!-- PUBLICATIONS-END -->"

    if start_marker not in html or end_marker not in html:
        raise RuntimeError("Markers not found in HTML file.")

    start_index = html.index(start_marker) + len(start_marker)
    end_index = html.index(end_marker)

    new_html = (
        html[:start_index]
        + "\n"
        + cards_html
        + "\n  "
        + html[end_index:]
    )

    Path(html_path).write_text(new_html, encoding="utf-8")


def main():
    entries = load_bib_entries(BIB_FILE)
    cards_html = build_cards_html(entries)
    inject_cards_into_html(HTML_FILE, cards_html)
    print(f"Updated {HTML_FILE} with {len(entries)} publications.")


if __name__ == "__main__":
    main()

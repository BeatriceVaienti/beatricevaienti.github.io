from pathlib import Path
from html import escape
import shutil
import re

import bibtexparser
from urllib.parse import quote_plus
from PIL import Image

# -------- CONFIGURATION --------
BIB_FILE = "scholar.bib"                # exported from Google Scholar
HTML_FILE = "index.html"                # your page file

ORIGINAL_IMAGE_DIR = Path("img/papers")                 # where you store/replace originals
CROPPED_IMAGE_DIR = Path("img/papers_cropped_smaller")  # auto-generated smaller copies

PLACEHOLDER_IMAGE = ORIGINAL_IMAGE_DIR / "placeholder.jpg"

TARGET_SIZE = (600, 400)    # width, height in pixels for the cropped/downscaled images
TARGET_RATIO = (3, 2)       # width:height aspect ratio for cropping (3:2 works nicely for cards)
# --------------------------------


def load_bib_entries(path):
    with open(path, encoding="utf-8") as f:
        db = bibtexparser.load(f)
    return db.entries


def format_authors(authors_str: str) -> str:
    """
    Show up to 6 authors, then 'et al.' if more.
    Assumes standard BibTeX 'author' field:
    "Surname, Name and Second, Name and Third, Name"
    """
    if not authors_str:
        return ""

    raw = authors_str.replace("\n", " ")
    authors = [a.strip() for a in raw.split(" and ") if a.strip()]

    if len(authors) <= 6:
        return ", ".join(authors)
    else:
        return ", ".join(authors[:6]) + ", et al."


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
        return "https://scholar.google.com/scholar?q=" + quote_plus(title)

    return None


def slugify(text: str, max_words=4) -> str:
    """
    Convert title into a short, filesystem-safe slug.
    e.g. "Segmentation and Clustering..." -> "SegmentationAndClustering"
    """
    if not text:
        return "paper"

    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    words = text.split()
    words = words[:max_words]
    return "".join(w.capitalize() for w in words)


def original_image_path_for_entry(entry) -> Path:
    """
    Construct a readable filename such as:
    img/papers/2025_Vaienti_SegmentationAndClustering.jpg
    """
    year = entry.get("year", "xxxx")

    authors = entry.get("author", "")
    first_author = "Unknown"
    if authors:
        first = authors.split(" and ")[0]
        if "," in first:
            last = first.split(",")[0].strip()
        else:
            last = first.split()[-1]
        first_author = last.capitalize()

    title = entry.get("title", "")
    title_slug = slugify(title)

    filename = f"{year}_{first_author}_{title_slug}.jpg"
    return ORIGINAL_IMAGE_DIR / filename


def cropped_image_path_for_entry(entry) -> Path:
    """
    Same filename as original, but in the cropped/smaller directory.
    """
    orig = original_image_path_for_entry(entry).name
    return CROPPED_IMAGE_DIR / orig


def process_image_to_cropped(source: Path, dest: Path):
    """
    Open 'source', center-crop to TARGET_RATIO, resize to TARGET_SIZE,
    and save to 'dest'.
    """
    CROPPED_IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    img = Image.open(source)
    img = img.convert("RGB")
    w, h = img.size

    target_ratio = TARGET_RATIO[0] / TARGET_RATIO[1]
    orig_ratio = w / h

    # Center crop to target aspect ratio
    if orig_ratio > target_ratio:
        # Image is wider than target: crop left/right
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        right = left + new_w
        top = 0
        bottom = h
    else:
        # Image is taller than target: crop top/bottom
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        bottom = top + new_h
        left = 0
        right = w

    img = img.crop((left, top, right, bottom))
    img = img.resize(TARGET_SIZE, Image.LANCZOS)

    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, format="JPEG", quality=85, optimize=True)


def ensure_local_image_for_entry(entry) -> str:
    """
    Ensure there is a cropped/small image for this entry.

    - If original (img/papers/...) doesn't exist, copy placeholder.jpg there.
    - Then create/update cropped version in img/papers_cropped_smaller/.
    - Return the path to the cropped image (as a POSIX string).
    """
    ORIGINAL_IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    orig_path = original_image_path_for_entry(entry)
    cropped_path = cropped_image_path_for_entry(entry)

    # If original doesn't exist, copy placeholder
    if not orig_path.exists():
        if PLACEHOLDER_IMAGE.exists():
            shutil.copyfile(PLACEHOLDER_IMAGE, orig_path)
        else:
            # If even placeholder is missing, just bail out to placeholder path
            return PLACEHOLDER_IMAGE.as_posix()

    # If cropped doesn't exist or is older than original, (re)create it
    if (not cropped_path.exists()) or (orig_path.stat().st_mtime > cropped_path.stat().st_mtime):
        process_image_to_cropped(orig_path, cropped_path)

    return cropped_path.as_posix()


def get_image_src_for_entry(entry) -> str:
    try:
        return ensure_local_image_for_entry(entry)
    except Exception:
        # Fallback if something unexpected happens
        return PLACEHOLDER_IMAGE.as_posix()


def entry_to_card(entry) -> str:
    title = escape(entry.get("title", "").strip("{}"))
    authors = escape(format_authors(entry.get("author", "")))
    venue = escape(entry.get("journal") or entry.get("booktitle", ""))
    year = escape(entry.get("year", ""))

    url = get_entry_url(entry)
    image_src = escape(get_image_src_for_entry(entry))
    image_alt = f"{title} cover image"

    img_html = (
        f'<img loading="lazy" src="{image_src}" '
        f'onerror="this.onerror=null;this.src=\'{PLACEHOLDER_IMAGE.as_posix()}\';" '
        f'alt="{escape(image_alt)}" class="gallery-image"/>'
    )

    article_html = f"""
      <article class="gallery-item">
        {img_html}
        <p>{title}</p>
        <p>{authors}</p>
        <p>{venue} {year}</p>
      </article>""".rstrip()

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
    # Sort: earliest year first, then title
    def sort_key(e):
        year_str = str(e.get("year", "0"))
        try:
            year = int(year_str)
        except ValueError:
            year = 0
        return (year, e.get("title", ""))

    sorted_entries = sorted(entries, key=sort_key)  # ascending
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

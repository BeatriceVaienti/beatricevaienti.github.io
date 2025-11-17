from pathlib import Path
from html import escape
import random
import time

import bibtexparser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# -------- CONFIGURATION --------
BIB_FILE = "scholar.bib"      # exported from Google Scholar
HTML_FILE = "index.html"      # your page file
PLACEHOLDER_IMAGE = "img/papers/placeholder.jpg"
IMAGE_DIR = Path("img/papers")
REQUEST_TIMEOUT = 10
POLITE_DELAY = 1.0            # seconds between remote requests
# --------------------------------

session = requests.Session()
session.headers.update(
    {
        "User-Agent": "Mozilla/5.0 (compatible; PublicationImageFetcher/1.0; +https://example.com)"
    }
)


def load_bib_entries(path):
    with open(path, encoding="utf-8") as f:
        db = bibtexparser.load(f)
    return db.entries


def format_authors(authors_str: str) -> str:
    if not authors_str:
        return ""
    authors = [a.strip() for a in authors_str.replace("\n", " ").split(" and ")]
    if len(authors) <= 2:
        return ", ".join(authors)
    return f"{authors[0]} et al."


def get_entry_url(entry) -> str | None:
    url = entry.get("url")
    doi = entry.get("doi")
    if url:
        return url
    if doi:
        return f"https://doi.org/{doi}"
    return None


def local_image_path_for_entry(entry) -> Path:
    key = entry.get("ID", "unknown").replace("/", "_")
    return IMAGE_DIR / f"{key}.jpg"


def try_download(url: str) -> requests.Response | None:
    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp
    except Exception:
        return None


def pick_candidate_image_urls(soup: BeautifulSoup, base_url: str) -> list[str]:
    imgs = soup.find_all("img")
    candidates = []

    for img in imgs:
        src = img.get("src") or ""
        if not src:
            continue

        full = urljoin(base_url, src)

        # filter obvious non-content images
        lower = full.lower()
        if any(bad in lower for bad in ["logo", "icon", "spinner", "badge", "pixel", "sprite", "analytics"]):
            continue

        # try to ignore tiny images if size is specified
        width = int(img.get("width") or 0)
        height = int(img.get("height") or 0)
        if width and height and (width < 150 or height < 150):
            continue

        candidates.append(full)

    return candidates


def fetch_remote_image_for_entry(entry) -> str | None:
    """
    Try to fetch an image from the paper's online page.
    Returns the local path (str) if successful, else None.
    """
    url = get_entry_url(entry)
    if not url:
        return None

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    dest_path = local_image_path_for_entry(entry)

    # If already downloaded before, reuse it
    if dest_path.exists():
        return str(dest_path).replace("\\", "/")

    # 1) Fetch the main page
    time.sleep(POLITE_DELAY)
    resp = try_download(url)
    if not resp:
        return None

    ctype = resp.headers.get("Content-Type", "")
    # If the URL itself is an image (rare but possible)
    if ctype.startswith("image/"):
        dest_path.write_bytes(resp.content)
        return str(dest_path).replace("\\", "/")

    if "html" not in ctype:
        return None

    # 2) Parse HTML and collect candidate images
    soup = BeautifulSoup(resp.text, "html.parser")
    candidates = pick_candidate_image_urls(soup, resp.url)

    if not candidates:
        return None

    # 3) Pick a random candidate and download it
    random.shuffle(candidates)
    for img_url in candidates:
        time.sleep(POLITE_DELAY)
        img_resp = try_download(img_url)
        if not img_resp:
            continue
        img_ctype = img_resp.headers.get("Content-Type", "")
        if not img_ctype.startswith("image/"):
            continue

        dest_path.write_bytes(img_resp.content)
        return str(dest_path).replace("\\", "/")

    return None


def get_image_src_for_entry(entry) -> str:
    # Try to fetch a remote image, else fallback
    local = fetch_remote_image_for_entry(entry)
    if local:
        return local
    return PLACEHOLDER_IMAGE


def entry_to_card(entry) -> str:
    title = escape(entry.get("title", "").strip("{}"))
    authors = escape(format_authors(entry.get("author", "")))
    venue = escape(entry.get("journal") or entry.get("booktitle", ""))
    year = escape(entry.get("year", ""))

    url = get_entry_url(entry)

    image_src = get_image_src_for_entry(entry)
    image_alt = f"{title} cover image"

    link_html = (
        f'<p><a href="{escape(url)}" target="_blank" rel="noopener">View paper</a></p>'
        if url
        else ""
    )

    return f"""
      <article class="gallery-item">
        <img loading="lazy" src="{image_src}" alt="{escape(image_alt)}" class="gallery-image"/>
        <p>{title}</p>
        <p>{authors}</p>
        <p>{venue} {year}</p>
        {link_html}
      </article>""".rstrip()


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

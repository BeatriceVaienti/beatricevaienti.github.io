from pathlib import Path
from html import escape
import bibtexparser

# -------- CONFIGURATION --------
BIB_FILE = "scholar.bib"      # exported from Google Scholar
HTML_FILE = "index.html"      # your page file
PLACEHOLDER_IMAGE = "img/papers/placeholder.jpg"
# --------------------------------

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

def entry_to_card(entry) -> str:
    title = escape(entry.get("title", "").strip("{}"))
    authors = escape(format_authors(entry.get("author", "")))
    venue = escape(entry.get("journal") or entry.get("booktitle", ""))
    year = escape(entry.get("year", ""))
    
    # Try to find a useful link: URL or DOI
    url = entry.get("url")
    doi = entry.get("doi")
    if not url and doi:
        url = f"https://doi.org/{doi}"

    # Single placeholder image for now
    image_src = PLACEHOLDER_IMAGE
    image_alt = f"{title} cover image"

    link_html = f'<p><a href="{escape(url)}" target="_blank" rel="noopener">View paper</a></p>' if url else ""

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

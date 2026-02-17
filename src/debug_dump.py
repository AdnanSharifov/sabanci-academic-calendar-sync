# Made by canadaaww
from __future__ import annotations

from pathlib import Path

from .scraper import fetch_html


def main():
    url = "https://www.sabanciuniv.edu/en/academic-calendar"
    html = fetch_html(url)

    out_path = Path("downloaded_page.html")
    out_path.write_text(html, encoding="utf-8")

    print("Saved HTML to:", out_path.resolve())
    print("HTML length:", len(html))

    # Quick probes
    probes = [
        "UNDER G.",
        "yeniBaslikTuruncu",
        "<table",
        "academic-calendar",
        "UNDER",
    ]
    for p in probes:
        print(f"Contains '{p}':", p in html)

    # Print a small snippet around where 'UNDER' might appear
    idx = html.find("UNDER")
    if idx != -1:
        start = max(0, idx - 200)
        end = min(len(html), idx + 400)
        print("\n--- SNIPPET AROUND FIRST 'UNDER' ---")
        print(html[start:end])
        print("--- END SNIPPET ---")
    else:
        print("\nNo 'UNDER' substring found at all.")


if __name__ == "__main__":
    main()
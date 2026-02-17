# Made by canadaaww
from __future__ import annotations

import re
from typing import List, Tuple

import requests
from bs4 import BeautifulSoup

from .date_parse import parse_undergrad_date_cell
from .models import ParsedEvent


UNDERGRAD_HEADER_RE = re.compile(r"UNDER\s*G\.", re.IGNORECASE)


def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": "SabanciCalendarSync/1.0",
        "Accept-Language": "en-US,en;q=1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection": "keep-alive",
    }
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.text


def _extract_cells_text(cells) -> List[str]:
    return [" ".join(c.get_text(" ", strip=True).split()) for c in cells]


def _header_cells(table) -> List[str]:
    # 1) Normal case: <thead>
    thead = table.find("thead")
    if thead:
        ths = thead.find_all(["th", "td"])
        hdrs = _extract_cells_text(ths)
        if hdrs:
            return hdrs

    # 2) Fallback: first row that contains <th>
    for tr in table.find_all("tr"):
        ths = tr.find_all("th")
        if ths:
            hdrs = _extract_cells_text(tr.find_all(["th", "td"]))
            if hdrs:
                return hdrs

    # 3) Last resort: use first <tr> as header-like row
    first_tr = table.find("tr")
    if first_tr:
        hdrs = _extract_cells_text(first_tr.find_all(["th", "td"]))
        if hdrs:
            return hdrs

    return []


def _find_undergrad_col_index(headers: List[str]) -> int | None:
    for i, h in enumerate(headers):
        if UNDERGRAD_HEADER_RE.search(h):
            return i
    return None


def _rows(table):
    # Prefer tbody, but if missing, fall back to all trs.
    tbody = table.find("tbody")
    if tbody:
        return tbody.find_all("tr")
    return table.find_all("tr")


def scrape_undergrad_events(url: str, strict_undergrad_only: bool, logger) -> Tuple[List[ParsedEvent], List[str]]:
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")

    tables = soup.find_all("table")
    if not tables:
        return [], ["No <table> elements found on the page."]

    extracted: List[ParsedEvent] = []
    warnings: List[str] = []

    found_any_undergrad_header = False

    for t_index, table in enumerate(tables):
        headers = _header_cells(table)
        if not headers:
            continue

        ug_idx = _find_undergrad_col_index(headers)
        if ug_idx is None:
            continue

        found_any_undergrad_header = True

        trs = _rows(table)
        if not trs:
            continue

        # If the first row looks like headers, skip it from data rows
        first_cells = trs[0].find_all(["th", "td"])
        first_text = " ".join([c.get_text(" ", strip=True) for c in first_cells])
        if UNDERGRAD_HEADER_RE.search(first_text):
            trs = trs[1:]

        for r_index, tr in enumerate(trs):
            tds = tr.find_all(["td", "th"])
            if not tds:
                continue

            title = " ".join(tds[0].get_text(" ", strip=True).split()) if len(tds) >= 1 else ""
            if not title:
                continue

            ug_text = ""
            if len(tds) > ug_idx:
                ug_text = " ".join(tds[ug_idx].get_text(" ", strip=True).split())

            if not ug_text:
                if strict_undergrad_only:
                    logger.info(f"SKIP (no UNDER G. date) | table={t_index} row={r_index} | {title}")
                    continue

                # Non-strict: try any cell that parses as a date/range
                for c in tds[1:]:
                    candidate = " ".join(c.get_text(" ", strip=True).split())
                    if parse_undergrad_date_cell(candidate) is not None:
                        ug_text = candidate
                        break

            parsed = parse_undergrad_date_cell(ug_text)
            if parsed is None:
                logger.error(f"ERROR (unparseable date) | {title} | cell='{ug_text}'")
                warnings.append(f"Unparseable date for '{title}': '{ug_text}'")
                continue

            start, end_inclusive = parsed
            extracted.append(ParsedEvent(title_raw=title, start=start, end=end_inclusive, source_url=url))
            logger.info(f"EXTRACT | {title} | {start.isoformat()}..{end_inclusive.isoformat()}")

    if not found_any_undergrad_header:
        warnings.append("No table with an 'UNDER G.' header was detected.")
    return extracted, warnings
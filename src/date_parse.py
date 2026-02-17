# Made by canadaaww
from __future__ import annotations

import re
from datetime import date
from typing import Optional, Tuple

from dateutil import parser as dtparser


# Examples supported:
#  - "11 Jul 2025"
#  - "01-04 Sep 2025"
#  - "03 Aug - 01 Sep 2026"
#  - "10 Nov - 05 Dec 2025"
#  - "29 Sep 2025 13 Jan 2026"   (two full dates, no dash)
RANGE_SAME_MONTH_RE = re.compile(r"^\s*(\d{1,2})\s*-\s*(\d{1,2})\s+([A-Za-z]{3,})\s+(\d{4})\s*$")
RANGE_DIFF_MONTH_RE = re.compile(r"^\s*(\d{1,2})\s+([A-Za-z]{3,})\s*-\s*(\d{1,2})\s+([A-Za-z]{3,})\s+(\d{4})\s*$")
SINGLE_DATE_RE = re.compile(r"^\s*(\d{1,2})\s+([A-Za-z]{3,})\s+(\d{4})\s*$")
TWO_FULL_DATES_RE = re.compile(
    r"^\s*(\d{1,2}\s+[A-Za-z]{3,}\s+\d{4})\s+(\d{1,2}\s+[A-Za-z]{3,}\s+\d{4})\s*$"
)


def _parse_single(d: str) -> date:
    # English month tokens on the page; dateutil handles them.
    return dtparser.parse(d, dayfirst=True, yearfirst=False, fuzzy=False).date()


def parse_undergrad_date_cell(text: str) -> Optional[Tuple[date, date]]:
    if not text:
        return None

    # Normalize multiple spaces/newlines
    text = " ".join(text.split())

    m = SINGLE_DATE_RE.match(text)
    if m:
        d = _parse_single(text)
        return d, d

    m = RANGE_SAME_MONTH_RE.match(text)
    if m:
        d1, d2, mon, y = m.groups()
        start = _parse_single(f"{d1} {mon} {y}")
        end = _parse_single(f"{d2} {mon} {y}")
        if end < start:
            return None
        return start, end

    m = RANGE_DIFF_MONTH_RE.match(text)
    if m:
        d1, mon1, d2, mon2, y = m.groups()
        start = _parse_single(f"{d1} {mon1} {y}")
        end = _parse_single(f"{d2} {mon2} {y}")
        if end < start:
            return None
        return start, end

    # NEW: two full dates with no dash (e.g., "29 Sep 2025 13 Jan 2026")
    m = TWO_FULL_DATES_RE.match(text)
    if m:
        d1, d2 = m.groups()
        start = _parse_single(d1)
        end = _parse_single(d2)
        if end < start:
            return None
        return start, end

    # Last-resort: try parse as a single date
    try:
        dt = _parse_single(text)
        return dt, dt
    except Exception:
        return None
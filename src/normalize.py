# Made by canadaaww
from __future__ import annotations

import hashlib
import re


WS_RE = re.compile(r"\s+")
PUNCT_RE = re.compile(r"[^\w\s]+")


def normalize_title_for_matching(title: str) -> str:
    s = title.strip().lower()
    s = PUNCT_RE.sub(" ", s)
    s = WS_RE.sub(" ", s).strip()
    return s


def compute_uid(start_iso: str, end_iso: str, norm_title: str) -> str:
    raw = f"{start_iso}|{end_iso}|{norm_title}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
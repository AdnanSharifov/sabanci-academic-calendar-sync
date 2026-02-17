# Made by canadaaww
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ParsedEvent:
    title_raw: str
    start: date
    end: date  # inclusive end date
    source_url: str

    @property
    def is_single_day(self) -> bool:
        return self.start == self.end
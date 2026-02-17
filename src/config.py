# Made by canadaaww
from __future__ import annotations

from dataclasses import dataclass
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class AppConfig:
    source_url: str = "https://www.sabanciuniv.edu/en/academic-calendar"
    tz: ZoneInfo = ZoneInfo("Europe/Istanbul")
    target_calendar_name: str = "Sabanci Academic Calendar by canadaaww"

    tag_key: str = "sac_tag"
    uid_key: str = "sac_uid"
    prev_uids_key: str = "sac_prev"
    src_key: str = "sac_src"
    tag_value: str = "1"

    strict_undergrad_only_default: bool = True
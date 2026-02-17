# Made by canadaaww
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from rapidfuzz import fuzz

from .categorize import categorize
from .config import AppConfig
from .normalize import compute_uid, normalize_title_for_matching


@dataclass
class SyncStats:
    created: int = 0
    updated: int = 0
    deleted: int = 0
    skipped: int = 0
    errors: int = 0


def _as_all_day_gcal_dates(start: date, end_inclusive: date) -> Tuple[str, str]:
    # Google all-day events use end as exclusive
    start_s = start.isoformat()
    end_exclusive = (end_inclusive + timedelta(days=1)).isoformat()
    return start_s, end_exclusive


def _is_past(event_end_inclusive: date, today_ist: date) -> bool:
    return event_end_inclusive < today_ist


def _is_future_or_today(event_start: date, today_ist: date) -> bool:
    return event_start >= today_ist


def _build_event_body(cfg: AppConfig, title_raw: str, start: date, end_inclusive: date, uid: str) -> Dict:
    cat = categorize(title_raw)
    emoji_title = f"{cat.emoji} {title_raw}"

    start_s, end_excl_s = _as_all_day_gcal_dates(start, end_inclusive)

    body = {
        "summary": emoji_title,
        "start": {"date": start_s},
        "end": {"date": end_excl_s},
        "colorId": cat.color_id,
        "description": f"Source: {cfg.source_url}\nMade by canadaaww",
        "extendedProperties": {
            "private": {
                cfg.tag_key: cfg.tag_value,
                cfg.uid_key: uid,
                cfg.src_key: cfg.source_url,
            }
        },
    }

    # Add reminders for deadline-ish categories (best-effort)
    if cat.reminder_minutes is not None:
        body["reminders"] = {
            "useDefault": False,
            "overrides": [{"method": "popup", "minutes": cat.reminder_minutes}],
        }

    return body


def _extract_private_props(cfg: AppConfig, g_event: Dict) -> Dict[str, str]:
    return (g_event.get("extendedProperties", {}).get("private", {}) or {})


def _is_ours(cfg: AppConfig, g_event: Dict) -> bool:
    props = _extract_private_props(cfg, g_event)
    return props.get(cfg.tag_key) == cfg.tag_value and cfg.uid_key in props


def _index_existing(cfg: AppConfig, existing_events: List[Dict]) -> Tuple[Dict[str, Dict], List[Dict]]:
    by_uid: Dict[str, Dict] = {}
    ours: List[Dict] = []
    for ev in existing_events:
        if not _is_ours(cfg, ev):
            continue
        ours.append(ev)
        props = _extract_private_props(cfg, ev)
        uid = props.get(cfg.uid_key)
        if uid:
            by_uid[uid] = ev
    return by_uid, ours


def _best_fuzzy_match(
    norm_title: str,
    start_s: str,
    end_excl_s: str,
    candidates: List[Dict],
    threshold: int = 92,
) -> Optional[Dict]:
    best = None
    best_score = -1
    for ev in candidates:
        s = ev.get("start", {}).get("date")
        e = ev.get("end", {}).get("date")
        if s != start_s or e != end_excl_s:
            continue

        summary = ev.get("summary", "")
        # remove leading emoji if present
        summary_norm = normalize_title_for_matching(summary)
        score = fuzz.token_sort_ratio(norm_title, summary_norm)
        if score > best_score:
            best_score = score
            best = ev

    if best is not None and best_score >= threshold:
        return best
    return None


def sync(
    cfg: AppConfig,
    logger,
    calendar_service,
    calendar_id: str,
    parsed_events: List,
    mode: str,
    strict_undergrad_only: bool,
    dry_run: bool = False,
) -> SyncStats:
    """
    mode:
      - add_future
      - add_future_remove_past
      - remove_past
      - remove_all
    """
    stats = SyncStats()

    today_ist = date.today()  # OS local date; later we will ensure Istanbul specifically in main.py
    # We'll fix Istanbul date in main.py using cfg.tz; keep here simple.

    # Define a listing window: from 1 year ago to 2 years ahead (wide enough, page is "current year" anyway)
    list_start = today_ist - timedelta(days=400)
    list_end = today_ist + timedelta(days=800)

    existing = calendar_service.events().list(
        calendarId=calendar_id,
        timeMin=f"{list_start.isoformat()}T00:00:00+03:00",
        timeMax=f"{(list_end + timedelta(days=1)).isoformat()}T00:00:00+03:00",
        singleEvents=True,
        showDeleted=False,
        maxResults=2500,
    ).execute().get("items", [])

    by_uid, ours = _index_existing(cfg, existing)

    logger.info(f"SYNC | mode={mode} | existing_ours={len(ours)} | scraped={len(parsed_events)} | dry_run={dry_run}")

    # Build desired set depending on mode
    desired = []
    for pe in parsed_events:
        if mode in ("add_future", "add_future_remove_past"):
            if _is_future_or_today(pe.start, today_ist):
                desired.append(pe)
        # remove modes don't need desired

    # Add/update
    if mode in ("add_future", "add_future_remove_past"):
        for pe in desired:
            try:
                norm = normalize_title_for_matching(pe.title_raw)
                uid = compute_uid(pe.start.isoformat(), pe.end.isoformat(), norm)

                start_s, end_excl_s = _as_all_day_gcal_dates(pe.start, pe.end)

                existing_ev = by_uid.get(uid)
                if existing_ev is None:
                    # fuzzy update: same dates but title changed slightly
                    existing_ev = _best_fuzzy_match(norm, start_s, end_excl_s, ours, threshold=92)

                body = _build_event_body(cfg, pe.title_raw, pe.start, pe.end, uid)

                if existing_ev is None:
                    logger.info(f"CREATE | {pe.title_raw} | {pe.start}..{pe.end} | uid={uid}")
                    if not dry_run:
                        calendar_service.events().insert(calendarId=calendar_id, body=body).execute()
                    stats.created += 1
                else:
                    ev_id = existing_ev["id"]
                    logger.info(f"UPDATE | {pe.title_raw} | {pe.start}..{pe.end} | uid={uid} | id={ev_id}")
                    if not dry_run:
                        calendar_service.events().patch(calendarId=calendar_id, eventId=ev_id, body=body).execute()
                    stats.updated += 1

            except Exception as e:
                stats.errors += 1
                logger.error(f"ERROR | add/update failed | {pe.title_raw} | {e}")

    # Deletions
    if mode in ("add_future_remove_past", "remove_past", "remove_all"):
        for ev in ours:
            try:
                s = ev.get("start", {}).get("date")
                e = ev.get("end", {}).get("date")  # exclusive
                if not s or not e:
                    continue

                end_inclusive = date.fromisoformat(e) - timedelta(days=1)
                should_delete = False

                if mode == "remove_all":
                    should_delete = True
                elif mode in ("add_future_remove_past", "remove_past"):
                    if _is_past(end_inclusive, today_ist):
                        should_delete = True

                if not should_delete:
                    stats.skipped += 1
                    continue

                logger.info(f"DELETE | {ev.get('summary','')} | ends={end_inclusive} | id={ev['id']}")
                if not dry_run:
                    calendar_service.events().delete(calendarId=calendar_id, eventId=ev["id"]).execute()
                stats.deleted += 1

            except Exception as e:
                stats.errors += 1
                logger.error(f"ERROR | delete failed | id={ev.get('id')} | {e}")

    return stats
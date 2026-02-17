# Made by canadaaww
from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, List

from googleapiclient.discovery import build


def build_calendar_service(creds):
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def ensure_calendar(service, calendar_name: str, logger) -> str:
    page_token = None
    while True:
        cal_list = service.calendarList().list(pageToken=page_token, maxResults=250).execute()
        for item in cal_list.get("items", []):
            if item.get("summary") == calendar_name:
                logger.info(f"CALENDAR | Found existing calendar: {calendar_name}")
                return item["id"]
        page_token = cal_list.get("nextPageToken")
        if not page_token:
            break

    created = service.calendars().insert(body={"summary": calendar_name, "timeZone": "Europe/Istanbul"}).execute()
    logger.info(f"CALENDAR | Created calendar: {calendar_name}")
    return created["id"]


def list_events_in_window(service, calendar_id: str, start: date, end: date, logger) -> List[Dict]:
    time_min = f"{start.isoformat()}T00:00:00+03:00"
    time_max = f"{(end + timedelta(days=1)).isoformat()}T00:00:00+03:00"

    out: List[Dict] = []
    page_token = None
    while True:
        resp = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            showDeleted=False,
            maxResults=2500,
            pageToken=page_token,
        ).execute()
        out.extend(resp.get("items", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    logger.info(f"GCAL | Listed {len(out)} events in window {start}..{end}")
    return out
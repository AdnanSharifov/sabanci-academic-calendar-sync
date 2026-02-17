# Made by canadaaww
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from .app_paths import log_path, token_path
from .config import AppConfig
from .google_auth import load_credentials
from .google_calendar import build_calendar_service, ensure_calendar
from .logger_setup import setup_logger
from .scraper import scrape_undergrad_events
from .sync_engine import sync

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def istanbul_today(cfg: AppConfig):
    return datetime.now(tz=cfg.tz).date()


def ask_strictness(cfg: AppConfig) -> bool:
    default = "Y" if cfg.strict_undergrad_only_default else "N"
    print(f"\nFilter strictness: STRICT UNDER G. only? (Y/N) [default {default}]")
    ans = input("> ").strip().upper()
    if not ans:
        ans = default
    return ans == "Y"


def menu() -> str:
    print("\nChoose an operation:")
    print("1) Add all future events (including today)")
    print("2) Add future events and remove past events")
    print("3) Remove past events")
    print("4) Remove all events")
    print("0) Exit")
    return input("> ").strip()


def main():
    cfg = AppConfig()
    logger = setup_logger(log_path())

    print("===============================================")
    print(" Sabanci Academic Calendar Sync (UNDER G.)")
    print(" Made by canadaaww")
    print("===============================================")

    strict = ask_strictness(cfg)

    choice = menu()
    if choice == "0":
        return

    mode_map = {
        "1": "add_future",
        "2": "add_future_remove_past",
        "3": "remove_past",
        "4": "remove_all",
    }
    if choice not in mode_map:
        print("Invalid choice.")
        return

    mode = mode_map[choice]

    if mode == "remove_all":
        print("\nCONFIRM: This will delete ALL events created by this app from the dedicated calendar.")
        print("Type DELETE to confirm:")
        conf = input("> ").strip()
        if conf != "DELETE":
            print("Cancelled.")
            return

    oauth_json = Path(__file__).resolve().parents[1] / "assets" / "oauth_client.json"
    if not oauth_json.exists():
        print("ERROR: Missing assets/oauth_client.json")
        print("You must place your downloaded Desktop OAuth client JSON there.")
        return

    creds = load_credentials(oauth_json, token_path(), SCOPES)
    service = build_calendar_service(creds)
    cal_id = ensure_calendar(service, cfg.target_calendar_name, logger)

    today = istanbul_today(cfg)
    logger.info(f"TIME | Istanbul today={today.isoformat()}")

    # Scrape every run for correctness
    events, warnings = scrape_undergrad_events(cfg.source_url, strict_undergrad_only=strict, logger=logger)
    for w in warnings:
        logger.warning(f"SCRAPE WARNING | {w}")

    stats = sync(
        cfg=cfg,
        logger=logger,
        calendar_service=service,
        calendar_id=cal_id,
        parsed_events=events,
        mode=mode,
        strict_undergrad_only=strict,
        dry_run=False,
    )

    print("\n================ SUMMARY ================")
    print(f"Added:    {stats.created}")
    print(f"Updated:  {stats.updated}")
    print(f"Deleted:  {stats.deleted}")
    print(f"Skipped:  {stats.skipped}")
    print(f"Errors:   {stats.errors}")
    print(f"Log file: {log_path()}")
    print("=========================================")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
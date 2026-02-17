# Made by canadaaww
from __future__ import annotations

from .config import AppConfig
from .logger_setup import setup_logger
from .app_paths import log_path
from .scraper import scrape_undergrad_events


def main():
    cfg = AppConfig()
    logger = setup_logger(log_path())

    print("Testing scrape...")
    events, warnings = scrape_undergrad_events(cfg.source_url, strict_undergrad_only=True, logger=logger)

    print(f"\nExtracted events: {len(events)}")
    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(" -", w)

    if events:
        print("\nFirst 5 events:")
        for e in events[:5]:
            print(f" - {e.title_raw} | {e.start}..{e.end}")


if __name__ == "__main__":
    main()
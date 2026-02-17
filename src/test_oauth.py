# Made by canadaaww
from __future__ import annotations

from pathlib import Path

from .app_paths import token_path, log_path
from .config import AppConfig
from .google_auth import load_credentials
from .google_calendar import build_calendar_service, ensure_calendar
from .logger_setup import setup_logger


SCOPES = ["https://www.googleapis.com/auth/calendar"]


def main():
    cfg = AppConfig()
    logger = setup_logger(log_path())

    oauth_json = Path(__file__).resolve().parents[1] / "assets" / "oauth_client.json"
    if not oauth_json.exists():
        print("Missing assets/oauth_client.json")
        return

    creds = load_credentials(oauth_json, token_path(), SCOPES)
    service = build_calendar_service(creds)

    cal_id = ensure_calendar(service, cfg.target_calendar_name, logger)
    print("OK. Calendar ID:", cal_id)


if __name__ == "__main__":
    main()
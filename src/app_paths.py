# Made by canadaaww
from __future__ import annotations

import os
from pathlib import Path

APP_DIR_NAME = "SabanciCalendarSync"


def app_data_dir() -> Path:
    base = os.environ.get("APPDATA")
    if not base:
        base = str(Path.home() / "AppData" / "Roaming")
    p = Path(base) / APP_DIR_NAME
    p.mkdir(parents=True, exist_ok=True)
    return p


def token_path() -> Path:
    return app_data_dir() / "token.json"


def state_path() -> Path:
    return app_data_dir() / "state.json"


def log_path() -> Path:
    return app_data_dir() / "sync.log"
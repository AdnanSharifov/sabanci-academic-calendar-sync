# Made by canadaaww
from __future__ import annotations

from pathlib import Path
from typing import Sequence

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


def load_credentials(oauth_client_json: Path, token_json: Path, scopes: Sequence[str]) -> Credentials:
    creds = None

    if token_json.exists():
        creds = Credentials.from_authorized_user_file(str(token_json), scopes=scopes)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_json.write_text(creds.to_json(), encoding="utf-8")
        return creds

    if creds and creds.valid:
        return creds

    flow = InstalledAppFlow.from_client_secrets_file(str(oauth_client_json), scopes=scopes)
    creds = flow.run_local_server(port=0, open_browser=True, authorization_prompt_message="")
    token_json.write_text(creds.to_json(), encoding="utf-8")
    return creds
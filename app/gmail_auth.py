from __future__ import annotations

import os
from typing import Sequence

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

DEFAULT_TOKEN_PATH = "token.json"
DEFAULT_CLIENT_SECRET = os.path.join("secrets", "client_secret.json")

READONLY_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
MODIFY_SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

def get_gmail_service(apply_actions: bool, token_path: str = DEFAULT_TOKEN_PATH):
    """
    Returns an authenticated Gmail API service.
    - DRY-RUN: uses gmail.readonly
    - APPLY: uses gmail.modify
    """
    scopes: Sequence[str] = MODIFY_SCOPES if apply_actions else READONLY_SCOPES

    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, scopes=scopes)

    # Refresh if possible
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        if not os.path.exists(DEFAULT_CLIENT_SECRET):
            raise FileNotFoundError(
                f"Missing OAuth client secrets at: {DEFAULT_CLIENT_SECRET}\n"
                "Create Google Cloud OAuth Desktop credentials and save JSON there."
            )
        flow = InstalledAppFlow.from_client_secrets_file(DEFAULT_CLIENT_SECRET, scopes=scopes)
        creds = flow.run_local_server(port=0)
        with open(token_path, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds, cache_discovery=False)

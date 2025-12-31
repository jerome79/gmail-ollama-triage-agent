from __future__ import annotations

from typing import Any, Dict, List

from .email_parse import extract_headers, find_body_text

def build_query(since_days: int) -> str:
    return f"newer_than:{since_days}d"

def list_message_ids(service, user_id: str, q: str, max_results: int) -> List[str]:
    resp = service.users().messages().list(userId=user_id, q=q, maxResults=max_results).execute()
    msgs = resp.get("messages") or []
    return [m["id"] for m in msgs if "id" in m]

def get_message(service, user_id: str, message_id: str) -> Dict[str, Any]:
    return service.users().messages().get(userId=user_id, id=message_id, format="full").execute()

def normalize_message(msg: Dict[str, Any], max_body_chars: int) -> Dict[str, Any]:
    payload = msg.get("payload") or {}
    headers = extract_headers(payload)

    frm = headers.get("from", "")
    to = headers.get("to", "")
    subject = headers.get("subject", "")
    date = headers.get("date", "")

    snippet = msg.get("snippet") or ""
    body = (find_body_text(payload) or "").strip()
    if len(body) > max_body_chars:
        body = body[:max_body_chars] + "…"

    return {
        "id": msg.get("id"),
        "threadId": msg.get("threadId"),
        "from": frm,
        "to": to,
        "subject": subject,
        "date": date,
        "snippet": snippet,
        "body": body,
    }

def fetch_recent_emails(
    service,
    user_id: str = "me",
    fetch_n: int = 20,
    since_days: int = 7,
    max_body_chars: int = 2000,
) -> List[Dict[str, Any]]:
    q = build_query(since_days)
    ids = list_message_ids(service, user_id=user_id, q=q, max_results=fetch_n)
    emails: List[Dict[str, Any]] = []
    for mid in ids:
        raw = get_message(service, user_id=user_id, message_id=mid)
        emails.append(normalize_message(raw, max_body_chars=max_body_chars))
    return emails

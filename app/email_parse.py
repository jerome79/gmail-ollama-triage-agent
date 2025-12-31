from __future__ import annotations

import base64
import re
from bs4 import BeautifulSoup
from typing import Any, Dict, Optional

def _b64url_decode(data: str) -> str:
    decoded = base64.urlsafe_b64decode(data.encode("utf-8"))
    return decoded.decode("utf-8", errors="replace")

def strip_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def extract_headers(payload: Dict[str, Any]) -> Dict[str, str]:
    headers = payload.get("headers", [])
    result: Dict[str, str] = {}
    for h in headers:
        name = (h.get("name") or "").lower()
        value = h.get("value") or ""
        if name:
            result[name] = value
    return result

def find_body_text(payload: Dict[str, Any]) -> str:
    """
    Best-effort extraction:
    - prefer text/plain
    - fallback to text/html (stripped)
    - supports multipart nesting
    """
    mime = payload.get("mimeType", "")
    body = payload.get("body", {}) or {}
    data = body.get("data")
    if data:
        raw = _b64url_decode(data)
        if mime == "text/html":
            return strip_html(raw)
        return raw.strip()

    parts = payload.get("parts") or []
    if not parts:
        return ""

    plain_candidate: Optional[str] = None
    html_candidate: Optional[str] = None

    def walk(part: Dict[str, Any]) -> None:
        nonlocal plain_candidate, html_candidate
        mt = part.get("mimeType", "")
        b = part.get("body", {}) or {}
        d = b.get("data")
        if d:
            raw = _b64url_decode(d)
            if mt == "text/plain" and not plain_candidate:
                plain_candidate = raw
            elif mt == "text/html" and not html_candidate:
                html_candidate = raw
        for child in (part.get("parts") or []):
            walk(child)

    for p in parts:
        walk(p)

    if plain_candidate:
        return plain_candidate.strip()
    if html_candidate:
        return strip_html(html_candidate)
    return ""

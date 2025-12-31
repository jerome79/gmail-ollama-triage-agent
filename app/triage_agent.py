from __future__ import annotations

import json
from typing import Dict, Any, Optional, List

from pydantic import BaseModel, Field, ValidationError
from .ollama_client import OllamaClient

ALLOWED_CATEGORIES = ["Finance", "Sales", "Support", "Personal", "Newsletter", "Spam", "Other"]
ALLOWED_PRIORITIES = ["High", "Medium", "Low"]
ALLOWED_ACTIONS = ["Label", "Star", "Archive", "DraftReply", "None"]

class TriageResult(BaseModel):
    category: str = Field(...)
    priority: str = Field(...)
    action: str = Field(...)
    label: Optional[str] = None
    star: bool = False
    archive: bool = False
    reason: str = Field(...)

def build_messages(email: Dict[str, Any], label_prefix: str) -> List[Dict[str, str]]:
    system = (
        "You are an email triage assistant.\n"
        "Return ONLY valid JSON with keys: category, priority, action, label, star, archive, reason.\n"
        f"category must be one of: {ALLOWED_CATEGORIES}.\n"
        f"priority must be one of: {ALLOWED_PRIORITIES}.\n"
        f"action must be one of: {ALLOWED_ACTIONS}.\n"
        "reason must be ONE short sentence.\n"
        "If unsure: category=Other, priority=Medium, action=None, star=false, archive=false.\n"
        f"If action=Label, use label like '{label_prefix}Finance', '{label_prefix}Sales', '{label_prefix}Support', '{label_prefix}Newsletter'.\n"
        "Never include extra text outside JSON."
    )

    user = (
        "Triage this email:\n"
        f"FROM: {email.get('from','')}\n"
        f"TO: {email.get('to','')}\n"
        f"SUBJECT: {email.get('subject','')}\n"
        f"DATE: {email.get('date','')}\n"
        f"SNIPPET: {email.get('snippet','')}\n"
        f"BODY: {email.get('body','')}\n"
        "\nReturn JSON only."
    )

    return [{"role": "system", "content": system}, {"role": "user", "content": user}]

def _extract_json(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model response.")
    return text[start : end + 1]

def triage_email(
    client: OllamaClient,
    model: str,
    email: Dict[str, Any],
    label_prefix: str = "AI/",
    max_retries: int = 2,
) -> TriageResult:
    last_err: Optional[Exception] = None
    for _ in range(max_retries + 1):
        try:
            raw = client.chat(model=model, messages=build_messages(email, label_prefix), temperature=0.2)
            data = json.loads(_extract_json(raw))

            # normalize booleans if model outputs strings
            if isinstance(data.get("star"), str):
                data["star"] = data["star"].lower() == "true"
            if isinstance(data.get("archive"), str):
                data["archive"] = data["archive"].lower() == "true"

            result = TriageResult(**data)

            if result.category not in ALLOWED_CATEGORIES:
                raise ValueError(f"Invalid category: {result.category}")
            if result.priority not in ALLOWED_PRIORITIES:
                raise ValueError(f"Invalid priority: {result.priority}")
            if result.action not in ALLOWED_ACTIONS:
                raise ValueError(f"Invalid action: {result.action}")

            return result

        except (ValueError, json.JSONDecodeError, ValidationError) as e:
            last_err = e
            # reduce body size and retry
            email = dict(email)
            email["body"] = (email.get("body") or "")[:1200]

    raise RuntimeError(f"Triage failed after retries: {last_err}")

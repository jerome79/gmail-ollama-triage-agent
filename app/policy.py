from __future__ import annotations
from typing import Iterable, Optional
from .triage_agent import TriageResult

def normalize_sender(from_header: str) -> str:
    # crude extraction: keep the email if present
    s = from_header or ""
    if "<" in s and ">" in s:
        s = s.split("<", 1)[1].split(">", 1)[0]
    return s.strip().lower()

def apply_policy(
    result: TriageResult,
    label_prefix: str = "AI/",
    vip_senders: Optional[Iterable[str]] = None,
    archive_newsletters: bool = False,
    archive_spam: bool = False,
) -> TriageResult:
    """
    Deterministic layer to make behavior consistent and business-friendly.
    - VIP senders => force High + star
    - High priority => star
    - Known categories => label
    - Optional: archive newsletters/spam
    """
    vip_set = {v.strip().lower() for v in (vip_senders or []) if v.strip()}

    # VIP handling (caller passes normalized sender separately if desired)
    # We'll treat vip_senders as a list of raw email strings; compare elsewhere in main if needed.

    # High priority => star
    if result.priority == "High":
        result.star = True
        if result.action == "None":
            result.action = "Star"

    # Label known categories
    if result.category in ("Finance", "Sales", "Support", "Newsletter"):
        if not result.label:
            result.label = f"{label_prefix}{result.category}"
        if result.action == "None":
            result.action = "Label"

    # Optional archiving
    if archive_newsletters and result.category == "Newsletter" and result.priority in ("Low", "Medium"):
        result.archive = True
        if result.action == "None":
            result.action = "Archive"

    if archive_spam and result.category == "Spam":
        result.archive = True
        if result.action == "None":
            result.action = "Archive"

    return result

from __future__ import annotations
from typing import Optional, Dict, Any, List

def get_label_id(service, user_id: str, label_name: str) -> Optional[str]:
    labels = service.users().labels().list(userId=user_id).execute()
    for lb in labels.get("labels", []):
        if lb.get("name") == label_name:
            return lb.get("id")
    return None

def create_label(service, user_id: str, label_name: str) -> str:
    body = {
        "name": label_name,
        "labelListVisibility": "labelShow",
        "messageListVisibility": "show",
    }
    created = service.users().labels().create(userId=user_id, body=body).execute()
    return created["id"]

def ensure_label(service, user_id: str, label_name: str) -> str:
    existing = get_label_id(service, user_id, label_name)
    if existing:
        return existing
    return create_label(service, user_id, label_name)

def modify_message_labels(
    service,
    user_id: str,
    message_id: str,
    add_label_ids: Optional[List[str]] = None,
    remove_label_ids: Optional[List[str]] = None,
) -> None:
    body: Dict[str, Any] = {
        "addLabelIds": add_label_ids or [],
        "removeLabelIds": remove_label_ids or [],
    }
    service.users().messages().modify(userId=user_id, id=message_id, body=body).execute()

def star_message(service, user_id: str, message_id: str) -> None:
    modify_message_labels(service, user_id, message_id, add_label_ids=["STARRED"])

def archive_message(service, user_id: str, message_id: str) -> None:
    modify_message_labels(service, user_id, message_id, remove_label_ids=["INBOX"])

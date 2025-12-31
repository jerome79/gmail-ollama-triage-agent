from __future__ import annotations

import argparse
from typing import List

from .config import SETTINGS
from .gmail_auth import get_gmail_service
from .gmail_fetch import fetch_recent_emails
from .ollama_client import OllamaClient
from .triage_agent import triage_email
from .policy import apply_policy, normalize_sender
from .gmail_actions import ensure_label, modify_message_labels, star_message, archive_message
from .utils import append_jsonl, utc_now_iso

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Gmail Ollama Triage Agent (local-first)")
    p.add_argument("--fetch", type=int, default=20, help="Number of emails to fetch")
    p.add_argument("--since-days", type=int, default=7, help="Fetch emails newer than N days")
    p.add_argument("--dry-run", action="store_true", help="Dry-run mode (safe, no changes)")
    p.add_argument("--apply", action="store_true", help="Apply label/star/archive actions (requires gmail.modify)")
    p.add_argument("--model", type=str, default=SETTINGS.default_model, help="Ollama model name")
    p.add_argument("--max-body-chars", type=int, default=SETTINGS.max_body_chars, help="Max body chars sent to LLM")
    p.add_argument("--label-prefix", type=str, default=SETTINGS.label_prefix, help="Gmail label prefix (e.g. AI/)")
    p.add_argument("--vip-senders", type=str, default="", help="Comma-separated VIP sender emails (force High priority)")
    p.add_argument("--archive-newsletters", action="store_true", help="Archive newsletters (low/medium priority)")
    p.add_argument("--archive-spam", action="store_true", help="Archive spam emails")
    p.add_argument("--verbose", action="store_true", help="Verbose logs")
    return p.parse_args()

def main() -> None:
    args = parse_args()

    apply_actions = bool(args.apply)
    dry_run = True if not apply_actions else False
    if args.dry_run:
        dry_run = True

    vip_list: List[str] = [s.strip().lower() for s in args.vip_senders.split(",") if s.strip()]

    service = get_gmail_service(apply_actions=apply_actions)
    emails = fetch_recent_emails(
        service,
        fetch_n=args.fetch,
        since_days=args.since_days,
        max_body_chars=args.max_body_chars,
    )

    client = OllamaClient(base_url=SETTINGS.ollama_base_url)

    for email in emails:
        sender_email = normalize_sender(email.get("from", ""))

        triage = triage_email(
            client=client,
            model=args.model,
            email=email,
            label_prefix=args.label_prefix,
        )

        # VIP override (business rule)
        if sender_email in set(vip_list):
            triage.priority = "High"
            triage.star = True
            if triage.action == "None":
                triage.action = "Star"
            triage.reason = f"VIP sender ({sender_email}). " + triage.reason

        triage = apply_policy(
            triage,
            label_prefix=args.label_prefix,
            vip_senders=vip_list,
            archive_newsletters=args.archive_newsletters,
            archive_spam=args.archive_spam,
        )

        title = f"\"{email.get('subject','(no subject)')}\" from {email.get('from','')}"
        planned = {
            "category": triage.category,
            "priority": triage.priority,
            "action": triage.action,
            "label": triage.label,
            "star": triage.star,
            "archive": triage.archive,
            "reason": triage.reason,
        }

        if dry_run:
            print(f"\n[DRY-RUN] {title}")
            print(
                f"  -> category={triage.category} priority={triage.priority} "
                f"action={triage.action} label={triage.label} star={triage.star} archive={triage.archive}\n"
                f"  reason: {triage.reason}"
            )
        else:
            print(f"\n[APPLY] {title}")
            print(
                f"  -> category={triage.category} priority={triage.priority} "
                f"action={triage.action} label={triage.label} star={triage.star} archive={triage.archive}\n"
                f"  reason: {triage.reason}"
            )

            # Apply label if needed
            if triage.label:
                label_id = ensure_label(service, "me", triage.label)
                modify_message_labels(service, "me", email["id"], add_label_ids=[label_id])

            # Star
            if triage.star:
                star_message(service, "me", email["id"])

            # Archive
            if triage.archive:
                archive_message(service, "me", email["id"])

        # Audit log (local)
        append_jsonl(
            SETTINGS.log_path,
            {
                "ts": utc_now_iso(),
                "email_id": email.get("id"),
                "threadId": email.get("threadId"),
                "from": email.get("from"),
                "subject": email.get("subject"),
                "decision": planned,
                "mode": "dry-run" if dry_run else "apply",
                "model": args.model,
            },
        )

    print("\nDone.")
    print("Audit log:", SETTINGS.log_path)

if __name__ == "__main__":
    main()

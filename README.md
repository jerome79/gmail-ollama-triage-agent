# Gmail Ollama Triage Agent (Local AI Inbox Organizer)

A local-first AI agent that connects to Gmail, fetches recent emails, and uses an **Ollama LLM** to:
- Categorize emails (Finance / Sales / Support / Personal / Newsletter / Spam / Other)
- Assign priority (High / Medium / Low)
- Recommend an action (Label / Star / Archive / DraftReply / None)
- Optionally apply Gmail actions (labels/star/archive) — **never sends emails**

This project is designed as a portfolio-grade “working proof” and can be extended into a production-ready inbox assistant.

---

## What’s included (today)

### ✅ Phase 1 (this repo)
**Inbox triage + organization**
- Gmail OAuth2 authentication
- Fetch last N emails (or newer_than X days)
- Best-effort email body extraction (plain text preferred, HTML fallback)
- Local LLM inference via **Ollama**
- Strict JSON output + schema validation + retries
- Deterministic policy layer (keeps results consistent)
- **DRY-RUN by default** (safe)
- Optional `--apply` to:
  - Create/apply Gmail labels (e.g., `AI/Finance`)
  - Star important emails
  - Archive newsletters/spam
- Local audit log: `data/triage_runs.jsonl`

---

## Why this is safe (important)

- **No auto-sending emails** (ever)
- **Human-in-the-loop**: recommended actions are visible, and apply is explicit
- Default OAuth scope: **read-only** (`gmail.readonly`)
- Apply actions requires explicit flag and uses `gmail.modify`
- LLM inference is **local** via Ollama (privacy-friendly)

---

## Quickstart (10–15 minutes)

### 0) Prerequisites
- Python 3.10+ (recommended 3.11)
- Ollama installed and running locally
- A local model pulled (example: `llama3.1`)

Check Ollama:
```bash
curl http://localhost:11434/api/tags
ollama list

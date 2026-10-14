# magicpin Merchant AI Assistant

Contest bot: stateful HTTP service that composes WhatsApp-style merchant engagement from four judge-pushed contexts (category, merchant, customer, trigger).

**LLM**: Groq — primary `openai/gpt-oss-120b`, alternate `qwen/qwen3.6-27b`. Client enforces 30 RPM / 1K RPD / 8K TPM / 200K TPD (85% headroom) with deterministic fallback.

## Approach

1. **Fact-pack only** — allowlisted fields; never invent digests, offers, slots, or peer stats.  
2. **Kind-family prompts** — route `trigger.kind` (+ deterministic fallback when over quota / no key).  
3. **Restraint** — ranking, consent, suppression, soft tick deadline (~25s), max 3 actions/tick.  
4. **Multi-turn FSM** — rule-based auto-reply / intent / hostile / off-topic (no LLM).  
5. **Adaptive reads** — every compose re-fetches latest store version.

**Tradeoffs**: Groq quality vs tight TPM — we compact fact packs, cap output tokens, skip repair when TPM is tight, and fall back to deterministic rather than waiting on rate limits.

**What extra context would have helped**: live offer redemption rates, WhatsApp delivery receipts, merchant voice samples.

## Deliverables (§7)

| Artifact | Role |
|---|---|
| `bot.py` | Offline `compose(category, merchant, trigger, customer?)` |
| `submission.jsonl` | 30 frozen test-pair messages (deterministic) |
| `README.md` | This page |
| `conversation_handlers.py` | Optional multi-turn `respond(state, message)` |
| `bot/` + uvicorn | Live HTTP harness (`/v1/context`, `/v1/tick`, `/v1/reply`, …) |

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set LLM_API_KEY + LLM_PROVIDER=groq
uvicorn bot.app:app --host 0.0.0.0 --port 8080
```

```bash
python scripts/preflight_deploy.sh          # smokes + local judge
BOT_URL=http://127.0.0.1:8080 ./scripts/run_judge.sh phase2_short
./scripts/freeze_submission.sh              # regenerate submission.jsonl
```

## Deploy

```bash
docker compose up --build -d
# or: fly secrets set LLM_API_KEY=gsk_... LLM_PROVIDER=groq LLM_MODEL=openai/gpt-oss-120b && fly deploy
```

Keep **one** process up for the judge window (`auto_stop_machines = off` in `fly.toml`). Teardown: `POST /v1/teardown`.

## Vera Lab UI (interactive)

Explains the problem statement live: pick 4 contexts → compose WhatsApp draft → check judge rubric.

```bash
# bot on :8080 first (docker compose up -d)
cd frontend && npm install && npm run dev
# open http://localhost:5173
```

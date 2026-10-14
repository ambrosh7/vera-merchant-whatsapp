# Candidate bot (Phase E)

Contest-ready FastAPI bot: adaptive 4-context compose, ranking/consent, multi-turn reply FSM, soft tick deadline.

See root [`README.md`](../README.md) for approach, env vars, and deploy.

## Run

```bash
source .venv/bin/activate
cp ../.env.example ../.env   # set LLM_API_KEY optionally
uvicorn bot.app:app --host 0.0.0.0 --port 8080
```

## Smoke

```bash
python scripts/smoke_phase_a.py http://127.0.0.1:8080
python scripts/smoke_phase_b.py
python scripts/smoke_phase_c.py
python scripts/smoke_phase_d.py
python scripts/smoke_phase_e.py
```

## Endpoints

| Method | Path | Notes |
|---|---|---|
| GET | `/v1/healthz` | trivial liveness + counts |
| GET | `/v1/metadata` | team / model / approach |
| POST | `/v1/context` | versioned push; 409 on stale |
| POST | `/v1/tick` | latest-version compose + soft deadline |
| POST | `/v1/reply` | auto-reply / intent / hostile FSM |
| POST | `/v1/teardown` | wipe in-memory state |

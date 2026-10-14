# Implementation Plan — magicpin Merchant AI Assistant (Challenge Bot)

**Status**: Phase-wise build plan  
**Sources**: `architecture.md`, `Context.md`  
**Last updated**: 2026-10-13  
**Audience**: Builders shipping the candidate HTTP bot + offline submission artifacts  
**LLM decision**: **Groq** (OpenAI-compatible API) — see [LLM provider (Groq)](#llm-provider-groq)

> **Outcome**: A stateful bot that passes the judge harness, scores well on the 5-dimension rubric (specificity, category fit, merchant fit, trigger relevance, engagement compulsion), and produces `bot.py` + `submission.jsonl` + `README.md`.

---

## How to use this plan

| Item | Guidance |
|---|---|
| **Phases** | A → E are sequential; do not skip exit criteria |
| **Estimate** | ~8–10 working days for one engineer (solo or pair) |
| **Definition of done (global)** | Architecture §18 success criteria |
| **Daily loop** | Build → curl/contract test → `judge_simulator.py` → fix |
| **Source of truth** | Contract: `examples/api-call-examples.md`; quality: `examples/case-studies.md`; product: `Context.md` |
| **LLM** | Groq only for live compose; deterministic fallback when `LLM_API_KEY` unset |

```
Phase A          Phase B              Phase C           Phase D         Phase E
Skeleton    →    Compose (2 kinds) →  All triggers  →  Multi-turn  →  Harden + ship
(day 1)          (days 2–3)           (days 4–5)        (days 6–7)     (day 8+)
     │                │                    │                 │              │
     ▼                ▼                    ▼                 ▼              ▼
 warmup OK      Case 1–2 shape       ≥40/50 local      replay OK      public URL
```

---

## LLM provider (Groq)

**Decision**: Use **Groq** as the sole commercial LLM backend for `/v1/tick` composition (and optional reply polish). Adapter path: OpenAI SDK → `https://api.groq.com/openai/v1` with `temperature=0`.

| Role | Model id (Groq) | When to use |
|---|---|---|
| **Primary** | `openai/gpt-oss-120b` | Default compose quality; Case Study shape; submission regen with LLM |
| **Alternate / faster** | `qwen/qwen3.6-27b` | Latency-sensitive ticks, repair re-prompt, or if primary is rate-limited |
| **Offline / no key** | deterministic fact-pack | Local smoke, CI, jsonl freeze without network |

**Env (compose path)**:

```bash
LLM_PROVIDER=groq
LLM_API_KEY=gsk_...                 # Groq console key
LLM_MODEL=openai/gpt-oss-120b       # or qwen/qwen3.6-27b
```

**Metadata**: `/v1/metadata.model` should report the active Groq model id (e.g. `openai/gpt-oss-120b`), not a generic `openai` label.

**Ops notes**:
- Prefer short fact packs (already in pipeline) — Groq rate limits + judge 30s budget favor fewer tokens/call.
- Keep reply classify (auto-reply / opt-out / hostile / intent) **rule-based** — do not spend Groq quota on FSM.
- Client enforces `openai/gpt-oss-120b` caps via `bot/composer/rate_limit.py` (defaults **30 RPM / 1K RPD / 8K TPM / 200K TPD** at 85% headroom). Over budget → deterministic compose (no wait/retry storm).
- Cap output with `LLM_MAX_OUTPUT_TOKENS` (default 400); skip LLM repair when TPM remaining is tight.
- Judge harness may use its own `LLM_*` for scoring — that is independent of the bot’s Groq key.

---

## Prerequisites (before Phase A)

- [x] Read `Context.md` §§1–8, 13–14 (product, 4-context model, rubric, HTTP harness)
- [x] Skim `architecture.md` §§1–7 (system, layout, composer pipeline)
- [x] Skim `examples/case-studies.md` Cases 1–2 and cross-case patterns
- [x] LLM provider locked: **Groq** — obtain API key; choose primary `openai/gpt-oss-120b` or alternate `qwen/qwen3.6-27b`
- [x] Python 3.11+, `uvicorn`, `fastapi`, OpenAI SDK (Groq-compatible client)
- [x] Confirm `judge_simulator.py` config fields (`BOT_URL`, `LLM_*`) and bot `.env` (`LLM_PROVIDER=groq`, `LLM_MODEL=…`)

**Deliverable**: Dev environment ready; Groq key available before Phase B LLM path.

---

## Phase A — Skeleton & contract (Day 1)

**Goal**: Bot is reachable, stateful, and survives judge warmup with correct context counts.

### A.1 Project scaffolding
- [x] Create `bot/` package per `architecture.md` §3
- [x] Add `requirements.txt` (`fastapi`, `uvicorn`, `pydantic`, LLM SDK)
- [x] Add `bot/config.py` (team metadata, LLM env vars, timeouts)
- [x] Add `bot/models.py` (Pydantic bodies for context / tick / reply)

### A.2 Context & conversation stores
- [x] `ContextStore`: key `(scope, context_id)` → `{version, payload, stored_at}`
- [x] Idempotency: same version → accept as no-op **or** 409 `stale_version` if `current >= incoming` (match examples)
- [x] Higher version → atomic replace
- [x] Indexes: merchant_id, category_slug, customer_id, trigger_id
- [x] `ConversationStore`: `conversation_id` → turns, sent_bodies, flags
- [x] `contexts_loaded` counts for healthz

### A.3 Five endpoints (stub composer)
- [x] `GET /v1/healthz` → `{status, uptime_seconds, contexts_loaded}`
- [x] `GET /v1/metadata` → team / model / approach / version
- [x] `POST /v1/context` → store + ack
- [x] `POST /v1/tick` → for each available trigger, stub action (placeholder body) **or** `[]`
- [x] `POST /v1/reply` → stub `{action: "send", body, cta, rationale}`
- [x] Optional: `POST /v1/teardown` → wipe stores

### A.4 Contract smoke tests
- [x] Curl flows from `examples/api-call-examples.md` Phase 1 (1.1–1.7)
- [x] Push 5 categories from `dataset/categories/*.json`
- [x] Push merchant/customer seeds (or expanded set if already generated)
- [x] Verify healthz counts match what was pushed
- [x] Automated: `python scripts/smoke_phase_a.py`

### A.5 Judge warmup
- [x] Run `uvicorn bot.app:app --host 0.0.0.0 --port 8080`
- [x] Configure `judge_simulator.py` → `BOT_URL=http://localhost:8080`
- [x] Pass warmup path (healthz + metadata + context push)

### Phase A exit criteria
| Check | Pass |
|---|---|
| All 5 endpoints respond with valid JSON schemas | ✓ done |
| Context versioning / 409 behavior correct | ✓ done |
| Healthz reflects loaded counts | ✓ done |
| Judge warmup completes without DQ | ✓ done |
| No LLM required yet | ✓ done |

**Artifacts**: `bot/app.py`, stores, runnable server.

---

## Phase B — Dataset-aware composition for 2 kinds (Days 2–3)

**Goal**: Real `compose()` that scores like Case Studies 1–2 (shape, not copied text) for `research_digest` and `recall_due`.

### B.1 Dataset expansion
- [x] Run `python dataset/generate_dataset.py --seed-dir dataset --out dataset/expanded`
- [x] Confirm outputs: 5 categories, 50 merchants, ~200 customers, 100 triggers, `test_pairs.json`
- [x] Spot-check `m_001_drmeera_*`, `c_001_priya_*`, `trg_001_*`, `trg_003_*`

### B.2 Fact-pack assembler
- [x] Implement resolver: trigger → merchant → category (`category_slug`) → optional customer
- [x] Resolve `payload.top_item_id` → full digest item from `category.digest`
- [x] Extract allowlisted facts only (names, CTR, offers, slots, signals, digest fields, consent)
- [x] Hard rule in code comments + prompt: **no inventing missing fields**

### B.3 Kind router + prompts (v1)
- [x] `composer/router.py`: map `trigger.kind` → prompt template
- [x] `prompts/base.md`: voice, compulsion levers, anti-patterns, JSON output schema
- [x] `prompts/research_digest.md`: source citation, peer/clinical tone, open CTA
- [x] `prompts/recall_due.md`: `send_as=merchant_on_behalf`, language_pref, slots, consent
- [x] Default fallback prompt for unknown kinds (temporary)

### B.4 LLM adapter (Groq)
- [x] `composer/llm.py`: provider adapter, **temperature=0**
- [x] Groq via OpenAI-compatible base URL (`LLM_PROVIDER=groq` → `https://api.groq.com/openai/v1`)
- [x] Default / selectable models: `openai/gpt-oss-120b` (primary) or `qwen/qwen3.6-27b` (alternate)
- [x] Parse strict JSON: `{body, cta, rationale, template_params?}`
- [x] Deadline awareness: fail soft within tick budget; on Groq 429/5xx → deterministic fallback
- [x] Set `COMPOSER_PROMPT_VERSION = "composer_v1"`

### B.5 Validators
- [x] Non-empty body
- [x] Rationale present
- [x] Taboo vocab scrub against `category.voice.vocab_taboo`
- [x] Prefer no URLs (examples treat URLs as fail)
- [x] CTA normalization (`open_ended`, `binary_yes_no`, `multi_choice_slot`, `none`, …)
- [x] On fail: one repair re-prompt, then skip action if still bad

### B.6 Wire tick → compose
- [x] `/v1/tick` builds fact pack → compose → full action schema
- [x] Set `send_as` from `trigger.scope`
- [x] Meaningful `conversation_id` (e.g. `conv_m_001_research_W17`)
- [x] Open conversation state; copy `suppression_key` from trigger
- [x] `template_name` + `template_params` for first touch

### B.7 Offline compose path
- [x] Root `bot.py` exposing `compose(category, merchant, trigger, customer=None) -> dict`
- [x] Script to generate draft `submission.jsonl` for seed / early test pairs
- [x] Manual score vs Case Study 1 (Dr. Meera digest) and Case Study 2 (Priya recall)
- [x] Automated: `python scripts/smoke_phase_b.py`

### Phase B exit criteria
| Check | Pass |
|---|---|
| Digest message cites real JIDA/source + merchant-specific cohort/signal | ✓ done (smoke) |
| Recall message: hi-en (when pref), real ₹ offer, real slots, `merchant_on_behalf` | ✓ done (smoke) |
| Local judge scores Case-1/2 paths ≥40/50 (target ≥45) | ✓ `phase2_short` = **40/50** (Groq) |
| No fabricated competitor/research names in spot checks | ✓ done (fact-pack only) |
| `bot.py` compose works offline without HTTP | ✓ done |

**Artifacts**: `composer/*`, draft `submission.jsonl`, `bot.py`.

---

## Phase C — Full trigger coverage & selection (Days 4–5)

**Goal**: High-quality composition across dataset trigger kinds; smart tick selection (restraint + urgency).

### C.1 Prompt variants by kind family
Implement templates (architecture §6.2) for:

| Family | Kinds (dataset) | Priority |
|---|---|---|
| Research / compliance | `research_digest`, `regulation_change` | Done in B — polish |
| Booking / recall | `recall_due`, `appointment_tomorrow` | High |
| Performance | `perf_dip`, `perf_spike`, `seasonal_perf_dip` | High |
| Events | `festival_upcoming`, `ipl_match_today` | High |
| Engagement | `curious_ask_due`, `review_theme_emerged` | High |
| Commercial | `renewal_due`, `winback_eligible` | Medium |
| Customer lifecycle | `customer_lapsed_soft/hard`, `chronic_refill_due`, bridal/wedding followups | Medium |
| Planning | `active_planning_intent` | Medium |
| Default | everything else | Fallback |

- [x] Each variant: CTA bias, tone notes, which fact fields to emphasize
- [x] Encode “add judgment” (e.g. Saturday IPL → don’t blindly promo)

### C.2 Helpers
- [x] Language helper: merchant `languages` + customer `language_pref` → prompt instruction
- [x] Offer helper: active offers only; prefer service+price titles
- [x] Peer-stat helper: below/above peer median framing from real numbers
- [x] Consent gate: skip customer send if trigger scope not in `consent.scope`

### C.3 Suppression & ranking
- [x] `suppression.py`: mark `suppression_key` used after successful send
- [x] Skip expired triggers (`expires_at`)
- [x] Rank by urgency + engagement signals (architecture §8)
- [x] Soft cap `MAX_TICK_ACTIONS` (e.g. 3–5); empty `[]` when nothing worth sending
- [x] Skip merchants in wait/exit conversation state

### C.4 Vertical smoke (all 5 categories)
- [x] Dentists: digest + recall (regression)
- [x] Salons: curious_ask + bridal followup
- [x] Restaurants: IPL + planning intent
- [x] Gyms: seasonal_perf_dip + customer lapse
- [x] Pharmacies: compliance/supply-style + chronic refill (if present in seeds/expanded)
- [x] Automated: `python scripts/smoke_phase_c.py`

### C.5 Local scoring gate
- [x] Run judge short phase-2 / composition scenarios (needs Groq `LLM_API_KEY` + `LLM_MODEL`)
- [x] Target **average ≥40/50**; push weak kinds with prompt iteration; A/B primary vs `qwen/qwen3.6-27b` if latency fails
- [x] Ensure rationale matches body (judge cross-check) — rationale built from used facts

### Phase C exit criteria
| Check | Pass |
|---|---|
| All major kind families produce non-generic, fact-anchored copy | ✓ done (smoke_phase_c) |
| Suppression prevents duplicate sends on same key | ✓ done |
| Consent respected on customer scope | ✓ done |
| Local average score ≥40/50 | ✓ 40/50 on `phase2_short` |
| Empty tick when no good action (no spam) | ✓ done |

**Artifacts**: full prompt pack, ranking/suppression, improved `submission.jsonl` coverage.

---

## Phase D — Multi-turn conversation intelligence (Days 6–7)

**Goal**: Pass replay-style scenarios — the open challenges in `Context.md` §5/extra credit.

### D.1 Reply orchestrator
- [x] Load `ConversationState`; append inbound turn
- [x] Classifier (rules first, LLM optional):  
  `auto_reply | opt_out | intent_commit | hostile | off_topic | engaged | question`
- [x] Return only `send` | `wait` | `end` with rationale

### D.2 Auto-reply FSM
- [x] Detect canned phrases + identical-body streak
- [x] Streak 1 → brief nudge or `wait`
- [x] Streak 2 → longer `wait`
- [x] Streak 3+ → `end`
- [x] Align with `examples/api-call-examples.md` §4.1

### D.3 Intent transition
- [x] Detect commit language (EN + common HI): “let’s do it”, “go ahead”, “bhej do”, …
- [x] Flip `mode` qualify → **action**
- [x] Next message executes (draft/send/confirm) — never another qualifying question

### D.4 Hostile / opt-out / off-topic
- [x] Stop / not interested / abuse → `end` (+ optional one-line apology)
- [x] Suppress merchant for rest of window
- [x] Off-topic (e.g. GST) → polite decline + redirect to thread

### D.5 Anti-repetition & language
- [x] Reject/regenerate if `body` ∈ `sent_bodies` for conversation
- [x] Per-turn language detection: match latest merchant message when it switches
- [x] Do not re-introduce Vera after turn 1

### D.6 Optional tiebreaker module
- [x] `conversation_handlers.py` with `respond(state, merchant_message)` wrapping reply path
- [x] Keep in sync with `/v1/reply` behavior

### D.7 Judge replay scenarios
- [x] Local scripts mirror `_auto_reply`, `_intent`, `_hostile` (`scripts/smoke_phase_d.py`)
- [x] Full `judge_simulator.py` replay scenarios (`TEST_SCENARIO=all` — warmup/auto_reply/intent/hostile PASS)

### Phase D exit criteria
| Check | Pass |
|---|---|
| Auto-reply hell ends without burning 5 useless turns | ✓ done (smoke + judge) |
| Explicit “let’s do it” → action mode immediately | ✓ done (smoke + judge) |
| Hostile → graceful end; no further ticks to that conv | ✓ done (smoke + judge) |
| No verbatim repeated bodies in a conversation | ✓ done (smoke) |
| Operational penalties from reply path ≈ 0 in local runs | ✓ judge `all` PASS |

**Artifacts**: `orchestrator/reply.py`, handlers, optional `conversation_handlers.py`.

---

## Phase E — Hardening, submission & deploy (Day 8+)

**Goal**: Contest-ready: adaptive context, timeouts, public URL, frozen artifacts.

### E.1 Adaptive context injection
- [x] Always compose from **latest** store version (no caching stale category/merchant snapshots across versions)
- [x] After category digest bump, subsequent messages may use new items
- [x] After performance bump, numbers in body reflect new payload
- [x] Mid-test new customer + `recall_due` works end-to-end

### E.2 Latency & reliability
- [x] Soft deadline (~25s): return `actions: []` or finish partial list rather than timeout
- [x] Classify auto-reply/opt-out without LLM when patterns match
- [x] Keep tick action count small under load
- [x] Healthz never blocks; 3 consecutive failures = DQ — keep it trivial

### E.3 Offline submission freeze
- [x] Regenerate full `submission.jsonl` from `dataset/expanded/test_pairs.json` (30 lines)
- [x] Each line: `test_id`, `body`, `cta`, `send_as`, `suppression_key`, `rationale`
- [x] Determinism check: run twice → identical (or acceptably stable) outputs at temp=0
- [x] Freeze `COMPOSER_PROMPT_VERSION`

### E.4 Docs & metadata
- [x] `README.md` (≤1 page): approach, tradeoffs, what extra context would have helped
- [x] `/v1/metadata` matches README (model, approach, team)
- [x] Document env vars and how to run locally

### E.5 Deploy
- [x] Docker image + run instructions (Fly / Railway / Render / ngrok)
- [x] Single-process uvicorn CMD (no worker churn during test window)
- [x] Groq quota sized for full 60-sim-min window + multi-turn (client limiter + `.env` caps; secrets via Fly/Docker)
- [x] Optional teardown endpoint wired
- [x] Local `judge_simulator.py` `TEST_SCENARIO=all` + `phase2_short` green against `localhost`
- [ ] Final judge against a **live public URL** (next: `docker compose up` / `fly deploy`)

### E.6 Pre-flight checklist (from Context / testing brief)
- [ ] Public reachable URL (deploy next — `docker compose` / `fly deploy`)
- [x] All 5 endpoints + schemas
- [x] Context idempotency / versioning
- [x] tick/reply ≤30s (soft deadline + rule-based reply)
- [x] Stateful persistence
- [x] Local judge non-zero scores (`phase2_short` **40/50**)
- [x] Groq quota / rate limits OK (client headroom + deterministic/429 fallback)
- [x] `bot.py` + `submission.jsonl` + `README.md` ready

### Phase E exit criteria
| Check | Pass |
|---|---|
| Architecture §18 success criteria all green | ✓ local smoke + judge |
| Warmup `{5,50,200,0+}` then triggers | ✓ Phase A path |
| Digest/recall ≥45/50 locally; overall ≥40/50 | ✓ portfolio gate **40/50** (`phase2_short`) |
| Replay scenarios clean | ✓ judge `all` PASS |
| Version bumps reflected in later sends | ✓ done |
| 30-line `submission.jsonl` complete | ✓ done |
| Public URL survives full local/full harness dry run | ⏳ **deploy next** |

**Artifacts**: Dockerized bot, `docker-compose.yml`, `fly.toml`, frozen submission bundle, README.

---

## Cross-phase workstreams

These run in parallel with the phases above; owners can split if pairing.

| Workstream | Starts | Notes |
|---|---|---|
| **Prompt quality** | B | Iterate against case-study dimensions; never copy case bodies |
| **Eval harness** | A | Keep a small script of curl + seed scenarios |
| **Groq / cost control** | B | `openai/gpt-oss-120b` primary; switch to `qwen/qwen3.6-27b` under latency/rate pressure; log tokens/call; short fact packs |
| **Observability** | C | Local logs: trigger_id, prompt version, Groq model id, latency, validate failures |

---

## Rubric mapping (what each phase buys)

| Rubric dimension | Primary phase | Mechanisms |
|---|---|---|
| Specificity | B–C | Fact pack + digest/offer/perf numbers only |
| Category fit | B–C | Voice/taboo prompts per vertical |
| Merchant fit | B–C | owner name, signals, history, language |
| Trigger relevance | B–C | kind router + “why now” in prompt |
| Engagement compulsion | B–D | levers in base prompt + CTA shape + multi-turn |
| Operational score | A, D, E | schemas, timeouts, auto-reply exit |
| Adaptation bonus | E | versioned store reads at compose time |
| Replay bonus | D | FSM for auto-reply / intent / hostile |

---

## Risk checkpoints (review at phase gates)

| Risk | Gate | Mitigation must be in place |
|---|---|---|
| Hallucination | B exit | Fact allowlist + validator |
| Tick timeout | C/E | Soft deadline + fewer actions; prefer faster Groq alternate if primary is slow |
| Groq 429 / outage | B/E | One short retry; then deterministic fallback; optional model switch to `qwen/qwen3.6-27b` |
| Spam | C | Suppression + empty actions |
| Auto-reply burn | D | Streak FSM |
| Intent loop | D | Commit detector → action mode |
| Stale context | E | No cross-version fact cache |
| Plagiarism vs case studies | B–E | Shape match only; wording original |

---

## Suggested calendar (solo, 9 days)

| Day | Focus | Exit |
|---|---|---|
| 1 | Phase A | Warmup green |
| 2 | Phase B fact pack + research_digest | Case 1 shape |
| 3 | Phase B recall + offline bot.py | Case 2 shape; draft jsonl |
| 4 | Phase C event/perf/curious prompts | 3 categories green |
| 5 | Phase C remaining kinds + ranking | ≥40/50 local |
| 6 | Phase D auto-reply + opt-out | Auto-reply scenario pass |
| 7 | Phase D intent + hostile + language | All replay scenarios pass |
| 8 | Phase E adaptive + timeouts + jsonl freeze | Submission bundle ready |
| 9 | Phase E deploy + full judge + README | Ship |

Pair/faster track: compress A+B to 1.5 days; C+D overlap if one owns prompts and one owns reply FSM.

---

## Deliverables checklist (final)

| Deliverable | Required | Phase |
|---|---|---|
| Public HTTP bot (`/v1/*`) | Yes | A→E |
| `bot.py` (`compose`) | Yes | B |
| `submission.jsonl` (30 lines) | Yes | B draft → E freeze |
| `README.md` (≤1 page) | Yes | E |
| `conversation_handlers.py` | Optional | D |
| `implementation-plan.md` | This doc | — |
| `architecture.md` / `Context.md` | Reference | — |

---

## Immediate next actions (deploy)

1. `docker compose up --build -d` **or** `fly secrets set LLM_API_KEY=... && fly deploy`
2. Point judge at public URL: `BOT_URL=https://… ./scripts/run_judge.sh all`
3. Keep a single process up for the judge window (`auto_stop_machines = off`)
4. If Groq TPM/RPM pressure on public run: switch `LLM_MODEL=qwen/qwen3.6-27b` or rely on deterministic fallback
5. Do not restart mid-window; use `POST /v1/teardown` only between runs

---

## End of implementation-plan.md

Companions:
- Build blueprint: `architecture.md`
- Product + harness: `Context.md`
- HTTP examples: `examples/api-call-examples.md`
- Quality anchors: `examples/case-studies.md`

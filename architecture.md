# Architecture — magicpin Merchant AI Assistant (Challenge Bot)

**Status**: Build blueprint for this repo  
**Sources**: `Context.md`, `dataset/`, `examples/`, `judge_simulator.py`  
**Last updated**: 2026-10-13  
**Audience**: Engineers implementing the candidate bot end-to-end

> Goal: ship a **stateful HTTP bot** that receives 4-context pushes from the judge, initiates WhatsApp-style conversations on `/v1/tick`, and handles multi-turn replies on `/v1/reply` — composing messages that beat production Vera on specificity, category fit, merchant fit, trigger relevance, and engagement compulsion.

---

## 1. System overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         JUDGE HARNESS                                    │
│  (warmup → context push → tick loop → reply sim → adaptive injection)   │
│  Local: judge_simulator.py  |  Contest: magicpin remote harness         │
└───────────────┬─────────────────────────────────────▲───────────────────┘
                │ HTTPS/JSON                          │
                │ POST /v1/context                    │
                │ POST /v1/tick                       │
                │ POST /v1/reply                      │
                │ GET  /v1/healthz|/v1/metadata       │
                ▼                                     │
┌─────────────────────────────────────────────────────────────────────────┐
│                      CANDIDATE BOT (this project)                        │
│                                                                         │
│  ┌──────────────┐   ┌─────────────────┐   ┌──────────────────────────┐ │
│  │ API Layer    │──►│ Context Store   │──►│ Orchestrator             │ │
│  │ (FastAPI)    │   │ (versioned KV)  │   │ tick / reply / suppress  │ │
│  └──────────────┘   └─────────────────┘   └────────────┬─────────────┘ │
│                                                         │               │
│                                                         ▼               │
│                                          ┌──────────────────────────┐   │
│                                          │ Engagement Composer      │   │
│                                          │  router → prompt → LLM   │   │
│                                          │  → validate → action     │   │
│                                          └──────────────────────────┘   │
│                                                         │               │
│                                          ┌──────────────────────────┐   │
│                                          │ Conversation State       │   │
│                                          │ turns, auto-reply flags, │   │
│                                          │ intent mode, sent bodies │   │
│                                          └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                │
                │ (optional) commercial LLM APIs only
                ▼
        OpenAI / Anthropic / Gemini / DeepSeek / …
```

**Non-goals for the challenge bot**
- No real Meta / Kaleyra WhatsApp sends
- No calls to production vera-mcp / aryan / Redis
- No outbound of merchant/customer payloads to non-LLM APIs

**Goals**
- Survive warmup (255 base contexts loaded)
- Compose high-scoring messages from real dataset fields only
- Handle auto-reply, intent transition, hostile/off-topic gracefully
- Adapt when judge bumps context versions mid-test

---

## 2. Design principles

| Principle | Implication |
|---|---|
| **Contexts are the only truth** | Never invent digest titles, peer stats, offers, slots, or competitor names |
| **One composer, two surfaces** | Same `compose()` for merchant (`send_as=vera`) and customer (`send_as=merchant_on_behalf`) |
| **Trigger decides *why now*** | Every outbound action must cite a `trigger_id` |
| **Dispatch by `kind`** | Prompt variants for research vs recall vs IPL vs curious_ask |
| **Stateful + versioned** | `(scope, context_id) → {version, payload}`; higher version replaces atomically |
| **Restraint > spam** | Empty `actions: []` is valid; suppress used keys; cap actions/tick |
| **≤30s budget** | Tick/reply must return within timeout; prefer fast model + tight prompts |
| **North star = case studies** | Match *shape* from `examples/case-studies.md`, never copy bodies |

---

## 3. Recommended repo layout

```
magicpin-merchant-ai-assitant/
├── Context.md                 # consolidated product/context brief
├── architecture.md            # this file
├── problemStatement.md
├── challenge-testing-brief.md
├── engagement-design.md
├── engagement-research.md
├── judge_simulator.py
├── dataset/
│   ├── categories/*.json      # 5 complete CategoryContexts
│   ├── merchants_seed.json    # 10 seeds → expand to 50
│   ├── customers_seed.json    # 15 seeds → expand to 200
│   ├── triggers_seed.json     # 25 seeds → expand to 100
│   └── generate_dataset.py    # writes expanded/ + test_pairs.json
├── examples/
│   ├── api-call-examples.md   # HTTP contract walkthrough
│   └── case-studies.md        # 10 scoring anchors
│
└── bot/                       # ← implement here
    ├── __init__.py
    ├── app.py                 # FastAPI app + 5 endpoints
    ├── config.py              # env: LLM keys, team metadata, timeouts
    ├── models.py              # Pydantic request/response schemas
    ├── store/
    │   ├── context_store.py   # versioned context KV
    │   └── conversation_store.py
    ├── orchestrator/
    │   ├── tick.py            # trigger selection → actions
    │   ├── reply.py           # auto-reply / intent / hostile routing
    │   └── suppression.py     # suppression_key + anti-spam
    ├── composer/
    │   ├── composer.py        # EngagementComposer.compose()
    │   ├── router.py          # kind → prompt variant
    │   ├── prompts/           # versioned prompt templates
    │   │   ├── base.md
    │   │   ├── research_digest.md
    │   │   ├── recall_due.md
    │   │   ├── perf_*.md
    │   │   ├── festival_ipl.md
    │   │   ├── curious_ask.md
    │   │   └── customer_default.md
    │   ├── validators.py      # CTA, taboos, language, no-URL policy
    │   └── llm.py             # provider adapter (temp=0)
    ├── handlers/
    │   ├── auto_reply.py
    │   ├── intent.py
    │   └── language.py
    ├── compose_offline.py     # for submission.jsonl (30 test pairs)
    ├── requirements.txt
    └── README.md
```

Offline artifacts (also required by problem brief):
- `bot.py` — thin re-export of `compose(category, merchant, trigger, customer) → dict` for offline judging
- `submission.jsonl` — 30 lines from `test_pairs.json`
- Optional `conversation_handlers.py` with `respond(state, merchant_message)`

---

## 4. Data model

### 4.1 Context store

```python
# key = (scope, context_id)
# value = { "version": int, "payload": dict, "stored_at": iso }

scopes = {"category", "merchant", "customer", "trigger"}
```

Rules (from `examples/api-call-examples.md`):
1. Same `(context_id, version)` → no-op / **409** `stale_version` if already stored at ≥ that version
2. Higher `version` → atomic replace of entire payload
3. Persist for the whole test window (in-memory OK; no restarts)

Indexes the bot should maintain for O(1) joins:

| Index | Purpose |
|---|---|
| `merchant_id → merchant` | tick composition |
| `category_slug → category` | join via `merchant.category_slug` |
| `customer_id → customer` | customer-scoped triggers |
| `trigger_id → trigger` | tick `available_triggers` |
| `suppression_key → used_at` | dedup across ticks |
| `conversation_id → ConversationState` | reply continuity |

### 4.2 Dataset shapes (what the judge pushes)

**Category** (`dataset/categories/{slug}.json`) — already complete for 5 verticals:

| Field | Use in composition |
|---|---|
| `voice.tone`, `vocab_allowed`, `vocab_taboo` | category fit + taboo filter |
| `offer_catalog[]` | prefer service+price over % off |
| `peer_stats` | comparative anchors (CTR, reviews) |
| `digest[]` | research/compliance hooks; resolve `top_item_id` |
| `patient_content_library[]` | patient-ed drafts |
| `seasonal_beats`, `trend_signals` | timing / curiosity |

**Merchant** (seed → expanded):

| Field | Use |
|---|---|
| `identity.name`, `owner_first_name`, `languages`, `locality`, `city` | salutation + language |
| `subscription` | renewal / winback triggers |
| `performance` + `delta_7d` | perf_dip / spike / seasonal |
| `offers[]` (active) | real catalog prices only |
| `conversation_history[]` | anti-repetition + continuity |
| `customer_aggregate` | "your 124 high-risk adults" style anchors |
| `signals[]` | which levers are relevant |
| `review_themes[]` | review_theme_emerged |

**Customer**:

| Field | Use |
|---|---|
| `identity.language_pref`, `name` | code-mix / salutation |
| `relationship.*` | recall math, service history |
| `state` | new / active / lapsed_* / churned framing |
| `preferences.preferred_slots` | slot selection |
| `consent.scope` | never message outside consent |

**Trigger**:

| Field | Use |
|---|---|
| `kind`, `scope`, `source` | prompt router + `send_as` |
| `merchant_id`, `customer_id` | join keys |
| `payload` | fact anchors (digest id, slots, match, batches) |
| `urgency` | ranking among available triggers |
| `suppression_key`, `expires_at` | dedup + staleness |

### 4.3 Dataset generation pipeline

```bash
cd dataset
python generate_dataset.py --seed-dir . --out ./expanded
```

Produces:
```
expanded/
├── categories/     # 5 (copied)
├── merchants/      # 50
├── customers/      # ~200
├── triggers/       # 100
└── test_pairs.json # 30 canonical pairs → submission.jsonl
```

Deterministic (`SEED = 20260426`). Local judge loads from `dataset/` (seeds + categories); contest harness pushes full expanded payloads via `/v1/context`.

### 4.4 Conversation state

```python
@dataclass
class ConversationState:
    conversation_id: str
    merchant_id: str
    customer_id: str | None
    trigger_id: str
    send_as: Literal["vera", "merchant_on_behalf"]
    turns: list[Turn]                 # {from, body, ts, turn_number}
    sent_bodies: set[str]             # anti-repetition
    auto_reply_streak: int            # identical canned replies
    mode: Literal["qualify", "action", "exit"]
    suppressed: bool                  # hard stop / opt-out
    wait_until: datetime | None
    language_observed: str | None     # per-turn detection
```

---

## 5. HTTP API layer

Implement exactly the contract in `challenge-testing-brief.md` / `examples/api-call-examples.md`.

| Endpoint | Role | Latency budget |
|---|---|---|
| `GET /v1/healthz` | liveness + `contexts_loaded` counts | ~2s |
| `GET /v1/metadata` | team / model / approach | ~2s |
| `POST /v1/context` | versioned push | ~5s |
| `POST /v1/tick` | proactive outbound actions | ≤30s (judge often waits ~10–15s locally) |
| `POST /v1/reply` | continue conversation | ≤30s |

Optional: `POST /v1/teardown` → wipe stores.

### 5.1 `/v1/context` flow

```
receive body → validate scope
  → lookup (scope, context_id)
  → if existing.version >= body.version → 409 stale_version
  → else store payload, update indexes
  → 200 {accepted, ack_id, stored_at}
```

### 5.2 `/v1/tick` flow

```
for each trigger_id in available_triggers (hint):
  load trigger; skip if missing / expired / suppressed
  load merchant (+ customer if scope=customer)
  load category via merchant.category_slug
  rank by urgency, freshness, merchant engagement signals
select ≤20 actions (prefer quality; often 0–3)
for each selected:
  compose(...) → validate → build action dict
  open ConversationState; mark suppression_key used
return {actions: [...]}
```

**Action schema** (required fields):
```json
{
  "conversation_id": "conv_m_001_drmeera_research_W17",
  "merchant_id": "...",
  "customer_id": null,
  "send_as": "vera",
  "trigger_id": "...",
  "template_name": "vera_research_digest_v1",
  "template_params": ["...", "...", "..."],
  "body": "...",
  "cta": "open_ended",
  "suppression_key": "...",
  "rationale": "..."
}
```

Rules:
- New `conversation_id` only on tick (never reuse here)
- One action per `(merchant_id, conversation_id)` per tick
- Empty list is valid
- `send_as`: `vera` if `trigger.scope == "merchant"`; `merchant_on_behalf` if `"customer"`

### 5.3 `/v1/reply` flow

```
load ConversationState
append merchant/customer message
classify: auto_reply | opt_out | intent_commit | hostile | off_topic | engaged | question
branch:
  auto_reply → streak++; maybe wait / end (see §7)
  opt_out / hostile → end (optional short apology)
  intent_commit → mode=action; compose next step (no more qualifying)
  off_topic → polite decline + redirect to thread
  engaged → compose follow-up using same 4 contexts + history
return {action: send|wait|end, ...}
```

---

## 6. Composer architecture

### 6.1 Core interface

```python
def compose(
    category: dict,
    merchant: dict,
    trigger: dict,
    customer: dict | None = None,
    *,
    conversation: ConversationState | None = None,
) -> dict:
    """
    Returns:
      body, cta, send_as, suppression_key, rationale,
      template_name, template_params  # for first-touch tick actions
    """
```

Used by:
1. `/v1/tick` (no conversation yet)
2. `/v1/reply` (with conversation history)
3. Offline `submission.jsonl` generation

### 6.2 Pipeline stages

```
┌─────────────┐   ┌──────────────┐   ┌─────────────┐   ┌───────────┐
│ 1. Assemble │──►│ 2. Route by  │──►│ 3. LLM      │──►│ 4. Validate│
│ fact pack   │   │ trigger.kind │   │ compose     │   │ + repair   │
└─────────────┘   └──────────────┘   └─────────────┘   └─────┬─────┘
                                                             │
                                                             ▼
                                                      ┌─────────────┐
                                                      │ 5. Emit     │
                                                      │ action dict │
                                                      └─────────────┘
```

#### Stage 1 — Assemble fact pack (no LLM)

Extract only verifiable fields the prompt may use:

```python
facts = {
  "owner_first_name": merchant["identity"].get("owner_first_name"),
  "biz_name": merchant["identity"]["name"],
  "locality": ..., "city": ...,
  "languages": ...,
  "peer_ctr": category["peer_stats"]["avg_ctr"],
  "merchant_ctr": merchant["performance"]["ctr"],
  "signals": merchant.get("signals", []),
  "active_offers": [o for o in merchant["offers"] if o["status"] == "active"],
  "digest_item": resolve_digest(category, trigger["payload"].get("top_item_id")),
  "customer_name": customer["identity"]["name"] if customer else None,
  "language_pref": customer["identity"].get("language_pref") if customer else None,
  "slots": trigger["payload"].get("available_slots"),
  # ... kind-specific payload fields only
}
```

**Hard rule**: prompt must say "use ONLY these facts; if missing, omit — do not invent."

#### Stage 2 — Route by `trigger.kind`

| Kind family | Prompt variant | CTA bias | send_as |
|---|---|---|---|
| `research_digest`, `regulation_change` | source-citation + peer tone | open_ended / binary | vera |
| `recall_due`, `appointment_tomorrow` | warm-clinical booking | multi_choice_slot / binary | merchant_on_behalf |
| `perf_dip`, `perf_spike`, `seasonal_perf_dip` | operator analytics | binary / open_ended | vera |
| `festival_upcoming`, `ipl_match_today` | event + existing offer leverage | binary | vera |
| `curious_ask_due` | ask-the-merchant | open_ended | vera |
| `review_theme_emerged` | quote + fix proposal | binary | vera |
| `renewal_due`, `winback_eligible` | loss aversion + concrete value | binary | vera |
| `bridal_followup`, `wedding_package_followup` | timeline + package | binary | merchant_on_behalf |
| `customer_lapsed_*`, `chronic_refill_due` | no-shame / trustworthy | binary | merchant_on_behalf |
| `active_planning_intent` | deliver drafted artifact | binary | vera |
| default | base + facts | open_ended | by scope |

#### Stage 3 — LLM call

- `temperature=0` (determinism requirement)
- System: voice rules, taboos, compulsion levers, anti-patterns
- User: structured JSON of fact pack + short instruction for this kind
- Output: strict JSON `{body, cta, rationale, template_params}`

Keep prompts short: pass **selected facts**, not entire 50-merchant dump.

#### Stage 4 — Validate / repair

| Check | On failure |
|---|---|
| Body non-empty | re-prompt or skip action |
| No verbatim repeat in conversation | regenerate |
| No taboo vocab (`category.voice.vocab_taboo`) | strip/rephrase |
| Language matches merchant/customer pref | regenerate |
| Single CTA shape | normalize |
| Facts referenced exist in fact pack | strip hallucinated numbers |
| URLs | follow contest policy (examples mark URL as hard fail; prefer no URLs unless brief allows) |
| Rationale present and consistent | rewrite rationale from used facts |

#### Stage 5 — Emit

Fill `template_name` / `template_params` for first outbound (24h window simulation). Reuse `trigger.suppression_key`.

---

## 7. Multi-turn intelligence (scoring differentiators)

### 7.1 Auto-reply detection

Signals (from case studies + replay examples):
- Phrases like "Thank you for contacting…", "Our team will respond shortly", "I am an automated assistant"
- Same message body repeated ≥2–3 times in a row

Policy (aligned with `examples/api-call-examples.md` §4.1):

| Streak | Action |
|---|---|
| 1 | Optional short "looks like auto-reply — reply YES when owner sees this" **or** `wait` |
| 2 | `wait` (hours → day) |
| 3+ | `end` — stop burning turns |

### 7.2 Intent transition

Detect commit phrases: "let's do it", "ok go ahead", "yes send it", "what's next?", Hindi equivalents ("haan kar do", "bhej do").

On detect: set `mode=action` and **execute** (draft, send abstract, confirm next step) — never another qualifying question. This is a top-10 replay scenario.

### 7.3 Hostile / opt-out

"Stop", "not interested", abuse → `end` (optional one-line apology). Suppress merchant triggers for remainder of test window.

### 7.4 Off-topic

GST / unrelated asks → politely decline + redirect to original trigger thread.

### 7.5 Language per turn

If merchant switches Hindi ↔ English mid-thread, match the latest turn. Prefer hi-en mix when `languages` includes `hi` or `language_pref` is `hi-en mix` / regional mixes (`te-en`, `kn-en`).

---

## 8. Trigger selection & suppression

On each tick:

1. Filter `available_triggers` to those present, not expired (`expires_at > now`), not suppressed.
2. Skip if merchant already has an open conversation in `wait` / `exit`.
3. Rank score roughly:
   ```
   score = urgency * 10
         + (4 if merchant engaged_in_last_48h else 0)
         - (5 if dormant_with_vera and kind is low-urgency curiosity)
         + kind_priority_bonus
   ```
4. Prefer customer-scoped recalls when consent allows.
5. Cap sends; when unsure, return `[]`.

Suppression keys from dataset (examples):
- `research:dentists:2026-W17`
- `recall:c_001_priya_for_m001:6mo`
- `ipl:m_005:2026-04-26`

Once used successfully, do not re-fire the same key in the test window.

---

## 9. Quality bar (from case studies)

Implement composition so the judge can score 9–10 on each dimension:

1. **Cite sources** for research/compliance (JIDA p.14, DCI circular, batch IDs).
2. **Numbers only from contexts** (`customer_aggregate`, `performance`, digest `trial_n`).
3. **Use owner first name** when present (`Meera`, `Lakshmi`, `Karthik`).
4. **One low-friction next step** ("Want me to draft X? Live in 10 min").
5. **Honor language + relationship state** on customer sends.
6. **Use category vocabulary correctly** (fluoride varnish, covers, sub-potency, ad spend).
7. **Add judgment**, not templates (e.g. Saturday IPL → skip match promo, push delivery BOGO).
8. **Meaningful `conversation_id`** (`conv_priya_recall_2026_11`).
9. **Rationale matches body** (judge cross-checks).
10. **No repetition, no fabrication** — hard floor.

Compulsion levers to encode in base prompt: specificity, loss aversion, social proof, effort externalization, curiosity, reciprocity, asking-the-merchant, single binary CTA.

---

## 10. End-to-end sequences

### 10.1 Warmup (judge)

```
GET  /v1/healthz          → contexts all 0
GET  /v1/metadata
POST /v1/context × 5      category
POST /v1/context × 50     merchant
POST /v1/context × 200    customer
GET  /v1/healthz          → {category:5, merchant:50, customer:200, trigger:0}
```

### 10.2 Merchant research digest (happy path)

```
POST /v1/context  trigger trg_001_research_digest_dentists
POST /v1/tick     available_triggers=[trg_001...]
  → action send_as=vera, body cites JIDA + high_risk_adult_count
POST /v1/reply    "Yes please send the abstract..."
  → action=send with abstract + patient draft + binary CTA
```

### 10.3 Customer recall

```
POST /v1/context  customer c_001_priya...
POST /v1/context  trigger trg_003_recall_due_priya
POST /v1/tick
  → send_as=merchant_on_behalf, hi-en mix, slots from payload, ₹299 offer
```

### 10.4 Adaptive injection

```
POST /v1/context  category dentists version=2  (new digest item)
POST /v1/tick / reply later
  → subsequent messages may reference NEW item; never stale-only facts
```

---

## 11. Offline submission path

Parallel to the HTTP bot:

```
generate_dataset.py → expanded/test_pairs.json (30 pairs)
                 ↓
for each pair:
  load category, merchant, trigger, optional customer
  compose(...) → append line to submission.jsonl
```

Also expose:

```python
# bot.py
from bot.composer.composer import compose as _compose

def compose(category, merchant, trigger, customer=None):
    return _compose(category, merchant, trigger, customer)
```

Deterministic: fixed model temperature 0, stable prompt versions, no nondeterministic sampling of facts.

---

## 12. LLM & config

```python
# bot/config.py (env-driven)
TEAM_NAME = ...
LLM_PROVIDER = "openai" | "anthropic" | "gemini" | "deepseek" | ...
LLM_API_KEY = ...
LLM_MODEL = ...
COMPOSER_PROMPT_VERSION = "composer_v1"
MAX_TICK_ACTIONS = 5          # soft cap under judge's 20
TICK_DEADLINE_SECONDS = 25    # leave buffer under 30s
```

Recommendations:
- Frontier model for composition quality; smaller/faster OK for classification (auto-reply / intent) if needed
- Cache nothing across tests that would leak state after teardown
- Log prompt version + context hash per send (local debug; helpful rationale)

Privacy: LLM APIs allowed; do not POST merchant/customer payloads to other external services.

---

## 13. Implementation phases

### Phase A — Skeleton (day 1)
- [ ] FastAPI app with 5 endpoints
- [ ] In-memory context + conversation stores with versioning
- [ ] Stub composer returning placeholder bodies
- [ ] Pass `judge_simulator.py` warmup + healthz counts

### Phase B — Dataset-aware compose (days 2–3)
- [ ] Run `generate_dataset.py`
- [ ] Fact-pack assembler + kind router
- [ ] Real LLM composer for `research_digest` + `recall_due`
- [ ] Validators (taboo, empty body, rationale)
- [ ] Produce draft `submission.jsonl` for seed pairs
- [ ] Match Case Studies 1–2 shape (not text)

### Phase C — Trigger coverage (days 4–5)
- [ ] Prompt variants for perf, festival/IPL, curious_ask, review_theme, renewal, lapsed, refill, planning
- [ ] Suppression + urgency ranking
- [ ] Language / offer / peer-stat helpers
- [ ] Score ≥40/50 average on local judge for short phase-2

### Phase D — Multi-turn (days 6–7)
- [ ] Auto-reply streak machine
- [ ] Intent → action mode
- [ ] Hostile / off-topic handlers
- [ ] Anti-repetition across turns
- [ ] Pass local `_auto_reply`, `_intent`, `_hostile` scenarios

### Phase E — Hardening (day 8+)
- [ ] Adaptive version bumps respected
- [ ] Timeout guards (return `[]` / safe `wait` if near deadline)
- [ ] Deploy public URL; full `judge_simulator` run
- [ ] README + metadata + teardown
- [ ] Freeze prompt version; regenerate `submission.jsonl`

---

## 14. Testing strategy

| Layer | How |
|---|---|
| Unit | context versioning, suppression, auto-reply classifier, fact resolver for `top_item_id` |
| Contract | curl flows from `examples/api-call-examples.md` |
| Composition | golden checks against case-study *dimensions* (not string equality) |
| Integration | `python judge_simulator.py` with `TEST_SCENARIO=all` |
| Regression | replay auto-reply / intent / hostile after every prompt change |

Local loop:
```bash
# terminal 1
uvicorn bot.app:app --host 0.0.0.0 --port 8080

# terminal 2
export BOT_URL=http://localhost:8080
# configure LLM_* in judge_simulator.py
python judge_simulator.py
```

---

## 15. Deployment

Any public URL hosting `/v1/*`:
- Render / Fly / Railway / GCP Cloud Run / AWS / ngrok→localhost

Requirements:
- No restart during the ~60 simulated-minute window
- LLM quota sized for warmup + ~12 ticks × multi-turn + adaptive injections
- Healthz reflects true `contexts_loaded` counts

---

## 16. Mapping: production Vera → challenge bot

| Production concept | Challenge equivalent |
|---|---|
| `_merchant_snapshot` + Redis | `/v1/context` merchant payloads in ContextStore |
| Category string in aryan | Full `CategoryContext` JSON from dataset |
| Ad-hoc followup crons | Judge-pushed `TriggerContext` + `/v1/tick` |
| Per-agent prompt builders | Single `EngagementComposer` + kind router |
| Kaleyra templates | `template_name` + `template_params` fields (not sent to Meta) |
| Customer info pack | CustomerContext push + recall triggers |

The challenge bot is a **clean-room implementation of the engagement design**, not a wrapper around production MCP.

---

## 17. Risk register

| Risk | Mitigation |
|---|---|
| Hallucinated facts | Fact-pack allowlist + post-validate numbers/sources |
| Tick timeout | Soft deadline; return partial/empty actions; classify without LLM when possible |
| Prompt drift vs case studies | Keep `examples/case-studies.md` as eval set; similarity check awareness (don't copy) |
| Version ignore | Always read latest version from store at compose time |
| Spam / over-send | Urgency rank + suppression + empty actions OK |
| Auto-reply burn | Streak FSM (wait → end) |
| Intent loop | Explicit commit detector → action mode |
| Language mismatch | Prefer customer `language_pref` / merchant `languages` in prompt + validator |

---

## 18. Success criteria

The architecture is "done" when:

1. Warmup reports `{5, 50, 200, 0}` (triggers arrive later)
2. Research-digest and recall paths match case-study scoring shape (≥45/50 locally)
3. Auto-reply / intent / hostile scenarios end correctly without operational penalties
4. Mid-test category/merchant version bumps appear in subsequent compositions
5. `submission.jsonl` covers all 30 `test_pairs.json` entries deterministically
6. Public URL survives a full judge window within rate/timeout limits

---

## End of architecture.md

Companion docs:
- Product + rubric: `Context.md`
- HTTP examples: `examples/api-call-examples.md`
- Quality anchors: `examples/case-studies.md`
- Data generation: `dataset/generate_dataset.py`

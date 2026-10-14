# Project Context — magicpin Merchant AI Assistant ("Vera")

**Purpose**: Single loadable context for any fresh AI/human session working on this repo.
**Sources consolidated**:
- `problemStatement.md` — challenge brief (product, 4-context framework, rubric)
- `challenge-testing-brief.md` — HTTP/judge harness contract
- `engagement-design.md` — Vera engagement framework design proposal
- `engagement-research.md` — how production Vera loads merchant/customer data today
**Last consolidated**: 2026-10-13
**Audience**: Builders of the candidate bot + anyone designing, judging, or debugging Vera engagement.

> This file is self-contained. A cold start should understand the company, product, production data paths, 4-context design, composition contract, HTTP API, dataset, evaluation, rollout plan, and what this repo already contains.

---

## 0. Repo snapshot (this workspace)

| Path | Role |
|---|---|
| `problemStatement.md` | Product + composition challenge brief (`challenge-brief.md` equivalent) |
| `challenge-testing-brief.md` | Judge harness HTTP contract + lifecycle |
| `engagement-design.md` | Internal Vera 4-context design proposal (not yet implemented in production) |
| `engagement-research.md` | Research notes: how production Vera loads merchant + customer data |
| `Context.md` | This consolidated context |
| `judge_simulator.py` | Local LLM-powered mini-harness against `BOT_URL` |
| `dataset/` | Category JSONs + seed files + `generate_dataset.py` |
| `examples/` | API call examples + case studies |

**Goal of this project**: Build a stateful HTTP bot that engages merchants (and optionally their customers) on WhatsApp the way **Vera** does — but better — then survive the judge harness. The design/research docs explain *why* the 4-context model exists and what production already provides vs. what is greenfield.

---

## 1. The challenge in one sentence

> Build an AI chatbot that engages and assists merchants on WhatsApp the way **Vera** (magicpin's merchant-AI assistant) does — but better. Same base dataset for every participant. AI judges the outcome.

---

## 2. About magicpin (~30 sec)

magicpin is one of India's largest local-commerce platforms — ~100,000 merchant partners across 50+ Indian cities (restaurants, salons, gyms, dentists, retailers, car dealers, etc.). Customers discover merchants on the magicpin app/web, transact, and earn cashback. Merchants get visibility, walk-ins, and online orders.

**Vera** talks to merchants over WhatsApp, helps grow Google Business Profile (GBP), runs campaigns, and answers customer questions on their behalf. **Vera is the product participants rebuild.**

---

## 3. About Vera (product you're rebuilding)

### What Vera does today
- Talks to ~6,000–10,000 merchants/day over WhatsApp
- Improves GBP (photos, hours, posts, reviews)
- Runs marketing campaigns (festival, news, local events)
- Recommends pricing, offers, content
- Answers customers' questions about merchants on their behalf

### Live engagement shape (Apr 23–25, 2026)

| Metric | Apr 23 | Apr 24 | Apr 25 |
|---|---:|---:|---:|
| Merchants who engaged with Vera | 6,917 | 10,158 | 5,181 |
| Total messages mx ↔ Vera | 34,022 | 47,651 | 23,712 |
| Avg messages per engaged merchant | 4.9 | 4.7 | 4.6 |
| Customers who engaged with Vera | 720 | 707 | 681 |
| Unique merchants customers asked about | 580 | 514 | 466 |
| Total messages cx ↔ Vera | 3,713 | 4,839 | 4,695 |
| Avg messages per customer | 5.2 | 6.8 | 6.9 |

### Biggest pain points (opportunities to beat Vera)

1. **Auto-reply pollution** — 40–70% of "merchant replies" are WA Business canned auto-replies. Production detects them but burns 2–3 turns. Better detection + faster routing wins.
2. **Intent-handoff failures** — "I want to join" often loops back to qualifying. Better intent detection wins.
3. **Generic copy** — "10% off" underperforms; service+price ("Haircut @ ₹99", "Dental Cleaning @ ₹299") wins.
4. **Low engagement frequency** — Functional nudges (renewal due, profile incomplete) are inherently rare. 3–5×/week engagement needs curiosity-driven and knowledge-driven conversations, not just reminders.

---

## 4. Why the engagement framework exists (design rationale)

Production engagement (`agents/vera/followup/`) is a collection of ad-hoc nudges — campaign templates, performance reminders, conversation requeues — each built point-to-point with hardcoded assumptions. Adding a new nudge type means re-writing prompts, finding new data, and re-implementing send/dedup logic.

Two problems this creates:

1. **Functional nudges are inherently low-frequency.** A merchant only has a handful of "broken things" or "events" per month. To engage 3–5×/week needs curiosity-driven, knowledge-driven, and customer-driven conversations — not just "fix-this" reminders.
2. **Same engine should drive merchant-facing AND customer-facing messages.** When Dr. Meera's clinic sends a recall to patient Priya, Vera does the work — but composition should use the same framework that produces the research digest Vera sends to Dr. Meera.

The proposed solution is a **4-context composition framework** that separates slow-changing (category knowledge) from fast-changing (per-merchant, per-customer state) and event-driven (triggers).

---

## 5. The 4-context framework

Every message = `compose(category, merchant, trigger, customer?)`.

| Context | Question it answers | Refresh cadence | Owner | Shared across |
|---|---|---|---|---|
| **Category** | How do we talk to *this type* of business? What do they know, care about, offer, get regulated on? | Weekly (digest), monthly (voice/catalog) | Domain curator | All merchants in the vertical |
| **Merchant** | Who is this specific business, how are they doing, what's in their history with us? | Daily (perf), real-time (conversation) | Snapshot + conversation sync | Just this merchant |
| **Trigger** | Why am I messaging *right now*? | Per-event | Event detectors | This one send |
| **Customer** | Who is the merchant's customer, and what's their state with this merchant? | Per-visit / per-interaction | Merchant CRM sync | Just this customer |

```
                  ┌─────────────────┐
   Category   ───►│                 │
   Merchant   ───►│  Composer (LLM) │───► message {body, params, cta, send_as}
   Trigger    ───►│                 │
   Customer?  ───►│                 │
                  └─────────────────┘
```

Nothing is hardcoded into the composer — all variation comes from the contexts.

### 5.1 CategoryContext

Slow-changing knowledge pack per vertical. Bootstrap is labor-intensive; ongoing maintenance is mostly the weekly digest.

```python
@dataclass
class CategoryContext:
    slug: str                          # "dentists", "salons", "restaurants", ...
    offer_catalog: list[OfferTemplate] # prefer "Dental Cleaning @ ₹299" over "Flat 20% OFF"
    voice: VoiceProfile                # tone, vocab, taboos
    peer_stats: PeerStats              # city-scoped avg rating/reviews/CTR
    digest: list[DigestItem]           # weekly research/compliance, source-cited
    patient_content_library: list[ContentItem]  # merchant can reshare with customers
    seasonal_beats: list[SeasonalBeat]
    trend_signals: list[TrendSignal]
```

**Dentists example**:
- voice: technical terms welcome ("fluoride varnish at 3-month recall"); taboos ("cure", "guaranteed"); peer tone not hype
- offer_catalog: `["Dental Cleaning @ ₹299", "Free Consultation", "Teeth Whitening @ ₹1,499"]`
- peer_stats: `{avg_rating: 4.4, avg_reviews: 62, avg_ctr: 0.030}` (South Delhi solo practices)
- digest sources: PubMed dental RSS, JIDA, IDA Delhi calendar, DCI circulars, Dental Tribune India, Google Trends, vendor press
- seasonal_beats: exam-stress bruxism Nov–Feb; wedding whitening peak Oct–Dec
- trend_signals: e.g. "clear aligners Delhi" searches +62% YoY

### 5.2 MerchantContext

```python
@dataclass
class MerchantContext:
    merchant_id: str
    identity: Identity                # name, place_id, locality, city, verified, languages
    subscription: Subscription        # status, days_remaining, plan
    performance: PerformanceSnapshot  # views/calls/CTR/leads/directions, 30d + 7d deltas
    offers: list[MerchantOffer]       # active + paused from catalog
    conversation_history: ConversationHistory  # last N turns + engagement tags
    customer_aggregate: CustomerAggregate  # active/lapsed counts, retention %
    signals: list[DerivedSignal]      # stale_posts, ctr_below_peer, dormant, ...
```

**Running example — Dr. Meera's Dental Clinic**:
- identity: Lajpat Nagar, Delhi; verified
- subscription: active, Pro, 82 days remaining
- performance (30d): views=2410, calls=18, directions=45, ctr=0.021
- offers: `Dental Cleaning @ ₹299` active; `Deep Cleaning @ ₹499` expired 2mo ago
- customer_aggregate: 540 unique YTD, 78 lapsed >180d, 38% 6mo retention
- signals: `stale_posts` (22d), `ctr_below_peer_median` (peer 0.030)

### 5.3 TriggerContext

Every message must have one. Two families:

**External** (outside the merchant's account):
- `festival_upcoming`, `weather_heatwave`, `local_news_event`
- `category_research_digest_release`, `regulation_change`
- `competitor_opened`, `category_trend_movement`

**Internal** (within merchant data / customer roster):
- `perf_spike`, `perf_dip`, `milestone_reached`, `dormant_with_vera`
- `customer_lapsed_soft`, `appointment_tomorrow`, `review_theme_emerged`
- `scheduled_recurring` / `curious_ask_due`

```python
@dataclass
class TriggerContext:
    id: str
    scope: Literal["merchant", "customer"]
    kind: str
    source: Literal["external", "internal"]
    payload: dict
    urgency: int             # 1-5
    suppression_key: str     # Redis dedup
    expires_at: datetime
```

**Example** — research digest for dentists:
```json
{
  "id": "trg_2026_04_26_research_digest_dentists",
  "scope": "merchant",
  "kind": "research_digest",
  "source": "external",
  "payload": {
    "category": "dentists",
    "top_item": {
      "title": "3-mo fluoride recall cuts caries recurrence 38% better than 6-mo",
      "source": "JIDA Oct 2026, p.14",
      "trial_n": 2100,
      "patient_segment": "high-risk adults"
    }
  },
  "urgency": 2,
  "suppression_key": "research:dentists:2026-W17",
  "expires_at": "2026-05-03T00:00:00Z"
}
```

### 5.4 CustomerContext (optional — customer-facing only)

```python
@dataclass
class CustomerContext:
    customer_id: str
    merchant_id: str
    identity: CustomerIdentity  # name, phone, language preference
    relationship: Relationship  # first/last visit, visits_total, services, LTV
    state: Literal["new", "active", "lapsed_soft", "lapsed_hard", "churned"]
    preferences: Preferences    # preferred slots, channel, opt-in
    consent: Consent            # when/how opted in, scope
```

**Example — Priya for Dr. Meera**: hi-en mix; last visit ~5mo ago; `lapsed_soft`; weekday evenings; consent for recall/appointment reminders.

---

## 6. Composer

Single LLM-prompted module. Takes the 4 contexts; produces:

- `body` — WhatsApp message body
- `cta` — binary YES/STOP, open-ended, or none
- `send_as` — `"vera"` (merchant-facing) or `"merchant_on_behalf"` (customer-facing)
- `suppression_key` — for dedup
- `rationale` — why this message, what it should achieve
- `template_params` — for first-touch Kaleyra/Meta templates (challenge: any sensible `{{1}}/{{2}}` structure; no real Meta calls)

Must be **versioned** (`composer_v1`, …), A/B-testable, and auditable (replay any past message with all 4 input contexts). Dispatch by `trigger.kind` — e.g. research-digest needs source-citation framing; recall needs slot-offering framing; competitor-opened needs curiosity framing.

### Challenge composition signature

```python
def compose(
    category: CategoryContext,
    merchant: MerchantContext,
    trigger: TriggerContext,
    customer: Optional[CustomerContext] = None
) -> ComposedMessage:
    ...
```

### Constraints
1. **WhatsApp 24h window** — first outbound uses a pre-approved template; free-form after merchant reply within 24h.
2. **Body** — concise, readable; no hard cap.
3. **Single primary CTA** — binary for actions; none OK for pure info.
4. **URLs** — OK when they add clear value.
5. **Specificity** — anchor on verifiable facts from contexts.
6. **Voice match** — peer/colleague, not promo hype.
7. **Hindi–English code-mix** OK; match merchant language.
8. **Don't fabricate** — no fake offers, citations, competitors.

### Compulsion levers (use ≥1 per message)
1. Specificity / verifiability
2. Loss aversion
3. Social proof *(Vera underuses)*
4. Effort externalization
5. Curiosity
6. Reciprocity
7. Asking the merchant *(Vera underuses)*
8. Single binary commitment

### Anti-patterns (penalized)
- Generic % discounts when service+price exists
- Multiple CTAs; buried CTA
- Promotional tone for clinical categories
- Hallucinated data
- Long preambles; re-introducing after first message
- Ignoring language preference
- Exact-repeat messages in-conversation

### Open challenges (extra credit)
1. Detect auto-replies (same verbatim 3+ times) vs real replies
2. Intent transitions → action mode immediately
3. Multi-turn cadence inside 24h window
4. Per-turn language detection
5. Know when to stop (not-interested / 3 unanswered nudges)

---

## 7. Worked composition examples

### 7.1 Merchant-facing (research digest → Dr. Meera)

| Context | Key values used |
|---|---|
| Category | voice=peer/clinical; digest top=JIDA 3-mo fluoride recall 38% better; peer CTR median 3.0% |
| Merchant | CTR 2.1%; high-risk adult cohort; last Vera touch 2d ago (engaged) |
| Trigger | `research_digest_release`, urgency 2, external |
| Customer | none |

**Good message**:
```
Dr. Meera, JIDA's Oct issue landed. One item relevant to your high-risk adult
patients — 2,100-patient trial showed 3-month fluoride recall cuts caries
recurrence 38% better than 6-month. Worth a look (2-min abstract). Want me to
pull it + draft a patient-ed WhatsApp you can share?  — JIDA Oct 2026 p.14
```

Scores well on specificity, category fit, merchant fit, trigger relevance, compulsion (curiosity + reciprocity + low-friction CTA).

### 7.2 Customer-facing (recall → Priya)

| Context | Key values used |
|---|---|
| Category | warm-clinical; no medical claims / "guaranteed" |
| Merchant | active `Dental Cleaning @ ₹299`; slots Wed 6pm + Thu 5pm |
| Trigger | `recall_due`, scope=customer, urgency 3 |
| Customer | Priya, lapsed_soft, weekday evening, hi-en mix |

**Good message** (`send_as = merchant_on_behalf`):
```
Hi Priya, Dr. Meera's clinic here 🦷 It's been 5 months since your last visit —
your 6-month cleaning recall is due. Apke liye 2 slots ready hain: Wed 6 Nov,
6pm ya Thu 7 Nov, 5pm. ₹299 cleaning + complimentary fluoride. Reply 1 for
Wed, 2 for Thu, or tell us a time that works.
```

Same composer. Different context inputs. Two completely different conversations.

---

## 8. Engagement loops the framework enables

Once the framework exists, every loop is a small cron that emits `TriggerContext`. The composer handles the rest.

| Loop | Emits trigger kinds | Scope |
|---|---|---|
| News/weather scanner *(exists — `agents/vera/followup/event_sources.py`)* | festival, heatwave, fuel, IPL, monsoon, news | merchant |
| Weekly research digest per category | `research_digest_release` | merchant |
| Performance monitor | `perf_spike`, `perf_dip`, `milestone_reached` | merchant |
| Review-pattern detector | `review_theme_emerged` | merchant |
| Conversation curiosity-ask scheduler | `curious_ask_due` | merchant |
| Recall scheduler (merchant CRM) | `recall_due` | customer |
| Lapse detector | `customer_lapsed_soft`, `customer_lapsed_hard` | customer |
| Appointment reminder | `appointment_tomorrow` | customer |
| Capacity optimizer | `unplanned_slot_open` | customer |

Adding a loop = define one new `kind`, implement the detector, add a composer prompt variant. No change to merchant/category/customer code.

---

## 9. Production research — how Vera loads data today

Two distinct paths share infrastructure (vera-mcp + merchant-support-mcp + Redis) but compose context differently.

### 9.1 Path 1 — Merchant-facing (`VeraMerchantAgent`)

**Init** (`agents/vera/merchant_agent.py:402`): Spawns `vera_mcp_client` → `VERA_MCP_SERVER_URL` (default `vera-mcp:8000`); inherits shared `BaseAgent._merchant_mcp_client` → merchant-support-mcp. **No merchant data loaded at init.**

**Per-turn** (`handle_input` ~:2171):
1. Extract `merchant_id` from metadata (fallback: regex `\d{7,}` on message).
2. Parallel: `_detect_state` (GBP + subscription) + `_prefetch_merchant_context`.

**`_prefetch_merchant_context` (~:740)** — cache-first:
1. Redis `vera:merchant_ctx:{merchant_id}` — TTL **30 min**. Hit → return.
2. Parallel: `vera_merchant_snapshot` + `vera_get_merchant_profile` (vera-mcp).
3. Empty snapshot → fallback `get_aggregated_unassociated_merchant_data` (merchant-support-mcp).
4. Sequential enrich: `_prefetch_product_context` (subscription, performance summary, DA campaign if subscribed) + `_enrich_snapshot_with_pricing` (HTTP to vera pricing API).
5. Write Redis TTL 30 min → populate `_merchant_snapshot` + `_behavioral_profile`. System prompt serializes snapshot into the LLM prompt.

**`vera_merchant_snapshot` fan-out** (up to 13 parallel tools):
- Merchant-level: subscription, pricing, pain points, offers, config, onboarding, enhancement suggestions
- Location-level (needs place_id): GBP location, completeness, performance, search keywords, review stats, posts
- Composes sections: `identity`, `profile`, `reputation`, `growth`, `commercial`, `conversation_hooks`, `issues`
- Note: `category` and `locality` are **not** first-class on the snapshot — buried in `profile.business_info` / aryan `get_merchant_v2` via customer-info-pack

**Mid-turn**: LLM calls tools via vera-mcp / merchant-support-mcp. No re-prefetch of snapshot mid-turn.

### 9.2 Path 2 — Customer-facing (`CustomerIncomingAgent`)

Different agent (`customer_incoming_agent.py`). Instance holds `_merchant_id`, `_merchant_data`, `_category`, `_offers`, `_customer_phone`, `_customer_profile`, chat history.

**`_load_merchant_data` (~:221)** — no Redis cache:
1. Primary: `vera_get_customer_info_pack(merchant_id)` → business_info + reviews + photos + offers + metadata
2. Fallback: `get_unassociated_merchant_data` + `vera_list_merchant_offers`
3. Supplementary: `vera_get_merchant_jd_info` (JustDial)

**`vera_get_customer_info_pack`**: resolve place_id (MongoDB gbp_status → local JSON → aryan mapping) → parallel GBP fetch (24h Mongo cache) + active offers + aryan metadata (`name`, `category`, `locality`).

**Customer profile**: from past conversation tickets keyed by phone — mostly continuity (last visit/topic). No rich CRM; visit history aggregation does not exist.

### 9.3 Cross-cutting infrastructure

| Concern | Implementation |
|---|---|
| MCP transport | `HTTPMCPClient` → `/mcp/tools/{name}` HTTP POST |
| Merchant context cache | Redis `vera:merchant_ctx:{merchant_id}`, TTL 30 min |
| GBP cache | MongoDB `gbp_health_report:{place_id}`, TTL 24h |
| Source of truth for `category` | aryan `get_merchant_v2` (synchronous bottleneck) |
| Source of truth for `name` | aryan first, GBP `business_info` second |

### 9.4 What already exists vs. greenfield

**Already exists (adapter-friendly)**:
1. Most of `MerchantContext` — scattered across `_merchant_snapshot`, `_behavioral_profile`, `_session_scenario`, `_jd_info` (~80% without new fetching)
2. Half of `CustomerContext` — phone + conversation continuity; missing visit history, services, lapse state
3. Two MCP servers already wired — composer can consume collected context; no new MCP needed
4. 30-min Redis TTL fine for in-conversation reuse

**Does NOT exist (greenfield)**:
1. **`CategoryContext`** — category is a string in metadata; no voice/peer/digest packs. Biggest leveraged greenfield.
2. **`customer_aggregate`** on merchant snapshot — no per-merchant roster stats pipeline
3. **`TriggerContext` abstraction** — every nudge has its own cron + payload + send code. Genuinely new architectural primitive.
4. **Visit-history aggregation** per (merchant, customer_phone) — BOTOPS has raw chat data; no derived view
5. **Shared `EngagementComposer`** — each agent has its own prompt builder

### 9.5 Operational risks
1. **Aryan is the sync bottleneck** for category/locality — cache aryan responses ~24h before scaling engagement frequency.
2. **Daily engagement cron will miss the 30-min Redis cache** 100% of the time — consider longer-TTL background-warmed cache for the engagement loop.
3. **No prompt-version provenance today** — composer should record prompt version + context hash on every send for replay/A/B.

### 9.6 Key production file pointers

- `agents/vera/merchant_agent.py:402` — VeraMerchantAgent init
- `agents/vera/merchant_agent.py:740` — `_prefetch_merchant_context`
- `agents/vera/merchant_agent.py:899` — `_prefetch_product_context`
- `agents/vera/merchant_agent.py:996` — system-prompt builder
- `agents/vera/merchant_agent.py:2171` — `handle_input`
- `agents/vera/customer_incoming_agent.py:91` / `:221` — customer agent + `_load_merchant_data`
- `agents/base_agent.py:80-82`, `:237-244` — merchant-support-mcp config / shared client
- `vera-mcp/src/services/merchant_snapshot.py:51` — `build_merchant_snapshot` (13-call fan-out)
- `vera-mcp/src/tools/merchant_info.py:188` — `vera_get_customer_info_pack`
- `vera-mcp/src/services/aryan_client.py` — aryan HTTP client
- `agents/vera/followup/event_sources.py` / `event_extractor.py` — external triggers already shaped like TriggerContext
- `agents/vera/followup/template_registry.py` — Kaleyra template names
- `agents/vera/followup/snapshot_data.py` — most MerchantContext fields
- `services/vera-mcp/src/services/offer_suggester.py` — candidate for CategoryContext.offer_catalog

---

## 10. Implementation shape (production design)

```python
# agents/vera/engagement/contexts.py  — 4 dataclasses (see §5)

# agents/vera/engagement/composer.py
class EngagementComposer:
    def compose(self,
                category: CategoryContext,
                merchant: MerchantContext,
                trigger: TriggerContext,
                customer: CustomerContext | None = None) -> ComposedMessage:
        ...
```

Both surfaces (merchant-facing, customer-on-behalf) call the same composer. Only difference: whether `customer` is populated.

### Phased rollout

**Phase 1 — skeleton + dentistry (~2 weeks)** — mostly an adapter layer, not new infrastructure:
1. Define 4 dataclasses
2. Build `CategoryContext` for dentistry (catalog, voice, peer stats, weekly digest, patient-content seed)
3. `MerchantContext` loader from existing snapshot (+ new `_customer_aggregate` from BOTOPS)
4. First `EngagementComposer` for `research_digest_release` + one perf trigger
5. Render (no send) Dr. Meera research-digest end-to-end

Phase 1 should **not** modify existing agents — adapter reads existing state; composer runs in parallel; new triggers are new crons.

**Phase 2 — customer-on-behalf (~2 weeks)**:
6. Resolve customer-data source-of-truth (clinic SaaS / CSV upload / BOTOPS-derived)
7. Consent model: opted in via merchant, not Vera directly
8. Send-as-merchant channel (WA Business under merchant number, or shared number with attribution)
9. Ship first customer trigger: `recall_due`

**Phase 3 — multiply verticals (~1 week each)**:
10. CategoryContext for salons, gyms, pharmacies, restaurants, car service
11. More triggers: `perf_dip`, `milestone_reached`, `review_theme_emerged`; customer: `customer_lapsed_soft`, `appointment_tomorrow`, `unplanned_slot_open`

### Open questions (block Phase 2)
1. Where does the merchant's customer list live?
2. Consent: auto-send with merchant override vs. approve-every-send?
3. Attribution: "Dr. Meera's clinic" vs "Vera on behalf of…"? (likely category-dependent)
4. Composer prompt versioning from day 1
5. Offer source-of-truth (aryan catalogoffer / merchant-portal-api / magicpin_jobs?)
6. Model choice: Azure OpenAI primary + Deepseek fallback vs smaller model for high-volume customer sends?

### Why it's worth building
- Engagement frequency: few×/month → few×/week (curiosity + knowledge + customer loops)
- One framework, two products (Vera↔merchant and merchant↔customer)
- Vertical scaling becomes data work, not code work
- Auditable + versioned: answer "why did Vera send this?" for any past send

---

## 11. Base dataset (challenge — shared by all participants)

```
dataset/
├── categories/     # 5 CategoryContexts (dentists, salons, restaurants, gyms, pharmacies)
├── merchants/      # 50 MerchantContexts (10 per category)
├── customers/      # 200 customer profiles
└── triggers/       # 100 sample triggers
```

In this repo today: populated `dataset/categories/*.json`, seed JSONs (`merchants_seed.json`, `customers_seed.json`, `triggers_seed.json`), and `generate_dataset.py`. Full merchant/customer/trigger trees may need generation via the script.

Canonical submission comparison: **30 specific (merchant, trigger) pairs** for like-for-like judging.

**Ethics**: Synthetic/realistic data, no real PII. Do not scrape magicpin/Google or impersonate magicpin externally. Challenge-only output.

---

## 12. What participants submit

| Artifact | Required | Notes |
|---|---|---|
| HTTP bot at public URL | Yes (testing brief) | 5 endpoints under `/v1/*` |
| `bot.py` compose module | Yes (problem brief) | Deterministic (temp=0), <30s/call |
| `submission.jsonl` | Yes | 30 lines for test pairs |
| `README.md` | Yes | ≤1 page: approach, tradeoffs |
| `conversation_handlers.py` | Optional | Multi-turn `respond()` — tiebreaker |

Core `compose` return keys: `body`, `cta`, `send_as`, `suppression_key`, `rationale`.

---

## 13. Evaluation rubric (5 dimensions × 0–10 = 50)

| Dimension | Judge looks for |
|---|---|
| **Specificity** | Concrete verifiable fact from contexts; penalize generic sales talk |
| **Category fit** | Voice, vocab, offer format match vertical |
| **Merchant fit** | Personalized to this merchant's state + language |
| **Trigger relevance** | Clear *why now* |
| **Engagement compulsion** | Would a real merchant reply? |

### Post-submission context injection
Judge adds unseen digest items, updated performance, new triggers, and for 5/30 pairs a `CustomerContext`. Adaptation without hallucination/off-voice scores higher.

### Replay test (top 10)
Judge plays merchant for 3–5 turns: auto-reply, engaged, hard no, curveballs. Scores flow quality.

---

## 14. Testing model — HTTP judge harness

```
magicpin Judge Harness  ←──HTTP/JSON──►  Candidate Bot (stateful, public URL)
```

1. **Judge → Bot**: incremental pushes across all 4 context scopes.
2. **Bot → Judge**: bot initiates conversations; judge plays merchant/customer.

Bot is **stateful**. Judge is source of truth for what happened.

### Endpoints (5)

#### `POST /v1/context` — context push
```json
{
  "scope": "category" | "merchant" | "customer" | "trigger",
  "context_id": "...",
  "version": 3,
  "payload": { },
  "delivered_at": "2026-04-26T10:00:00Z"
}
```
- Idempotent on `(context_id, version)`; higher version replaces; 409 on stale; persist until test ends.

#### `POST /v1/tick` — wake-up; bot may initiate
```json
{ "now": "2026-04-26T10:30:00Z", "available_triggers": ["trg_..."] }
```
Response: `{ "actions": [ { conversation_id, merchant_id, customer_id, send_as, trigger_id, template_*, body, cta, suppression_key, rationale } ] }`  
Empty `actions` OK. New `conversation_id` only here; continue via `/v1/reply`. Cap: 20 actions/tick.

#### `POST /v1/reply` — merchant/customer reply
Bot returns one of:
- `{ "action": "send", "body", "cta", "rationale" }`
- `{ "action": "wait", "wait_seconds", "rationale" }`
- `{ "action": "end", "rationale" }`  
Timeout: **30s**.

#### `GET /v1/healthz` — liveness  
Returns status + `contexts_loaded` counts. 3 consecutive failures → disqualified for slot.

#### `GET /v1/metadata` — team/model/approach identity

Optional: `POST /v1/teardown` to wipe state after test.

### Context payload shapes (HTTP)
Mirror §5 dataclasses. Notable HTTP fields:
- Merchant includes `category_slug`
- Trigger includes `merchant_id` / `customer_id` at top level
- Category digest items have `id`, `kind`, `source`, etc.

### Harness lifecycle

| Phase | What happens |
|---|---|
| **1 Warmup** | healthz + metadata; push 5+50+200 contexts (0 triggers); settle 60s; expect 255 loaded |
| **2 Test window** | 60 simulated minutes; 5-min ticks; context updates → tick → actions → multi-turn reply (≤5) |
| **3 Adaptive injection** | New digests (v+), perf updates, 15 new triggers, 5 mid-test customers + recall triggers |
| **4 Replay** | Top 10: auto-reply hell, intent transition, hostile/off-topic (5 turns each) |
| **5 Score** | Rubric + adaptation bonus (+5/dim) + replay (+30) − operational penalties (max −20) |

### Rate limits / ops

| Limit | Value |
|---|---|
| Max RPS judge → bot | 10 |
| Per-call timeout | 30 s |
| Context payload cap | 500 KB |
| Actions per tick | ≤20 |
| Healthz fail DQ | 3 consecutive |
| Test window | 60 sim min (~30–45 real) |

Deploy anywhere with a public URL (`https://host/v1/*` or http for local). Submit URL via portal.

### Failure penalties
- healthz offline: −10
- tick/reply timeout: −1 each
- malformed / empty body: −2
- verbatim repeat in conversation: −2

### Privacy
- Synthetic data only
- May call commercial LLM APIs for composition
- Must **not** send merchant/customer payloads to non-LLM external APIs
- Wipe state after test

### Local self-test
```bash
export BOT_URL=http://localhost:8080
python judge_simulator.py
```

### Pre-flight checklist
- [ ] Public reachable URL
- [ ] All 5 endpoints + correct schemas
- [ ] Context idempotency / versioning
- [ ] tick/reply ≤30s (`actions: []` if nothing to send)
- [ ] Stateful persistence across calls
- [ ] `judge_simulator.py` passes with non-zero scores
- [ ] LLM quota for full 60-min window

### Scoring artifacts
```
results/<team_name>/
├── conversations.jsonl
├── context_pushes.jsonl
├── scoring.json
├── timeline.html
├── replay_*.jsonl          # top 10
└── final_report.md
```
Teams get their bundle within ~48h.

---

## 15. Reference patterns (from production Vera)

**Gold standard**: Hindi–English mix, specific numbers, Vera does work + reports back, honest about uncertainty (e.g. GBP unverified, 24–48h Google lag).

**Auto-reply**: Try once after detecting canned reply, then graceful exit — don't burn turns.

**Strong hook**: Verifiable local number + loss framing ("6,777 missed searches in Sector 14").

**Don't**: After clear "I want to join", ask another qualification question — route to action.

---

## 16. Suggested challenge architecture (non-binding)

1. Prompt template over 4 structured contexts → frontier LLM
2. Routing by trigger kind (digest vs recall vs perf-dip)
3. Post-LLM validation (CTA shape, language); re-prompt on fail
4. Multi-turn state: said / signaled / next move
5. Optional retrieval over digest items; internal tools OK

HTTP skeleton (FastAPI) is in `challenge-testing-brief.md` §7 — in-memory `contexts` + `conversations`, stub composer on tick/reply. Run: `uvicorn bot:app --host 0.0.0.0 --port 8080`.

---

## 17. FAQ (condensed)

- Internal tool/function calling: yes; no outbound merchant/customer data to non-LLM APIs.
- Slow composition: speed up or return empty actions for that tick — late responses dropped.
- Multiple messages same merchant per tick: one action per `(merchant_id, conversation_id)` per tick.
- `rationale` is scored/used by judge — write it well.
- Language: match `identity.languages` / prefs; hi-en encouraged when appropriate.
- Empty tick actions rewarded vs spam.
- New mid-test merchant contexts: treat as normal.
- No clarification channel mid-test.

---

## 18. What a judge / fresh session needs

1. This context (or the four source docs)
2. Base dataset
3. Post-submission injections (for judging)
4. Submitted bot artifacts / live URL
5. Rubric + replay instructions

No prior chat history required.

---

## End of Context.md

Primary sources remain authoritative if anything drifts:
- Product/composition: `problemStatement.md`
- HTTP/judge: `challenge-testing-brief.md`
- Production design: `engagement-design.md`
- Production data paths: `engagement-research.md`

Build something better than today's Vera.

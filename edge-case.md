# Edge Cases & Corner Scenarios — Challenge Bot

**Status**: Test / hardening catalog  
**Sources**: `implementation-plan.md`, `architecture.md`, `Context.md`, `examples/`  
**Last updated**: 2026-10-13  
**Audience**: Engineers implementing Phases A–E; use as a checklist before each phase exit gate

> Every row is a scenario the judge (or real merchants) can hit. **Expected behavior** is the pass criteria. **Phase** is when it must be handled. IDs are stable for tracking (`EC-A-01`, …).

---

## How to use

| Column | Meaning |
|---|---|
| **ID** | Stable edge-case id |
| **Scenario** | What happens |
| **Expected** | Correct bot behavior |
| **Anti-pattern** | What loses points / DQ |
| **Phase** | A–E from implementation plan |
| **Priority** | P0 = must for exit gate; P1 = high; P2 = nice |

Mark `[x]` in the Status column as you cover each case in tests.

---

## 1. Context store & HTTP contract (Phase A)

| Status | ID | Scenario | Expected | Anti-pattern | Phase | Pri |
|---|---|---|---|---|---|---|
| [ ] | EC-A-01 | Warmup before any context push | `healthz.contexts_loaded` all zeros | Fake non-zero counts | A | P0 |
| [ ] | EC-A-02 | Push same `(context_id, version)` twice | Idempotent no-op or **409** `stale_version` with `current_version` | Double-count in healthz; crash | A | P0 |
| [ ] | EC-A-03 | Push lower version after higher | **409** stale; keep higher payload | Downgrade / corrupt store | A | P0 |
| [ ] | EC-A-04 | Push higher version mid-test | Atomic replace; compose uses new payload | Keep serving v1 facts | A/E | P0 |
| [ ] | EC-A-05 | Unknown `scope` value | **400** `invalid_scope` | 500 / silent accept | A | P1 |
| [ ] | EC-A-06 | Malformed JSON / missing fields on `/v1/context` | **400** with reason | 500 stack trace | A | P1 |
| [ ] | EC-A-07 | Payload ~500 KB (cap) | Accept if under cap; reject gracefully if over | Hang / OOM | A/E | P2 |
| [ ] | EC-A-08 | Warmup expects 5+50+200, triggers=0 | Healthz matches exactly after settle | Off-by-one counts | A | P0 |
| [ ] | EC-A-09 | Trigger arrives only in test window | Store trigger; healthz trigger count updates | Assume triggers at warmup | A | P0 |
| [ ] | EC-A-10 | Process restart mid-test | **Must not happen**; if it does, state lost → DQ | Rely on disk without plan | A/E | P0 |
| [ ] | EC-A-11 | `GET /v1/metadata` missing fields | Always return full identity schema | Empty / partial JSON | A | P1 |
| [ ] | EC-A-12 | Healthz slow or non-200 ×3 | Avoid; keep healthz trivial & fast | Heavy work in healthz | A/E | P0 |
| [ ] | EC-A-13 | Teardown called | Wipe contexts + conversations | Leak state to next run | E | P1 |
| [ ] | EC-A-14 | UTF-8 Hindi / emoji in payloads | Store & round-trip intact | Mojibake / reject | A | P1 |

---

## 2. Tick selection & suppression (Phases A/C)

| Status | ID | Scenario | Expected | Anti-pattern | Phase | Pri |
|---|---|---|---|---|---|---|
| [ ] | EC-T-01 | `available_triggers: []` | `{actions: []}` quickly | Invent triggers | A/C | P0 |
| [ ] | EC-T-02 | Trigger id in hint but not in store | Skip silently | 500 / hallucinate payload | A/C | P0 |
| [ ] | EC-T-03 | Trigger past `expires_at` | Skip | Send stale festival/IPL | C | P0 |
| [ ] | EC-T-04 | Same `suppression_key` already used | Do not re-send | Spam same research week | C | P0 |
| [ ] | EC-T-05 | Merchant has open conv in `wait`/`end` | Skip new proactive for that merchant (or respect wait) | Parallel nag threads | C/D | P1 |
| [ ] | EC-T-06 | Merchant opted out / suppressed | No new actions for that merchant | Keep pitching | D | P0 |
| [ ] | EC-T-07 | >20 candidate triggers | Cap ≤20 actions; prefer quality | Blast all | C | P0 |
| [ ] | EC-T-08 | Many low-urgency curiosities + one urgency=5 | Prefer high urgency (e.g. supply_alert) | Send curious_ask first | C | P1 |
| [ ] | EC-T-09 | Two triggers same merchant same tick | At most one action per `(merchant_id, conversation_id)`; preferably one convo | Dual simultaneous pitches | C | P0 |
| [ ] | EC-T-10 | Reuse `conversation_id` on tick | Invalid — only create new ids on tick | Continue via tick instead of reply | A/C | P0 |
| [ ] | EC-T-11 | Nothing worth saying | `{actions: []}` — restraint rewarded | Generic “hope you're well” spam | C | P0 |
| [ ] | EC-T-12 | Compose near 30s budget | Return partial/empty before timeout | Hang → −1 timeout | C/E | P0 |
| [ ] | EC-T-13 | Merchant missing `category_slug` / category not loaded | Skip action | Fabricate category voice | B/C | P0 |
| [ ] | EC-T-14 | Customer-scoped trigger but customer not loaded | Skip (or wait until push) | Invent Priya-like profile | B/C | P0 |
| [ ] | EC-T-15 | Generated trigger with `payload.placeholder: true` | Compose carefully from merchant+category only; no fake payload facts | Invent batch numbers / slots | C | P1 |
| [ ] | EC-T-16 | Dormant merchant + low-urgency curious_ask | Down-rank or skip | High-frequency nag on dormant | C | P2 |
| [ ] | EC-T-17 | `now` far in future / past vs `expires_at` | Compare against tick `now`, not wall clock only | Wrong expiry decisions | C/E | P1 |

---

## 3. Composition & hallucination (Phases B/C)

| Status | ID | Scenario | Expected | Anti-pattern | Phase | Pri |
|---|---|---|---|---|---|---|
| [ ] | EC-C-01 | Digest `top_item_id` missing from category | Omit research claim or skip send | Cite fake JIDA paper | B | P0 |
| [ ] | EC-C-02 | Merchant has no active offers | Don't invent ₹ prices | “Haircut @ ₹99” from nowhere | B | P0 |
| [ ] | EC-C-03 | Recall slots missing in payload | Ask open time / skip booking CTA | Invent Wed 6pm | B | P0 |
| [ ] | EC-C-04 | Competitor not in trigger payload | Don't name competitors | Invent “Smile Studio” | C | P0 |
| [ ] | EC-C-05 | Peer stats vs merchant CTR | Use real numbers only (`0.021` vs `0.030`) | Round to marketing fluff without numbers | B | P1 |
| [ ] | EC-C-06 | `customer_aggregate` field absent (generated mx) | Don't claim “124 high-risk adults” | Fabricate cohort counts | C | P0 |
| [ ] | EC-C-07 | Taboo vocab for dentists (`guaranteed`, `cure`) | Strip / regenerate | Clinical overclaim | B | P0 |
| [ ] | EC-C-08 | Generic “Flat 30% off” when service+price exists | Prefer catalog service+price | Discount-style copy | B/C | P0 |
| [ ] | EC-C-09 | Multiple CTAs in one body | Single primary CTA | YES/NO/MAYBE laundry list | B | P0 |
| [ ] | EC-C-10 | Buried CTA / long preamble | CTA in last sentence; no “hope you're well” essay | Long intro | B | P1 |
| [ ] | EC-C-11 | URL in body | Prefer none (examples: hard fail −3) | magicpin.com links | B/E | P0 |
| [ ] | EC-C-12 | Empty LLM body / malformed JSON | Repair once → skip action | Return empty body (−2) | B | P0 |
| [ ] | EC-C-13 | Rationale contradicts body | Rewrite rationale from used facts | Fake rationale for judge | B | P1 |
| [ ] | EC-C-14 | Copy case-study body verbatim | Original wording, same *shape* | Plagiarism similarity penalty | B–E | P0 |
| [ ] | EC-C-15 | Building names / offices not in context | Don't invent “Embassy Tech” etc. | Case Study 6 fabrication trap | C | P0 |
| [ ] | EC-C-16 | Program/package not in offers | Don't assert ₹2,499 bridal program unless in context | Assume catalog | C | P0 |
| [ ] | EC-C-17 | Wrong `send_as` | `vera` for merchant scope; `merchant_on_behalf` for customer | Customer msg as Vera identity | B | P0 |
| [ ] | EC-C-18 | Re-introduce “Hi I'm Vera” on turn 2+ | Never re-intro after first | Re-intro penalty | D | P1 |
| [ ] | EC-C-19 | LLM temperature / nondeterminism | temp=0; stable fact selection | Flaky submission.jsonl | B/E | P0 |
| [ ] | EC-C-20 | Prompt given entire 200-customer dump | Pass allowlisted fact pack only | Timeout + leakage risk | B | P1 |

---

## 4. Language & personalization (Phases B–D)

| Status | ID | Scenario | Expected | Anti-pattern | Phase | Pri |
|---|---|---|---|---|---|---|
| [ ] | EC-L-01 | Customer `language_pref: "hi-en mix"` | Natural code-mix | Pure English lecture | B | P0 |
| [ ] | EC-L-02 | Customer `language_pref: "english"` | English | Forced Hindi | B | P1 |
| [ ] | EC-L-03 | Regional mix (`te-en`, `kn-en`) | Honor pref lightly / respectful mix | Ignore regional cue | C | P1 |
| [ ] | EC-L-04 | Merchant `languages: ["en","hi"]` | Match; hi-en OK | Wrong language entirely | B | P0 |
| [ ] | EC-L-05 | Merchant switches Hindi mid-thread | Follow latest turn | Stick to English forever | D | P1 |
| [ ] | EC-L-06 | Owner `owner_first_name` present | Use Dr. Meera / Lakshmi / Karthik | Generic “Hi Merchant” | B | P1 |
| [ ] | EC-L-07 | Owner first name missing | Use business name | Hallucinate “Ramesh” | C | P1 |
| [ ] | EC-L-08 | Child customer (`Aanya (parent: Sneha)`) | Address appropriately (parent) | Talk to child as adult buyer | C | P1 |
| [ ] | EC-L-09 | Senior / son-mediated pharmacy (`grandfather`) | Respectful tone; may address caregiver channel | Casual slang / shame | C | P1 |
| [ ] | EC-L-10 | Unverified GBP merchant | Honest about verification lag if relevant | Claim “you're fully live” | C | P2 |

---

## 5. Customer scope, consent & ethics (Phases B/C)

| Status | ID | Scenario | Expected | Anti-pattern | Phase | Pri |
|---|---|---|---|---|---|---|
| [ ] | EC-U-01 | Trigger scope customer; consent missing topic | Do not send that kind | Promo without `promotional_offers` | C | P0 |
| [ ] | EC-U-02 | `reminder_opt_in: false` | Skip recall/appointment outreach | Send anyway | C | P0 |
| [ ] | EC-U-03 | State `churned` | Extra caution / skip or very soft; no guilt | Aggressive winback | C | P1 |
| [ ] | EC-U-04 | State `lapsed_hard` (gym) | No-shame framing | “You abandoned your goals” | C | P1 |
| [ ] | EC-U-05 | Customer belongs to different merchant_id | Never cross-message | Mix Priya into Studio11 | B | P0 |
| [ ] | EC-U-06 | Phone fields | Keep redacted; don't invent numbers | Fake phone in body | B | P0 |
| [ ] | EC-U-07 | Medical claims on dental/pharmacy customer msgs | No “guaranteed cure” | Overclaim | B | P0 |
| [ ] | EC-U-08 | Customer push arrives mid-test after merchant-only warmup | Accept; handle later recall tick | Ignore new customer | E | P0 |

---

## 6. Trigger-kind corner cases (Phase C)

| Status | ID | Scenario | Expected | Anti-pattern | Phase | Pri |
|---|---|---|---|---|---|---|
| [ ] | EC-K-01 | `ipl_match_today` on Saturday | Consider covers drop; maybe skip match promo | Blind “IPL special!” | C | P1 |
| [ ] | EC-K-02 | `seasonal_perf_dip` flagged expected | Reframe as normal; don't panic-sell ads | “Your business is failing” | C | P1 |
| [ ] | EC-K-03 | `perf_dip` severe + `renewal_due` same merchant | Prefer one coherent thread (urgency) | Two conflicting pitches same tick | C | P1 |
| [ ] | EC-K-04 | `supply_alert` urgency 5 | Fast, specific batches if in payload; workflow offer | Soft curiosity tone | C | P0 |
| [ ] | EC-K-05 | `competitor_opened` with named rival in payload | Use only payload name/distance/offer | Invent second competitor | C | P0 |
| [ ] | EC-K-06 | `curious_ask_due` | Ask merchant; reciprocity offer | Push discount | C | P1 |
| [ ] | EC-K-07 | `active_planning_intent` after merchant said yes | Deliver drafted artifact | More qualifying questions | C/D | P0 |
| [ ] | EC-K-08 | `dormant_with_vera` | Soft re-engage; low ask | High-pressure renewal dump | C | P2 |
| [ ] | EC-K-09 | `review_theme_emerged` with quote | Cite theme/count from payload | Invent review text | C | P0 |
| [ ] | EC-K-10 | `festival_upcoming` with large `days_until` | Low urgency; maybe skip or soft plan | “Diwali tomorrow!” when 188 days out | C | P1 |
| [ ] | EC-K-11 | `cde_opportunity` / webinar after expiry | Skip if `now` > event | Promote past webinar | C | P1 |
| [ ] | EC-K-12 | `gbp_unverified` | Clear next step for verification | Shame tone | C | P2 |
| [ ] | EC-K-13 | `chronic_refill_due` stock-out date today/past | Urgent, precise molecules from payload | Vague “medicines running out” | C | P1 |
| [ ] | EC-K-14 | `wedding_package_followup` far from wedding | Window-appropriate ask (skin-prep vs day-of) | Panic urgency months early | C | P2 |
| [ ] | EC-K-15 | Unknown / new kind from adaptive injection | Default prompt + facts; don't crash | 500 on router miss | C/E | P0 |

---

## 7. Multi-turn reply edge cases (Phase D)

| Status | ID | Scenario | Expected | Anti-pattern | Phase | Pri |
|---|---|---|---|---|---|---|
| [ ] | EC-R-01 | Classic WA Business auto-reply once | Detect; wait or one gentle retry | 3+ qualification turns | D | P0 |
| [ ] | EC-R-02 | Same auto-reply ×2 | `wait` (hours–day) | Keep chatting with bot | D | P0 |
| [ ] | EC-R-03 | Same auto-reply ×3–4 (hell) | `end` | Burn full 5-turn replay | D | P0 |
| [ ] | EC-R-04 | Auto-reply that looks “polite human” (“team tak pahuncha deti hoon”) | Still detect pattern / streak | Treat as engaged | D | P1 |
| [ ] | EC-R-05 | “Not interested. Stop messaging.” | `end`; suppress | “Are you sure?” loop | D | P0 |
| [ ] | EC-R-06 | Abuse / hostile | `end` or one apology then end | Argue / moralize | D | P0 |
| [ ] | EC-R-07 | “Ok let's do it. What's next?” | Action mode: execute | Another qualifying question | D | P0 |
| [ ] | EC-R-08 | Hindi commit (“haan kar do”, “bhej do”) | Same as intent commit | Miss non-English intent | D | P1 |
| [ ] | EC-R-09 | Off-topic GST / taxes | Decline + redirect to thread | Attempt GST advice | D | P0 |
| [ ] | EC-R-10 | Curveball question on-topic | Answer briefly from context or honest “I don't have that data” | Fabricate | D | P1 |
| [ ] | EC-R-11 | Merchant sends empty / whitespace | `wait` or gentle clarify once | Crash / empty send | D | P2 |
| [ ] | EC-R-12 | Unknown `conversation_id` on reply | Safe error or soft end; no 500 | Assume empty state + hallucinate | D | P0 |
| [ ] | EC-R-13 | `turn_number` jumps / out of order | Append by received order; don't crash | IndexError | D | P1 |
| [ ] | EC-R-14 | Reply after `action: end` | Stay ended; no new body | Revive dead conversation | D | P0 |
| [ ] | EC-R-15 | Reply during `wait_seconds` window | Honor wait; don't spam | Immediate re-pitch | D | P1 |
| [ ] | EC-R-16 | Verbatim same bot body twice | Regenerate / different angle | −2 anti-repetition | D | P0 |
| [ ] | EC-R-17 | Merchant asks to join magicpin (clear intent) | Route to action / next step | Qualifying loop (Pattern D fail) | D | P0 |
| [ ] | EC-R-18 | Mixed: engaged then auto-reply | Reset streak logic carefully | Misclassify engaged as auto | D | P2 |
| [ ] | EC-R-19 | Customer replies on `merchant_on_behalf` thread | Stay in merchant voice; booking flow | Switch to Vera persona mid-thread | D | P1 |
| [ ] | EC-R-20 | 5-turn cap from judge | Be concise; leave clean state | Endless tooling chatter | D | P1 |

---

## 8. Adaptive injection & versioning (Phase E)

| Status | ID | Scenario | Expected | Anti-pattern | Phase | Pri |
|---|---|---|---|---|---|---|
| [ ] | EC-E-01 | New digest item on category v2 | Later messages may use new item | Only ever cite old digest | E | P0 |
| [ ] | EC-E-02 | Performance snapshot updated | Numbers in body match latest | Stale views/CTR | E | P0 |
| [ ] | EC-E-03 | New trigger mid-window | Eligible on subsequent tick | Ignore until restart | E | P0 |
| [ ] | EC-E-04 | New customer + recall 2 min later | Compose with full customer context | Send without customer join | E | P0 |
| [ ] | EC-E-05 | Version bump during open conversation | Next reply uses new facts if relevant | Cache fact pack from turn 1 forever | E | P0 |
| [ ] | EC-E-06 | Judge injects context bot never saw in training | Use pushed payload only | Hallucinate “remembered” training data | E | P0 |

---

## 9. Operational / judge harness (Phases A/E)

| Status | ID | Scenario | Expected | Anti-pattern | Phase | Pri |
|---|---|---|---|---|---|---|
| [ ] | EC-O-01 | `/v1/tick` >30s | Avoid; return `[]` early | Timeout −1 | E | P0 |
| [ ] | EC-O-02 | `/v1/reply` >30s | Fast path for auto-reply/opt-out without LLM | `bot_silent` −1 | D/E | P0 |
| [ ] | EC-O-03 | Malformed action (missing `conversation_id` / `cta` / …) | Never emit; validate before return | Score 0 + −2 | A/B | P0 |
| [ ] | EC-O-04 | `action: send` with empty body | Blocked by validator | −2 | B | P0 |
| [ ] | EC-O-05 | Judge rate ~10 rps | Stateless handlers; no global lock pileup | Serialized LLM queue deadlock | E | P1 |
| [ ] | EC-O-06 | LLM API 429 / 5xx | Retry once short; else skip action / safe wait | Uncaught exception 500 | B/E | P0 |
| [ ] | EC-O-07 | LLM API key missing | Clear metadata/error; don't crash healthz | Healthz down → DQ | A | P0 |
| [ ] | EC-O-08 | Clock skew / ISO timestamps with offsets | Parse timezone-aware | Wrong expiry | C | P1 |
| [ ] | EC-O-09 | Deploy platform sleep / cold start | Keep warm or accept first healthz retries | 3 fails → DQ | E | P0 |
| [ ] | EC-O-10 | Logging PII to third parties | Only LLM provider; no other exfil | Webhook debug with full payloads | E | P0 |

---

## 10. Offline submission (`bot.py` / jsonl) (Phases B/E)

| Status | ID | Scenario | Expected | Anti-pattern | Phase | Pri |
|---|---|---|---|---|---|---|
| [ ] | EC-S-01 | 30 test pairs missing customer when null | `customer=None`; merchant message | Crash on None | B/E | P0 |
| [ ] | EC-S-02 | Pair has customer_id | Load customer; `send_as` correct | Always vera | B/E | P0 |
| [ ] | EC-S-03 | Regenerating jsonl twice | Stable at temp=0 | Random wording each run | E | P1 |
| [ ] | EC-S-04 | Line missing required keys | Schema complete per brief | Partial objects | E | P0 |
| [ ] | EC-S-05 | test_id mismatch vs `test_pairs.json` | Preserve `T01`… mapping | Renumbered ids | E | P0 |
| [ ] | EC-S-06 | compose >30s offline | Optimize; still must meet brief | Hang generation | E | P1 |

---

## 11. Category-specific traps (Phase C)

| Status | ID | Scenario | Expected | Anti-pattern | Phase | Pri |
|---|---|---|---|---|---|---|
| [ ] | EC-V-01 | Dentists: clinical peer tone | Source-cited, no hype | “AMAZING DEAL!!!” | C | P0 |
| [ ] | EC-V-02 | Salons: warm practical | OK light emoji; still specific | Pure clinical jargon | C | P2 |
| [ ] | EC-V-03 | Restaurants: operator language | covers, delivery, AOV if in data | Fake “Michelin” claims | C | P1 |
| [ ] | EC-V-04 | Gyms: no-shame lapse | Coach tone | Guilt trip | C | P0 |
| [ ] | EC-V-05 | Pharmacies: precise, calm | Batch/molecule accuracy; no alarmism | Scare tactics | C | P0 |
| [ ] | EC-V-06 | Cross-category voice bleed | Dentist prompt ≠ salon prompt | One global promo voice | C | P0 |

---

## 12. End-to-end scripted corner scenarios

Use these as integration tests after Phase D.

### Script S1 — Auto-reply hell
1. Tick CDE/research trigger → bot sends  
2. Reply canned ×1 → wait or one nudge  
3. Reply same canned ×2 → wait  
4. Reply same canned ×3 → **end**  
**Pass**: no more than one substantive retry; conversation closed.

### Script S2 — Intent transition
1. Tick planning or digest → qualify lightly  
2. Merchant engages  
3. Merchant: “Ok, let's do it”  
**Pass**: next bot turn delivers artifact / concrete action, not another question.

### Script S3 — Hostile exit
1. Tick any  
2. Merchant: “Stop. This is useless.”  
**Pass**: `end` (+ optional one-line apology); later ticks skip merchant.

### Script S4 — Adaptive digest
1. Compose on digest A  
2. Context push category v2 with new compliance item  
3. New related trigger or follow-up  
**Pass**: new item eligible; no citation of items never pushed.

### Script S5 — Consent block
1. Customer opted in only `appointment_reminders`  
2. Tick promotional / match-night style customer trigger  
**Pass**: `{actions: []}` or skip that customer.

### Script S6 — Missing join
1. Tick `trg_003_recall` before customer context pushed  
**Pass**: skip; after customer push + tick → send.

### Script S7 — Saturday IPL judgment
1. Tick `ipl_match_today` with `is_weeknight: false`  
**Pass**: nuanced recommendation using existing offer; not blind match promo.

### Script S8 — Suppression
1. Successful research send with key `research:dentists:2026-W17`  
2. Same trigger available next tick  
**Pass**: no second send.

---

## 13. Mapping to implementation-plan phases

| Phase | Edge-case groups to clear before exit |
|---|---|
| **A** | EC-A-*, EC-T-01/02/10, EC-O-03/07 |
| **B** | EC-C-01–14, EC-L-01/04/06, EC-U-05/06, EC-S-01/02 |
| **C** | EC-T-*, EC-K-*, EC-V-*, EC-U-01–04, EC-C-15/16 |
| **D** | EC-R-*, Scripts S1–S3 |
| **E** | EC-E-*, EC-O-*, EC-S-*, Scripts S4–S8 |

---

## 14. Quick triage: if judge score drops

| Symptom | Likely edge cases |
|---|---|
| Low Specificity | EC-C-01–06, EC-C-15 |
| Low Category fit | EC-C-07/08, EC-V-* |
| Low Merchant fit | EC-L-*, EC-C-05 |
| Low Trigger relevance | EC-T-03/11, EC-K-10/11 |
| Low Compulsion | EC-C-09/10, EC-K-06 |
| Operational penalties | EC-O-01–04, EC-R-01–03 |
| Replay failure | EC-R-03/05/07/09 |
| Adaptation failure | EC-E-01–05 |

---

## End of edge-case.md

Companions:
- Build order: `implementation-plan.md`
- Architecture: `architecture.md`
- Product/rubric: `Context.md`
- HTTP examples: `examples/api-call-examples.md`
- Quality anchors: `examples/case-studies.md`

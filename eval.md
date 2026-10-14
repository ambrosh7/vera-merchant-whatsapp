# Evaluation Playbook — magicpin Merchant AI Assistant

**Status**: Eval plan for Phases A–E  
**Sources**: `implementation-plan.md`, `Context.md`, `architecture.md`, `edge-case.md`, `examples/`, `judge_simulator.py`  
**Last updated**: 2026-10-13  
**Audience**: Builders deciding go/no-go at each phase gate and before ship

> **Purpose**: Define *what* we measure, *how* we measure it, *pass thresholds*, and *which commands/scenarios* to run so evaluation stays aligned with the contest judge — not vibes.

---

## 1. Eval principles

1. **Same rubric as the contest** — 5 dimensions × 0–10 = 50 (+ operational / adaptation / replay modifiers).
2. **Shape over plagiarism** — match Case Study *patterns*; never copy case-study bodies (similarity penalty).
3. **Facts over fluency** — a fluent hallucinated message fails Specificity.
4. **Phase gates are hard** — do not start Phase N+1 until Phase N exit metrics pass.
5. **Automate the floor, LLM-judge the ceiling** — schema/latency/suppression = deterministic tests; quality = LLM scorer + human spot-check.
6. **Log everything local** — trigger_id, prompt version, latency_ms, validate_fail reason, dimension scores.

---

## 2. Score model (contest-aligned)

### 2.1 Core quality (per composed action)

| Dimension | 0–10 looks for | Cap / hard fails |
|---|---|---|
| **Specificity** | Concrete fact from contexts (number, date, source, offer, slot) | Generic sales talk ≤4; fabricated fact → ≤3 |
| **Category fit** | Voice, vocab, offer format for vertical | Taboo hit (e.g. “guaranteed”) ≤4 |
| **Merchant fit** | This merchant’s state, name, language, history | Wrong language / ignore signals ≤5 |
| **Trigger relevance** | Clear *why now* for this trigger | Generic “improve profile” ≤4 |
| **Engagement compulsion** | Would a real merchant reply? Lever + CTA | Multi-CTA / buried ask ≤5 |

**Per-action total** = sum of 5 dims (max 50).

### 2.2 Contest modifiers (Context / testing brief)

| Modifier | When | Range |
|---|---|---|
| Adaptation bonus | Mid-test context injection used correctly | up to +5 per dimension (harness) |
| Replay score | Top-10 deep dives (auto-reply / intent / hostile) | up to +30 |
| Operational penalties | Timeouts, healthz fails, malformed, repeats | up to −20 |

### 2.3 Local composite (what we track daily)

```
local_quality_avg   = mean(per-action totals)          # target ≥40; ship digest/recall ≥45
ops_penalty         = timeouts + malformed + repeats   # target 0
replay_pass_rate    = (# replay scripts passed) / 3    # target 100%
gate_status         = PASS iff quality + ops + phase exit all green
```

---

## 3. Eval layers

```
┌─────────────────────────────────────────────────────────────┐
│ L4  Ship eval          full judge + deploy + jsonl freeze   │
├─────────────────────────────────────────────────────────────┤
│ L3  Replay / multi-turn   auto-reply, intent, hostile       │
├─────────────────────────────────────────────────────────────┤
│ L2  Composition quality   LLM judge + case-study checklist  │
├─────────────────────────────────────────────────────────────┤
│ L1  Contract / ops        schema, versioning, latency, EC-* │
└─────────────────────────────────────────────────────────────┘
```

| Layer | Tools | Frequency |
|---|---|---|
| L1 | curl, unit tests, `edge-case.md` P0s | Every PR / phase A+ |
| L2 | `judge_simulator.py` phase2_short + manual rubric | Phase B+ daily |
| L3 | `auto_reply_hell`, `intent_transition`, `hostile` | Phase D+ |
| L4 | `all` / `full_evaluation` + public URL | Phase E |

---

## 4. Tooling

### 4.1 Local judge simulator

```bash
# terminal 1
uvicorn bot.app:app --host 0.0.0.0 --port 8080

# terminal 2 — configure BOT_URL + LLM_* in judge_simulator.py header
python judge_simulator.py
```

| `TEST_SCENARIO` | What it exercises | Phase |
|---|---|---|
| `warmup` | healthz, metadata, context push | A |
| `phase2_short` | warmup + tick + LLM score actions | B–C |
| `auto_reply_hell` | repeated canned replies | D |
| `intent_transition` | commit → action | D |
| `hostile` | opt-out / abuse | D |
| `all` | suite aggregate | D–E |
| `full_evaluation` | broader run | E |

### 4.2 Contract smoke (no LLM)

```bash
export BOT_URL=http://localhost:8080
curl -s $BOT_URL/v1/healthz | jq .
curl -s $BOT_URL/v1/metadata | jq .

# Push category (wrap as context envelope in real use)
curl -s -X POST $BOT_URL/v1/context \
  -H 'Content-Type: application/json' \
  -d @- <<'EOF'
{"scope":"category","context_id":"dentists","version":1,
 "delivered_at":"2026-04-26T09:45:00Z",
 "payload": $(cat dataset/categories/dentists.json)}
EOF
```

Follow sequences in `examples/api-call-examples.md` Phases 1–2.

### 4.3 Offline compose eval

```bash
python dataset/generate_dataset.py --seed-dir dataset --out dataset/expanded
# then your script:
python -m bot.compose_offline --pairs dataset/expanded/test_pairs.json \
  --out submission.jsonl
```

Score a sample of lines with the same 5-dimension rubric (LLM or human).

### 4.4 Recommended local artifacts

```
eval_runs/
├── YYYYMMDD_HHMM/
│   ├── actions.jsonl          # every tick/reply action
│   ├── scores.jsonl           # per-action 5 dims + notes
│   ├── ops.json               # latencies, timeouts, malformed
│   ├── edge_coverage.md       # checked EC-* ids
│   └── summary.md             # gate PASS/FAIL
```

---

## 5. Phase-gated evaluation

### Phase A — Skeleton (Day 1)

**Eval type**: L1 only (no quality score required)

| Metric | Pass | Fail |
|---|---|---|
| Endpoints 5/5 schema-valid | yes | any 500 / wrong shape |
| Version conflict → 409 | yes | accepts downgrade |
| Healthz counts match pushes | exact | off-by-one |
| `judge_simulator` `warmup` | success | unreachable / reject |
| Healthz p95 latency | <2s | slow enough to risk DQ |

**Edge coverage**: `EC-A-*` P0, `EC-T-01/02/10`, `EC-O-03/07`  
**Go/No-go**: all rows Pass → start Phase B.

---

### Phase B — Compose digest + recall (Days 2–3)

**Eval type**: L1 + L2 on two golden paths

#### Golden path G1 — Research digest (Case Study 1 shape)

| Check | Pass criteria |
|---|---|
| Source citation | Mentions JIDA / page or equivalent from digest |
| Number from context | e.g. trial_n 2100 and/or 38% if in digest |
| Merchant anchor | high-risk cohort / signal / locality — from merchant JSON |
| `send_as` | `vera` |
| CTA | single open_ended or binary |
| Fabrication | zero invented papers/competitors |
| Dimension total | **≥40/50** (target **≥45**) |

#### Golden path G2 — Recall Priya (Case Study 2 shape)

| Check | Pass criteria |
|---|---|
| `send_as` | `merchant_on_behalf` |
| Language | hi-en mix when pref says so |
| Offer | real active catalog price (e.g. ₹299) |
| Slots | only from trigger payload |
| Consent | within recall/appointment scope |
| Dimension total | **≥40/50** (target **≥45**) |

**Commands**:
```text
TEST_SCENARIO=phase2_short  # after pushing trg_001 / trg_003 manually if needed
```

**Heuristic pre-score (before LLM judge)** — binary checklist:

- [ ] ≥1 verifiable number/date/source from contexts  
- [ ] Owner or business name correct  
- [ ] Trigger kind recognizable in first 2 sentences  
- [ ] No URL  
- [ ] No taboo terms  
- [ ] Rationale mentions the same facts as body  

If any unchecked → do not bother LLM-scoring; fix composer.

**Go/No-go**: G1+G2 ≥40; offline `bot.py` works; no fabrication in spot check.

---

### Phase C — Full kinds + selection (Days 4–5)

**Eval type**: L2 across verticals + selection behavior

#### Quality sampling plan

Score **at least 2 actions per family** (or seed triggers):

| Family | Seed examples | Min avg |
|---|---|---|
| Research/compliance | trg_001, trg_002 | ≥40 |
| Recall/booking | trg_003 | ≥40 |
| Perf | trg_004, trg_014, trg_024 | ≥38 |
| Events | trg_006, trg_010 | ≥38 |
| Curious / review | trg_008, trg_011 | ≥38 |
| Commercial | trg_005, trg_009 | ≥38 |
| Customer lifecycle | trg_007, trg_015, trg_019 | ≥38 |
| Planning / supply | trg_013, trg_016, trg_018 | ≥40 |

**Portfolio gate**: mean of all scored actions **≥40/50**.

#### Selection / ops checks

| Test | Pass |
|---|---|
| Empty available_triggers | `actions: []` |
| Expired trigger | skipped |
| Duplicate suppression_key | no second send |
| Consent mismatch | skip customer send |
| Tick latency | p95 <25s; zero timeouts in local run |
| Cap | ≤ soft max actions (e.g. 5) |

**Vertical smoke**: one green path each for dentists, salons, restaurants, gyms, pharmacies.

**Edge coverage**: `EC-T-*`, `EC-K-*`, `EC-V-*`, `EC-U-01–04` P0s.

**Go/No-go**: portfolio ≥40; selection tests pass; spam not observed.

---

### Phase D — Multi-turn (Days 6–7)

**Eval type**: L3 replay scripts (binary pass/fail + light quality)

| Script | Simulator / manual | Pass |
|---|---|---|
| S1 Auto-reply hell | `auto_reply_hell` + `edge-case.md` S1 | `end` by streak 3; ≤1 substantive retry |
| S2 Intent transition | `intent_transition` + S2 | Action mode; no extra qualify |
| S3 Hostile / stop | `hostile` + S3 | `end`; no further pitches |
| S8-adjacent | reply after end | stays silent / ended |

**Ops**: reply p95 <25s; prefer rule-based classify for auto-reply/opt-out (no LLM required).

**Anti-repetition**: force same engaged path twice → second body ≠ first (or regenerate).

**Go/No-go**: 3/3 replay scripts pass; `ops_penalty` from reply path = 0.

---

### Phase E — Harden & ship (Day 8+)

**Eval type**: L4 full

| Suite | Pass |
|---|---|
| Adaptive S4 | New digest/perf used after version bump |
| Consent S5 | Promo blocked when out of scope |
| Missing join S6 | Skip until customer present |
| Judgment S7 | Saturday IPL nuanced |
| Suppression S8 | No double-send |
| `TEST_SCENARIO=all` or `full_evaluation` | Completes; quality ≥40 avg |
| Deployed URL | Warmup + short phase2 from remote |
| `submission.jsonl` | 30 lines; schema complete; stable regen |
| README / metadata | Consistent |

**Ship bar (must all be true)**:

1. Digest/recall golden paths **≥45/50**  
2. Portfolio average **≥40/50**  
3. Replay **3/3** pass  
4. Operational penalties **0** in final local full run  
5. Adaptation scripts **pass**  
6. Public URL healthz stable (≥3 consecutive polls OK)  
7. Submission artifacts complete  

---

## 6. Human / LLM scoring worksheet

Use for any action (tick or offline jsonl line).

```
test_id / conversation_id: _______________
trigger.kind: _______________
send_as: vera | merchant_on_behalf

Specificity        __ /10   evidence: _______________________
Category fit       __ /10   evidence: _______________________
Merchant fit       __ /10   evidence: _______________________
Trigger relevance  __ /10   evidence: _______________________
Compulsion         __ /10   levers: _______________________
TOTAL              __ /50

Fabrication?  Y/N   (if Y, cap dims at 3)
URL present?  Y/N   (if Y, fail ops)
Taboo hit?    Y/N
Case-study near-duplicate? Y/N

Notes:
```

**Calibration**: score G1 against Case Study 1 commentary in `examples/case-studies.md` once as a team so “7 vs 9” means the same thing.

---

## 7. Deterministic automated checks (implement early)

These should be unit/integration tests — no LLM:

| Check ID | Assert |
|---|---|
| AUTO-01 | Context v2 replaces v1 |
| AUTO-02 | Stale version → 409 |
| AUTO-03 | Healthz counts |
| AUTO-04 | Tick with unknown trigger → no crash, skip |
| AUTO-05 | Expired trigger skipped |
| AUTO-06 | Suppression key blocks second send |
| AUTO-07 | Customer trigger without consent scope → no action |
| AUTO-08 | `send_as` matches trigger.scope |
| AUTO-09 | Action schema required keys present |
| AUTO-10 | Body non-empty |
| AUTO-11 | No URL regex in body (policy) |
| AUTO-12 | Taboo list intersection empty |
| AUTO-13 | Auto-reply streak 3 → action end |
| AUTO-14 | Opt-out phrase → end |
| AUTO-15 | Intent phrase → mode action (flag) |
| AUTO-16 | Repeat body rejected |
| AUTO-17 | Fact pack: top_item_id resolves or omitted |
| AUTO-18 | Tick returns within 25s soft budget (fake LLM) |

Map failures to `edge-case.md` IDs in test names (`test_EC_A_02_stale_version`).

---

## 8. LLM-as-judge prompt contract (local)

When scoring with an LLM (as `judge_simulator` does), require:

1. Inputs: action body + category/merchant/trigger/(customer) JSON slices  
2. Output: JSON `{specificity, category_fit, merchant_fit, trigger_relevance, compulsion, notes, fabrication: bool}`  
3. Instruction: penalize any claim not grounded in provided contexts  
4. Instruction: do not reward similarity to case-study wording  

If `fabrication: true` → force total ≤15/50 for reporting.

---

## 9. Regression suite (minimum)

Run before every prompt change (Phase B+):

| # | Name | Layer |
|---|---|---|
| R1 | Warmup | L1 |
| R2 | G1 digest compose | L2 |
| R3 | G2 recall compose | L2 |
| R4 | IPL / seasonal judgment spot | L2 |
| R5 | Supply alert specificity | L2 |
| R6 | Auto-reply hell | L3 |
| R7 | Intent transition | L3 |
| R8 | Hostile stop | L3 |
| R9 | Version bump adaptation | L1+L2 |
| R10 | Suppression double-tick | L1 |

**Pass rule**: R1–R3, R6–R8, R10 must pass; R4/R5/R9 should not regress >5 points vs last `eval_runs/` baseline.

---

## 10. Metrics dashboard (lightweight)

Track per eval run:

| Metric | Target |
|---|---|
| `quality_avg` | ≥40 (≥45 on G1/G2) |
| `quality_p50` / `quality_p10` | p10 ≥30 (no catastrophic tails) |
| `fabrication_rate` | 0% |
| `timeout_count` | 0 |
| `malformed_count` | 0 |
| `repeat_count` | 0 |
| `tick_latency_p95_ms` | <25000 |
| `reply_latency_p95_ms` | <25000 |
| `empty_tick_rate` | >0 when appropriate (not 0% spam) |
| `replay_pass` | 3/3 |
| `edge_p0_coverage` | 100% checked for current phase |
| `llm_cost_per_full_run` | budgeted |

---

## 11. Failure triage (eval → fix)

| Eval signal | Likely cause | Fix in |
|---|---|---|
| Specificity low | Fat prompts / weak fact pack | Phase B assembler |
| Category fit low | Missing kind/vertical prompt | Phase C router |
| Merchant fit low | Not passing signals/name/lang | Fact pack |
| Trigger relevance low | Wrong template / buried hook | Kind prompt |
| Compulsion low | Weak CTA / no lever | Base prompt |
| Timeouts | Slow LLM / too many actions | Cap + soft deadline |
| Replay fail | Classifier FSM | Phase D handlers |
| Adaptation fail | Cached stale facts | Compose reads latest version |
| Near-duplicate case study | Overfit examples in prompt | Remove verbatim few-shots |

See also `edge-case.md` §14 quick triage.

---

## 12. Phase exit scorecard (copy per gate)

```markdown
## Gate: Phase __  |  Date: ____  |  Run: eval_runs/____

### L1 Contract
- [ ] Schemas / versioning / healthz
- [ ] Latency budgets
- [ ] EC P0s for this phase

### L2 Quality
- quality_avg: __ /50   (need ≥__)
- G1: __ /50   G2: __ /50
- fabrication_rate: __%

### L3 Replay (if Phase D+)
- auto_reply: PASS/FAIL
- intent: PASS/FAIL
- hostile: PASS/FAIL

### L4 Ship (if Phase E)
- submission.jsonl: 30 lines OK
- public URL: OK
- full_evaluation: OK

### Decision
- [ ] GO to next phase
- [ ] NO-GO — blockers: _______________
```

---

## 13. Final contest readiness checklist

- [ ] Core rubric portfolio ≥40/50; G1/G2 ≥45/50  
- [ ] Operational penalties 0 on final full local run  
- [ ] Replay 3/3  
- [ ] Adaptive injection scripts pass  
- [ ] `edge-case.md` all P0 for A–E marked done  
- [ ] Regression R1–R10 green vs baseline  
- [ ] `bot.py` + `submission.jsonl` (30) + `README.md`  
- [ ] Public `/v1/*` durable for full window  
- [ ] Privacy: no non-LLM exfil of payloads  
- [ ] Prompt version frozen and recorded in metadata  

---

## 14. Mapping to implementation-plan

| Plan phase | Primary eval section | Simulator | Threshold |
|---|---|---|---|
| A | §5 Phase A | `warmup` | L1 green |
| B | §5 Phase B | `phase2_short` + G1/G2 | ≥40 (aim 45) |
| C | §5 Phase C | `phase2_short` + sampling | portfolio ≥40 |
| D | §5 Phase D | `auto_reply_hell`, `intent_transition`, `hostile` | 3/3 |
| E | §5 Phase E | `all` / `full_evaluation` | ship bar §5 |

---

## End of eval.md

Companions:
- Build order: `implementation-plan.md`
- Corner cases: `edge-case.md`
- Architecture: `architecture.md`
- Product/rubric: `Context.md`
- Quality anchors: `examples/case-studies.md`
- HTTP contract: `examples/api-call-examples.md`
- Harness: `judge_simulator.py`

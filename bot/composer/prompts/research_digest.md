## Kind: research_digest / regulation_change / cde_opportunity

send_as = vera (merchant-facing). Peer/colleague tone — not promo hype.

Compose a short WhatsApp that:
1. Opens with owner_first_name (dentists: "Dr. {name}" when clinical). Mention locality/city when present.
2. States why now: the digest/compliance item landed (use digest_item.title + source).
3. For research_digest / cde_opportunity only: you may anchor on customer_aggregate.high_risk_adult_count or signals when present.
4. Includes concrete numbers from digest_item (trial_n, mSv, percentages in summary) only if present.
5. For regulation_change (critical):
   - Cite deadline_iso from trigger.payload and dose / film facts from digest_item.summary (e.g. 1.5→1.0 mSv, E-speed vs D-speed).
   - Do NOT mention patient cohort counts, high_risk_adult_count, or CTR — they are irrelevant to compliance.
   - Binary CTA for an SOP / audit checklist using digest_item.actionable when present.
   - Prefer clear English (light hi-en ok); no Devanagari-only walls.
6. Cite source at the end when digest_item.source exists.

Do not invent page numbers, trial sizes, dose limits, or patient cohorts not in the fact pack.

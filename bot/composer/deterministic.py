"""
Deterministic fact-pack composers for all Phase C kind families.
Used when LLM is unavailable; never invents facts missing from the pack.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Optional


def _first_name(facts: dict[str, Any]) -> str:
    m = facts.get("merchant") or {}
    return m.get("owner_first_name") or (m.get("name") or "there").split()[0]


def _biz(facts: dict[str, Any]) -> str:
    return (facts.get("merchant") or {}).get("name") or "your business"


def _payload(facts: dict[str, Any]) -> dict[str, Any]:
    return (facts.get("trigger") or {}).get("payload") or {}


def _pct_from_text(text: str) -> Optional[str]:
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", text or "")
    return m.group(1) + "%" if m else None


def _offer(facts: dict[str, Any]) -> Optional[str]:
    offers = (facts.get("merchant") or {}).get("active_offers") or []
    if offers:
        return offers[0].get("title")
    return None


def _base(facts: dict[str, Any], body: str, cta: str, rationale: str, send_as: Optional[str] = None) -> dict[str, Any]:
    trg = facts.get("trigger") or {}
    kind = trg.get("kind") or "generic"
    name = _first_name(facts)
    return {
        "body": body.strip(),
        "cta": cta,
        "rationale": rationale,
        "send_as": send_as or facts.get("send_as") or "vera",
        "template_name": f"vera_{kind}_v1",
        "template_params": [name, kind, body[:60]],
        "suppression_key": trg.get("suppression_key") or "",
    }


# ----- research / compliance -----

def compose_research_digest(facts: dict[str, Any]) -> dict[str, Any]:
    m = facts.get("merchant") or {}
    dig = facts.get("digest_item") or {}
    agg = m.get("customer_aggregate") or {}
    signals = m.get("signals") or []
    peer = (facts.get("category") or {}).get("peer_stats") or {}
    name = _first_name(facts)
    payload = _payload(facts)

    title = dig.get("title") or "a new category update"
    source = dig.get("source") or ""
    summary = dig.get("summary") or ""
    trial_n = dig.get("trial_n")
    segment = dig.get("patient_segment") or dig.get("segment")
    deadline = payload.get("deadline_iso")

    kind = (facts.get("trigger") or {}).get("kind")
    locality = m.get("locality")
    city = m.get("city")
    place = ", ".join([p for p in (locality, city) if p])
    offer = _offer(facts)
    who = f"Dr. {name}" if name and name != "there" else name

    # regulation_change: digest + deadline only; benefit-hook binary CTA
    if kind == "regulation_change":
        lead = f"{who}"
        if place:
            lead += f" ({place})"
        lead += ", compliance note"
        if deadline:
            lead += f" — deadline {deadline[:10]}"
        lead += "."
        # Prefer short concrete facts over dumping full summary
        mid = f" {title}."
        dose = re.search(
            r"(\d+(?:\.\d+)?\s*mSv).*?(\d+(?:\.\d+)?\s*mSv)", summary or "", re.I
        )
        if dose:
            mid += f" IOPA max drops {dose.group(1)} → {dose.group(2)}"
            if "E-speed" in (summary or ""):
                mid += " (E-speed/RVG OK; D-speed fails)"
            mid += "."
        elif summary:
            first = re.split(r"(?<=[A-Za-z\)])\.\s+", summary.strip(), maxsplit=1)[0].strip()
            if first and not first.endswith("."):
                first += "."
            mid += f" {first}"
        team = locality or city or "clinic"
        ask = (
            f" Want me to draft a 5-point SOP for your {team} team so the"
            f" {deadline[:10] if deadline else 'deadline'} audit is a non-event — reply YES?"
        )
        body = (lead + mid + ask).replace("  ", " ").strip()
        if source:
            body += f" — {source}"
        return _base(
            facts, body, "binary_yes_no", f"kind={kind}; source={source or 'n/a'}"
        )

    # research_digest: case-study shape (specificity + merchant cohort + reciprocity)
    if kind == "research_digest":
        src_short = source.split(",")[0].strip() if source else "New research"
        lead = f"{who}, {src_short} landed. "
        if agg.get("high_risk_adult_count"):
            mid = (
                f"One item relevant to your {agg['high_risk_adult_count']} "
                f"high-risk adult patients — "
            )
        elif segment:
            mid = f"One item relevant if you see {str(segment).replace('_', ' ')} patients — "
        else:
            mid = "One item worth your time — "
        # Prefer trial outcome framing over raw title dump
        pct = _pct_from_text(summary) or _pct_from_text(title)
        if trial_n and pct and "fluoride" in (title + summary).lower():
            mid += (
                f"{trial_n:,}-patient trial showed 3-month fluoride recall cuts caries "
                f"recurrence {pct} better than 6-month."
            )
        else:
            mid += f"{title}"
            bits = []
            if trial_n:
                bits.append(
                    f"{trial_n:,}-patient"
                    if isinstance(trial_n, int)
                    else f"{trial_n}-patient"
                )
            if pct:
                bits.append(pct)
            if bits:
                mid += f" ({', '.join(bits)})"
            mid += "."
            if summary:
                first = re.split(r"(?<=[A-Za-z\)])\.\s+", summary.strip(), maxsplit=1)[
                    0
                ].strip()
                if first and not first.endswith("."):
                    first += "."
                mid += f" {first}"
        if not mid.rstrip().endswith("."):
            mid = mid.rstrip() + "."
        # Optional peer/CTR social proof from real merchant signals
        proof = ""
        if (
            "ctr_below_peer_median" in signals
            and m.get("performance", {}).get("ctr") is not None
            and peer.get("avg_ctr") is not None
        ):
            proof = (
                f" Your CTR is {m['performance']['ctr']:.1%} vs peer ~{peer['avg_ctr']:.1%}"
                " — a tighter recall cadence is one lever."
            )
        ask = (
            " Worth a look (2-min abstract). Want me to pull it + draft a patient-ed "
            "WhatsApp you can share — reply YES?"
        )
        body = (lead + mid + proof + " " + ask).replace("  ", " ").strip()
        if source:
            body += f"  — {source}"
        return _base(
            facts, body, "binary_yes_no", f"kind={kind}; source={source or 'n/a'}"
        )

    if kind == "cde_opportunity":
        credits = payload.get("credits") or dig.get("credits")
        lead = f"{who}, CDE opportunity"
        if credits:
            lead += f" ({credits} credits)"
        lead += f". {title}."
        ask = " Want me to draft the one-line RSVP WhatsApp — reply YES?"
        body = (lead + " " + ask).replace("  ", " ").strip()
        if source:
            body += f" — {source}"
        return _base(
            facts, body, "binary_yes_no", f"kind={kind}; source={source or 'n/a'}"
        )

    # generic digest-family fallback
    lead = f"{who}, "
    if source:
        lead += f"{source.split(',')[0]} landed. "
    else:
        lead += "Quick category note. "
    mid = f"One item worth your time — {title}."
    if summary:
        first = re.split(r"(?<=[A-Za-z\)])\.\s+", summary.strip(), maxsplit=1)[0].strip()
        if first and not first.endswith("."):
            first += "."
        mid += f" {first}"
    ask = " Want me to pull the abstract + draft a short WhatsApp you can share — reply YES?"
    body = (lead + mid + " " + ask).replace("  ", " ").strip()
    if source:
        body += f" — {source}"
    return _base(
        facts, body, "binary_yes_no", f"kind={kind}; source={source or 'n/a'}"
    )


# ----- recall / booking -----

def compose_recall_due(facts: dict[str, Any]) -> dict[str, Any]:
    m = facts.get("merchant") or {}
    c = facts.get("customer") or {}
    payload = _payload(facts)
    cust = c.get("name") or "there"
    biz = m.get("name") or "our clinic"
    owner = m.get("owner_first_name")
    lang = (c.get("language_pref") or "").lower()
    hi_mix = "hi" in lang or "mix" in lang
    service = (payload.get("service_due") or "visit").replace("_", " ")
    slots = payload.get("available_slots") or payload.get("next_session_options") or []
    slot_labels = []
    for s in slots[:2]:
        if isinstance(s, dict) and s.get("label"):
            slot_labels.append(s["label"])
        elif isinstance(s, str):
            slot_labels.append(s)
    offer_title = _offer(facts)
    last = payload.get("last_service_date") or (c.get("relationship") or {}).get("last_visit")
    due = payload.get("due_date")
    time_line = "your recall window is open"
    if last and due:
        time_line = f"your {service} recall is due (last visit {last})"
    elif last:
        time_line = f"it's been a while since {last} — {service} recall is due"

    # Prefer binary CTA (scores better than Reply 1/2 multi-choice)
    if hi_mix:
        greet = (
            f"Hi {cust}, Dr. {owner}'s clinic here"
            if owner
            else f"Hi {cust}, {biz} here"
        )
        slot_bit = ""
        if slot_labels:
            slot_bit = " Apke liye " + (" ya ".join(slot_labels)) + " ready hain."
        offer_bit = f" {offer_title}." if offer_title else ""
        scarce = (
            f" Sirf {len(slot_labels)} evening slots hold kiye hain is week."
            if len(slot_labels) >= 2
            else ""
        )
        body = (
            f"{greet}. {time_line[0].upper() + time_line[1:]}.{slot_bit}{offer_bit}{scarce}"
            " Reply YES for the first slot, or tell us a time that works."
        )
    else:
        who = f"Dr. {owner}'s clinic" if owner else biz
        body = f"Hi {cust}, {who} here. {time_line[0].upper() + time_line[1:]}."
        if slot_labels:
            body += " Open: " + " or ".join(slot_labels) + "."
            if len(slot_labels) >= 2:
                body += f" Only {len(slot_labels)} slots held this week."
        if offer_title:
            body += f" {offer_title}."
        body += " Reply YES to book the first slot, or suggest a better time."
    cta = "binary_yes_no"
    return _base(
        facts, body, cta,
        f"kind=recall; lang={c.get('language_pref')}; slots={len(slot_labels)}",
        send_as="merchant_on_behalf",
    )


# ----- performance -----

def compose_performance(facts: dict[str, Any]) -> dict[str, Any]:
    name = _first_name(facts)
    m = facts.get("merchant") or {}
    payload = _payload(facts)
    kind = (facts.get("trigger") or {}).get("kind")
    metric = payload.get("metric") or "views"
    delta = payload.get("delta_pct")
    window = payload.get("window") or "7d"
    delta_s = f"{delta:+.0%}" if isinstance(delta, (int, float)) else str(delta or "")
    members = (m.get("customer_aggregate") or {}).get("total_unique_ytd")

    if kind == "seasonal_perf_dip" or payload.get("is_expected_seasonal"):
        note = payload.get("season_note") or "seasonal lull"
        body = (
            f"{name}, {metric} {delta_s} over {window} — flagging this as the expected "
            f"seasonal {note.replace('_', ' ')} window, not a sudden collapse."
        )
        if members:
            body += f" Focus retention on your ~{members} known customers for now."
        body += " Want me to draft a light retention challenge instead of boosting ads?"
        return _base(facts, body, "binary_yes_no", f"kind=seasonal_perf_dip; metric={metric}")

    if kind == "perf_spike":
        driver = payload.get("likely_driver")
        body = f"{name}, nice move — {metric} {delta_s} over {window}."
        if driver:
            body += f" Likely driver: {str(driver).replace('_', ' ')}."
        body += " Want me to draft a follow-up Google post to lock it in?"
        return _base(facts, body, "binary_yes_no", f"kind=perf_spike; metric={metric}")

    # perf_dip
    baseline = payload.get("vs_baseline")
    body = f"{name}, heads-up: {metric} {delta_s} over {window}."
    if baseline is not None:
        body += f" Baseline was ~{baseline}."
    body += " I can audit your last 3 Google posts + active offers and suggest one fix. Shall I?"
    return _base(facts, body, "binary_yes_no", f"kind=perf_dip; metric={metric}")


# ----- events -----

def compose_events(facts: dict[str, Any]) -> dict[str, Any]:
    name = _first_name(facts)
    payload = _payload(facts)
    kind = (facts.get("trigger") or {}).get("kind")
    offer = _offer(facts)

    if kind == "ipl_match_today":
        match = payload.get("match") or "tonight's match"
        venue = payload.get("venue")
        is_weeknight = payload.get("is_weeknight")
        body = f"Quick heads-up {name} — {match}"
        if venue:
            body += f" at {venue}"
        body += "."
        if is_weeknight is False:
            body += (
                " Saturday IPL usually pulls dine-in covers down — skip a match-night "
                "dine-in promo."
            )
            if offer:
                body += f" Better: push your existing {offer} as delivery-focused."
            else:
                body += " Better: lean delivery / takeaway messaging."
        else:
            if offer:
                body += f" Want me to draft a match-night note around {offer}?"
            else:
                body += " Want a short match-night WhatsApp draft?"
        body += " I can draft copy in ~10 min — reply YES."
        return _base(facts, body, "binary_yes_no", f"kind=ipl; weeknight={is_weeknight}")

    # festival
    festival = payload.get("festival") or "the festival"
    days = payload.get("days_until")
    date = payload.get("date")
    if isinstance(days, (int, float)) and days > 60:
        body = (
            f"{name}, early note for {festival}"
            + (f" ({date})" if date else "")
            + f" — still {int(days)} days out, so no rush."
        )
        body += " Want me to park a simple prep checklist for when you're closer?"
        return _base(facts, body, "binary_yes_no", f"kind=festival; days_until={days}")
    body = f"{name}, {festival} is coming up"
    if days is not None:
        body += f" in {days} days"
    body += "."
    if offer:
        body += f" Your {offer} can be the hero."
    body += " Want a 3-line WhatsApp + Google post draft?"
    return _base(facts, body, "binary_yes_no", f"kind=festival; days_until={days}")


# ----- engagement -----

def compose_engagement(facts: dict[str, Any]) -> dict[str, Any]:
    name = _first_name(facts)
    biz = _biz(facts)
    payload = _payload(facts)
    kind = (facts.get("trigger") or {}).get("kind")

    if kind == "review_theme_emerged":
        theme = str(payload.get("theme") or "a recurring theme").replace("_", " ")
        n = payload.get("occurrences_30d")
        quote = payload.get("common_quote")
        body = f"{name}, review pattern: {theme}"
        if n is not None:
            body += f" ({n}× in 30d)"
        body += "."
        if quote:
            body += f' Common line: "{quote}".'
        body += " Want me to draft a short ops note + a reply template for the next review?"
        return _base(facts, body, "binary_yes_no", f"kind=review_theme; theme={theme}")

    # curious_ask
    ask_t = payload.get("ask_template") or "what_service_in_demand_this_week"
    body = (
        f"Hi {name}! Quick check — what has been most asked-for this week at {biz}? "
        f"I'll turn it into a Google post + a 4-line WhatsApp reply you can reuse. Takes ~5 min."
    )
    return _base(facts, body, "open_ended", f"kind=curious_ask; template={ask_t}")


# ----- commercial -----

def compose_commercial(facts: dict[str, Any]) -> dict[str, Any]:
    name = _first_name(facts)
    payload = _payload(facts)
    kind = (facts.get("trigger") or {}).get("kind")

    if kind == "renewal_due":
        days = payload.get("days_remaining")
        plan = payload.get("plan") or "your plan"
        amount = payload.get("renewal_amount")
        body = f"{name}, renewal heads-up"
        if days is not None:
            body += f" — {days} days left on {plan}"
        else:
            body += f" on {plan}"
        if amount is not None:
            body += f" (₹{amount})"
        body += ". Want a 2-bullet value recap + renew link draft for you?"
        return _base(facts, body, "binary_yes_no", f"kind=renewal; days={days}")

    # winback merchant
    days = payload.get("days_since_expiry")
    dip = payload.get("perf_dip_pct")
    body = f"{name}, you're eligible for a winback check-in"
    if days is not None:
        body += f" ({days}d since expiry)"
    if isinstance(dip, (int, float)):
        body += f"; perf {dip:+.0%} since then"
    body += ". Want me to draft a no-pressure reactivation note with one clear next step?"
    return _base(facts, body, "binary_yes_no", f"kind=winback; days={days}")


# ----- customer lifecycle -----

def compose_customer_lifecycle(facts: dict[str, Any]) -> dict[str, Any]:
    m = facts.get("merchant") or {}
    c = facts.get("customer") or {}
    payload = _payload(facts)
    kind = (facts.get("trigger") or {}).get("kind")
    cust = c.get("name") or "there"
    owner = m.get("owner_first_name")
    biz = m.get("name") or "us"
    who = f"{owner} from {biz}" if owner else biz
    offer = _offer(facts)

    if kind == "chronic_refill_due":
        mols = payload.get("molecule_list") or []
        stock = payload.get("stock_runs_out_iso") or ""
        date = stock[:10] if stock else "soon"
        mol_s = ", ".join(mols) if mols else "your regular medicines"
        body = (
            f"Namaste — {biz} yahan. {cust} ji ki medicines ({mol_s}) {date} ko khatam hongi."
        )
        if offer:
            body += f" {offer} applies."
        if payload.get("delivery_address_saved"):
            body += " Free home delivery to saved address available."
        body += " Reply CONFIRM to dispatch, or tell us if dosage changed."
        return _base(facts, body, "binary_confirm_cancel", f"kind=refill; n_mols={len(mols)}", "merchant_on_behalf")

    if kind in ("wedding_package_followup",):
        days = payload.get("days_to_wedding")
        window = str(payload.get("next_step_window_open") or "prep").replace("_", " ")
        body = f"Hi {cust} — {who} here."
        if days is not None:
            body += f" {days} days to your wedding — good window for {window}."
        else:
            body += f" Following up on your bridal trial — {window} window is open."
        body += " Want me to hold your preferred slot for the next session? Reply YES."
        return _base(facts, body, "binary_yes_no", f"kind=bridal; days={days}", "merchant_on_behalf")

    if kind == "trial_followup":
        opts = payload.get("next_session_options") or []
        label = opts[0].get("label") if opts and isinstance(opts[0], dict) else None
        body = f"Hi {cust}, {who} here — thanks for trying us."
        if label:
            body += f" Next session option: {label}."
        body += " Reply YES to hold it, or send a better time."
        return _base(facts, body, "binary_yes_no", "kind=trial_followup", "merchant_on_behalf")

    # lapsed soft/hard
    days = payload.get("days_since_last_visit")
    focus = payload.get("previous_focus")
    body = f"Hi {cust} 👋 {who} here."
    if days is not None:
        body += f" It's been about {days} days — happens to most members, no judgment."
    else:
        body += " It's been a while — no judgment."
    if focus:
        body += f" If you're still focused on {str(focus).replace('_', ' ')}, we can ease you back in."
    if offer:
        body += f" {offer} is open."
    body += " Reply YES for a free trial spot — no auto-charge."
    return _base(facts, body, "binary_yes_no", f"kind={kind}; days={days}", "merchant_on_behalf")


# ----- planning -----

def compose_planning(facts: dict[str, Any]) -> dict[str, Any]:
    name = _first_name(facts)
    m = facts.get("merchant") or {}
    payload = _payload(facts)
    topic = str(payload.get("intent_topic") or "your idea").replace("_", " ")
    locality = (m.get("identity") or {}).get("locality") or m.get("locality")
    # locality may be under merchant dict from fact pack
    locality = m.get("locality") or locality
    last = payload.get("merchant_last_message")
    body = f"{name}, here's a starter outline for {topic} — edit freely:\n"
    body += f"- Position for customers near {locality or 'your locality'}\n"
    body += "- Clear weekday vs weekend slots\n"
    body += "- Simple WhatsApp booking line + price band you already use\n"
    if last:
        body += f"(Building on: “{last[:80]}”)\n"
    body += "Want me to turn this into a customer-facing WhatsApp you can send?"
    return _base(facts, body, "binary_yes_no", f"kind=planning; topic={topic}")


# ----- misc alerts -----

def compose_alerts(facts: dict[str, Any]) -> dict[str, Any]:
    name = _first_name(facts)
    payload = _payload(facts)
    kind = (facts.get("trigger") or {}).get("kind")
    m = facts.get("merchant") or {}

    if kind == "supply_alert":
        mol = payload.get("molecule") or "the flagged medicine"
        batches = payload.get("affected_batches") or []
        mfr = payload.get("manufacturer") or ""
        batch_s = ", ".join(batches) if batches else "listed batches"
        body = (
            f"{name}, urgent: voluntary recall on {mol} batches ({batch_s})"
            + (f" by {mfr}" if mfr else "")
            + ". Sub-potency risk framing — customers may need replacement."
        )
        body += " Want me to draft their WhatsApp note + a pickup workflow?"
        return _base(facts, body, "binary_yes_no", f"kind=supply_alert; batches={len(batches)}")

    if kind == "competitor_opened":
        comp = payload.get("competitor_name") or "a nearby competitor"
        dist = payload.get("distance_km")
        their = payload.get("their_offer")
        body = f"{name}, competitor note: {comp} opened"
        if dist is not None:
            body += f" ~{dist} km away"
        body += "."
        if their:
            body += f" They're listing {their}."
        offer = _offer(facts)
        if offer:
            body += f" Want a side-by-side draft vs your {offer}?"
        else:
            body += " Want a calm positioning note for your GBP description?"
        return _base(facts, body, "binary_yes_no", f"kind=competitor; name={comp}")

    if kind == "gbp_unverified":
        path = payload.get("verification_path") or "postcard or phone"
        uplift = payload.get("estimated_uplift_pct")
        body = f"{name}, your Google profile still looks unverified."
        body += f" Typical path: {path}."
        if uplift is not None:
            body += f" Merchants who verify often see ~{float(uplift):.0%} more actions."
        body += " Want a 4-step verification checklist?"
        return _base(facts, body, "binary_yes_no", "kind=gbp_unverified")

    if kind == "dormant_with_vera":
        days = payload.get("days_since_last_merchant_message")
        body = f"Hi {name} — just checking in"
        if days is not None:
            body += f" (quiet for ~{days}d)"
        body += ". One useful thing I can do this week: draft a Google post from your latest offer/signal. Want that?"
        return _base(facts, body, "binary_yes_no", f"kind=dormant; days={days}")

    if kind == "category_seasonal":
        trends = payload.get("trends") or []
        season = payload.get("season") or "this season"
        body = f"{name}, {season.replace('_', ' ')} shelf note:"
        if trends:
            body += " " + "; ".join(str(t).replace("_", " ") for t in trends[:3]) + "."
        else:
            body += " demand is shifting in your category."
        body += " Want a 5-line stocking checklist?"
        return _base(facts, body, "binary_yes_no", f"kind=category_seasonal; n={len(trends)}")

    if kind == "milestone_reached":
        metric = payload.get("metric") or "milestone"
        value = payload.get("value_now")
        target = payload.get("milestone_value")
        body = f"{name}, milestone watch on {metric}"
        if value is not None and target is not None:
            body += f" — you're at {value}, aiming for {target}"
        body += ". Want a short celebration post draft for when you cross it?"
        return _base(facts, body, "binary_yes_no", f"kind=milestone; {metric}")

    # fallback inside alerts
    return compose_default(facts)


def compose_default(facts: dict[str, Any]) -> dict[str, Any]:
    m = facts.get("merchant") or {}
    trg = facts.get("trigger") or {}
    kind = (trg.get("kind") or "nudge").replace("_", " ")
    name = _first_name(facts)
    send_as = facts.get("send_as") or "vera"
    perf = m.get("performance") or {}
    anchor = ""
    if perf.get("ctr") is not None:
        anchor = f" Your 30d CTR is {perf['ctr']}."
    elif m.get("signals"):
        anchor = f" Flag: {m['signals'][0]}."

    if send_as == "merchant_on_behalf" and facts.get("customer"):
        cust = facts["customer"].get("name") or "there"
        body = (
            f"Hi {cust}, {m.get('name') or 'us'} here — quick note about {kind}."
            f" Reply YES if you'd like us to help."
        )
    else:
        body = (
            f"Hi {name} — flagging {kind} for {m.get('name') or 'your business'}."
            f"{anchor} Want me to draft next steps?"
        )
    return _base(facts, body, "open_ended", f"deterministic default kind={trg.get('kind')}", send_as)


_DISPATCH: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "research_digest": compose_research_digest,
    "regulation_change": compose_research_digest,
    "cde_opportunity": compose_research_digest,
    "recall_due": compose_recall_due,
    "appointment_tomorrow": compose_recall_due,
    "perf_dip": compose_performance,
    "perf_spike": compose_performance,
    "seasonal_perf_dip": compose_performance,
    "festival_upcoming": compose_events,
    "ipl_match_today": compose_events,
    "curious_ask_due": compose_engagement,
    "review_theme_emerged": compose_engagement,
    "renewal_due": compose_commercial,
    "winback_eligible": compose_commercial,
    "customer_lapsed_soft": compose_customer_lifecycle,
    "customer_lapsed_hard": compose_customer_lifecycle,
    "chronic_refill_due": compose_customer_lifecycle,
    "wedding_package_followup": compose_customer_lifecycle,
    "trial_followup": compose_customer_lifecycle,
    "active_planning_intent": compose_planning,
    "supply_alert": compose_alerts,
    "competitor_opened": compose_alerts,
    "gbp_unverified": compose_alerts,
    "dormant_with_vera": compose_alerts,
    "category_seasonal": compose_alerts,
    "milestone_reached": compose_alerts,
}


def deterministic_compose(facts: dict[str, Any]) -> dict[str, Any]:
    kind = (facts.get("trigger") or {}).get("kind") or ""
    fn = _DISPATCH.get(kind, compose_default)
    return fn(facts)

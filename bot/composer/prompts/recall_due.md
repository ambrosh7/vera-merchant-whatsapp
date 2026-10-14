## Kind: recall_due / appointment_tomorrow

send_as = merchant_on_behalf (message from the merchant's clinic/salon to their customer).

Compose a short WhatsApp that:
1. Greets customer.name; attributes from merchant.name / owner.
2. States the recall/appointment reason using trigger.payload (service_due, last_service_date, due_date).
3. Honors customer.language_pref (hi-en mix → natural code-mix).
4. Offers only available_slots from trigger.payload — never invent times.
5. Mentions an active offer title/price only if present in merchant.active_offers.
6. Respects consent.scope — only recall/appointment framing.
7. CTA: multi_choice_slot or binary_yes_no; keep booking friction low.
8. Warm-clinical / category-appropriate; no medical overclaims; respect vocab_taboo.

Do not invent slots, prices, or phone numbers.

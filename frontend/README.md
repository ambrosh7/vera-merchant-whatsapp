# Vera Lab (interactive frontend)

Interactive demo of what the magicpin challenge asks for:

`compose(category, merchant, trigger, customer?) → WhatsApp message`

## Run

1. Start the bot (Docker or uvicorn) on port **8080**
2. Start the UI:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

Vite proxies `/v1/*` → `http://127.0.0.1:8080`.

## What you can do

- One-click **case scenarios** (research digest, recall, compliance, …)
- Edit the **4 contexts** (category / merchant / trigger / customer)
- **Compose** via live bot (`POST /v1/demo/compose`)
- Review output against the **5-dimension judge rubric**
- See the exact JSON the contest cares about

This UI is for demos / understanding / reuse — the contest scores the bot, not the screens.

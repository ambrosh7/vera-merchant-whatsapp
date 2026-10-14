export type Scenario = {
  id: string
  title: string
  blurb: string
  category_slug: string
  merchant_id: string
  trigger_id: string
  customer_id: string | null
}

export type Catalog = {
  scenarios: Scenario[]
  categories: { slug: string; tone?: string }[]
  merchants: {
    merchant_id: string
    category_slug: string
    label: string
    owner?: string
    city?: string
  }[]
  triggers: {
    id: string
    kind: string
    scope: string
    urgency: number
    label: string
    merchant_id?: string
  }[]
  customers: {
    customer_id: string
    label: string
    language_pref?: string
    merchant_hint?: string | null
  }[]
}

export type ComposeResult = {
  body: string
  cta: string
  send_as: string
  suppression_key: string
  rationale: string
  template_name?: string
  template_params?: string[]
  contexts: Record<string, unknown>
}

/** Local `npm run dev` proxies `/v1` to the bot. Production calls Railway directly. */
const API_BASE = (
  import.meta.env.VITE_API_BASE ??
  (import.meta.env.DEV
    ? ''
    : 'https://vera-merchant-whatsapp-production.up.railway.app')
).replace(/\/$/, '')

function apiUrl(path: string): string {
  return `${API_BASE}${path}`
}

async function getJson<T>(path: string): Promise<T> {
  const url = apiUrl(path)
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${path} → ${res.status}`)
  return res.json() as Promise<T>
}

export async function fetchCatalog(): Promise<Catalog> {
  return getJson<Catalog>('/v1/demo/catalog')
}

export async function composeDemo(input: {
  category_slug: string
  merchant_id: string
  trigger_id: string
  customer_id?: string | null
}): Promise<ComposeResult> {
  const res = await fetch(apiUrl('/v1/demo/compose'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      category_slug: input.category_slug,
      merchant_id: input.merchant_id,
      trigger_id: input.trigger_id,
      customer_id: input.customer_id || null,
    }),
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(detail || `compose failed (${res.status})`)
  }
  return res.json() as Promise<ComposeResult>
}

export async function fetchHealth(): Promise<{ status: string; uptime_seconds: number }> {
  return getJson('/v1/healthz')
}

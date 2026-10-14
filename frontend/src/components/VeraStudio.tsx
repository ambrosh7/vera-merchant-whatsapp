import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Check,
  CheckCheck,
  ChevronDown,
  Coffee,
  Loader2,
  MapPin,
  Mic,
  Paperclip,
  Scissors,
  Send,
  SkipForward,
  Smile,
  Sparkles,
  Stethoscope,
  User,
  Wand2,
} from 'lucide-react'
import {
  composeDemo,
  fetchCatalog,
  fetchHealth,
  type Catalog,
  type ComposeResult,
  type Scenario,
} from '../lib/api'

type DraftStatus = 'ready' | 'sending' | 'sent' | 'skipped'
type ChatLine =
  | { id: string; kind: 'out'; text: string; ticks: 1 | 2 }
  | { id: string; kind: 'in'; text: string }
  | { id: string; kind: 'typing' }

const COPY: Record<
  string,
  { title: string; subtitle: string; why: string; reply: string }
> = {
  case_research_digest: {
    title: 'Share a clinical update',
    subtitle: 'New research your patients may care about',
    why: 'A fresh JIDA paper lines up with Meera’s high-risk adult cohort — worth a 2-minute share before peers circulate it.',
    reply: 'Yes, send the abstract — I’ll share with the team.',
  },
  case_recall_priya: {
    title: 'Book a recall visit',
    subtitle: 'Priya is due for her cleaning',
    why: 'Priya’s 6-month cleaning window opened. Two evening slots are held — a short WhatsApp usually books one.',
    reply: 'YES — Wed 5 Nov works for me 👍',
  },
  case_regulation: {
    title: 'Prep for compliance',
    subtitle: 'Radiograph rules before the Dec deadline',
    why: 'DCI dose limits change Dec 15. Clinics that prep SOPs now skip the last-week scramble.',
    reply: 'Please draft the SOP. Need it this week.',
  },
  case_salon_wedding: {
    title: 'Wedding package follow-up',
    subtitle: 'Stay close to a bridal client',
    why: 'Kavya loved her bridal trial. Skin prep opens now — warm follow-up locks the package.',
    reply: 'Yes please book the skin prep!',
  },
  case_curious_ask: {
    title: "Ask what's working",
    subtitle: 'A light check-in that gets a reply',
    why: 'Quiet week for ops alerts. A curious ask keeps the cafe relationship warm without selling.',
    reply: 'Filter coffee is selling crazy this week ☕',
  },
}

const CATS = [
  { id: 'dentists', label: 'Clinic', accent: 'var(--color-clinic)', Icon: Stethoscope },
  { id: 'salons', label: 'Salon', accent: 'var(--color-salon)', Icon: Scissors },
  { id: 'restaurants', label: 'Cafes', accent: 'var(--color-cafe)', Icon: Coffee },
] as const

function meta(s: Scenario) {
  return (
    COPY[s.id] || {
      title: s.title,
      subtitle: s.blurb,
      why: 'Vera spotted a timely reason to message.',
      reply: 'Sounds good — tell me more.',
    }
  )
}

function formatDraft(body: string): string {
  const t = body.trim()
  if (t.includes('\n')) return t
  return t
    .replace(/ — /g, '\n\n')
    .replace(/\. (?=[A-Z0-9₹])/g, '.\n\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

function shortName(label: string) {
  return label.split('·')[0].trim()
}

function wait(ms: number) {
  return new Promise((r) => window.setTimeout(r, ms))
}

export function VeraStudio() {
  const [catalog, setCatalog] = useState<Catalog | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [scenarioId, setScenarioId] = useState('')
  const [merchantId, setMerchantId] = useState('')
  const [result, setResult] = useState<ComposeResult | null>(null)
  const [draft, setDraft] = useState('')
  const [toast, setToast] = useState<string | null>(null)
  const [draftKey, setDraftKey] = useState(0)
  const [editing, setEditing] = useState(false)
  const [statuses, setStatuses] = useState<Record<string, DraftStatus>>({})
  const [open, setOpen] = useState<Record<string, boolean>>({
    dentists: true,
    salons: true,
    restaurants: true,
  })
  const [chat, setChat] = useState<ChatLine[]>([])
  const [busy, setBusy] = useState(false)
  const [celebrate, setCelebrate] = useState(false)
  const chatEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  function flash(msg: string) {
    setToast(msg)
    window.setTimeout(() => setToast(null), 2000)
  }

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const [cat] = await Promise.all([fetchCatalog(), fetchHealth()])
        if (cancelled) return
        setCatalog(cat)
        const first = cat.scenarios[0]
        if (first) {
          setScenarioId(first.id)
          setMerchantId(first.merchant_id)
        }
      } catch (e) {
        if (!cancelled) {
          setError(
            e instanceof Error ? e.message : 'Vera is offline. Start the API on port 8080.',
          )
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const scenario = useMemo(
    () => catalog?.scenarios.find((s) => s.id === scenarioId) || null,
    [catalog, scenarioId],
  )
  const merchant = useMemo(
    () => catalog?.merchants.find((m) => m.merchant_id === merchantId) || null,
    [catalog, merchantId],
  )
  const queue = useMemo(() => catalog?.scenarios || [], [catalog])

  const sections = useMemo(() => {
    if (!catalog) return []
    return CATS.map((cat) => {
      const scenarios = catalog.scenarios.filter((s) => s.category_slug === cat.id)
      const stores = new Map<string, Scenario[]>()
      for (const s of scenarios) {
        const list = stores.get(s.merchant_id) || []
        list.push(s)
        stores.set(s.merchant_id, list)
      }
      return {
        ...cat,
        scenarios,
        stores: [...stores.entries()].map(([id, scs]) => {
          const m = catalog.merchants.find((x) => x.merchant_id === id)
          return {
            id,
            name: shortName(m?.label || id),
            city: m?.city || '',
            scenarios: scs,
          }
        }),
      }
    }).filter((s) => s.scenarios.length > 0)
  }, [catalog])

  const progress = useMemo(() => {
    const done = queue.filter((s) => {
      const st = statuses[s.id]
      return st === 'sent' || st === 'skipped'
    }).length
    return { done, total: queue.length, pct: queue.length ? (done / queue.length) * 100 : 0 }
  }, [queue, statuses])

  useEffect(() => {
    if (!catalog || !scenario) return
    let cancelled = false
    ;(async () => {
      setLoading(true)
      setError(null)
      setEditing(false)
      setChat([])
      try {
        const out = await composeDemo({
          category_slug: scenario.category_slug,
          merchant_id: scenario.merchant_id,
          trigger_id: scenario.trigger_id,
          customer_id: scenario.customer_id,
        })
        if (cancelled) return
        setResult(out)
        setDraft(formatDraft(out.body))
        setMerchantId(scenario.merchant_id)
        setDraftKey((k) => k + 1)
        setStatuses((prev) =>
          prev[scenario.id] && prev[scenario.id] !== 'ready'
            ? prev
            : { ...prev, [scenario.id]: 'ready' },
        )
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : 'Could not draft message')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [catalog, scenarioId]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chat])

  function selectScenario(s: Scenario) {
    if (busy) return
    setScenarioId(s.id)
    setMerchantId(s.merchant_id)
    setOpen((prev) => ({ ...prev, [s.category_slug]: true }))
  }

  function nextReady(fromId: string): Scenario | null {
    const idx = queue.findIndex((s) => s.id === fromId)
    for (let i = 1; i <= queue.length; i++) {
      const s = queue[(idx + i) % queue.length]
      const st = statuses[s.id]
      if (!st || st === 'ready') return s
    }
    return null
  }

  async function regenerate() {
    if (!scenario || busy) return
    setLoading(true)
    setChat([])
    try {
      const out = await composeDemo({
        category_slug: scenario.category_slug,
        merchant_id: scenario.merchant_id,
        trigger_id: scenario.trigger_id,
        customer_id: scenario.customer_id,
      })
      setResult(out)
      setDraft(formatDraft(out.body))
      setStatuses((p) => ({ ...p, [scenario.id]: 'ready' }))
      setDraftKey((k) => k + 1)
      flash('Rewritten')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not draft message')
    } finally {
      setLoading(false)
    }
  }

  async function sendMessage() {
    if (!scenario || !draft.trim() || busy || loading) return
    const current = scenario
    const text = draft.trim()
    const replyText = meta(current).reply
    setBusy(true)
    setEditing(false)
    setStatuses((p) => ({ ...p, [current.id]: 'sending' }))
    const outId = `o-${Date.now()}`
    setChat([{ id: outId, kind: 'out', text, ticks: 1 }])
    await wait(400)
    setChat([{ id: outId, kind: 'out', text, ticks: 2 }])
    setStatuses((p) => ({ ...p, [current.id]: 'sent' }))
    await wait(650)
    setChat((p) => [...p, { id: `t-${outId}`, kind: 'typing' }])
    await wait(1000)
    setChat((p) => [
      ...p.filter((l) => l.kind !== 'typing'),
      { id: `i-${outId}`, kind: 'in', text: replyText },
    ])
    flash('They replied')
    await wait(850)
    const nxt = nextReady(current.id)
    setBusy(false)
    if (nxt) {
      selectScenario(nxt)
    } else {
      setCelebrate(true)
      flash('Inbox clear')
      window.setTimeout(() => setCelebrate(false), 1600)
    }
  }

  function skipMessage() {
    if (!scenario || busy) return
    setStatuses((p) => ({ ...p, [scenario.id]: 'skipped' }))
    setChat([])
    const nxt = nextReady(scenario.id)
    if (nxt) selectScenario(nxt)
    else {
      setCelebrate(true)
      flash('Inbox clear')
      window.setTimeout(() => setCelebrate(false), 1600)
    }
  }

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const tag = (e.target as HTMLElement)?.tagName
      const inField = tag === 'TEXTAREA' || tag === 'INPUT'
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault()
        void sendMessage()
        return
      }
      if (inField || busy) return
      if (e.key === 'e') {
        setEditing(true)
        window.setTimeout(() => textareaRef.current?.focus(), 0)
      } else if (e.key === 'r') void regenerate()
      else if (e.key === 's') skipMessage()
      else if (e.key === 'ArrowDown' || e.key === 'j') {
        const i = queue.findIndex((x) => x.id === scenarioId)
        const n = queue[Math.min(queue.length - 1, i + 1)]
        if (n) selectScenario(n)
      } else if (e.key === 'ArrowUp' || e.key === 'k') {
        const i = queue.findIndex((x) => x.id === scenarioId)
        const n = queue[Math.max(0, i - 1)]
        if (n) selectScenario(n)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [scenarioId, queue, busy, loading, draft]) // eslint-disable-line react-hooks/exhaustive-deps

  if (error && !catalog) {
    return (
      <div className="vera-app flex min-h-screen items-center justify-center px-6">
        <div className="animate-pop panel max-w-md rounded-2xl p-8 text-center shadow-sm">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-teal font-display text-lg font-bold text-lime">
            V
          </div>
          <h1 className="font-display text-xl font-bold">Vera is offline</h1>
          <p className="mt-2 text-sm text-ink-muted">{error}</p>
        </div>
      </div>
    )
  }

  if (!catalog || !scenario || !merchant) {
    return (
      <div className="vera-app flex min-h-screen items-center justify-center text-ink-muted">
        <Loader2 className="animate-spin" />
      </div>
    )
  }

  const m = meta(scenario)
  const cat = CATS.find((c) => c.id === scenario.category_slug) || CATS[0]
  const CatIcon = cat.Icon
  const sendAs =
    result?.send_as === 'merchant_on_behalf' ? shortName(merchant.label) : 'Vera'
  const st = statuses[scenario.id] || 'ready'
  const customerName = String(result?.contexts?.customer_name || '')
  const locality = String(result?.contexts?.locality || merchant.city || '')
  return (
    <div className="vera-app relative flex h-dvh max-h-dvh flex-col overflow-hidden text-ink">
      {celebrate && <Confetti />}

      <header className="relative z-10 flex shrink-0 items-center justify-between gap-3 px-4 py-2.5 md:px-6">
        <div className="flex items-center gap-2.5">
          <div className="animate-glow flex h-9 w-9 items-center justify-center rounded-[12px] bg-lime">
            <span className="font-display text-base font-bold leading-none text-teal-deep">V</span>
          </div>
          <div>
            <div className="font-display text-xl font-bold leading-none tracking-tight">Vera</div>
            <div className="mt-0.5 text-[10px] font-medium text-ink-muted">
              WhatsApp for merchants · magicpin
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden items-center gap-2 rounded-full border border-hairline bg-chalk/80 px-2.5 py-1 text-[10px] font-semibold text-ink-muted sm:flex">
            <span className="live-dot h-1.5 w-1.5 rounded-full bg-teal" />
            Live
          </div>
          <div className="relative flex h-9 w-9 items-center justify-center">
            <svg width="36" height="36" className="-rotate-90">
              <circle
                cx="18"
                cy="18"
                r="14"
                fill="none"
                stroke="var(--color-hairline)"
                strokeWidth="2.5"
              />
              <circle
                cx="18"
                cy="18"
                r="14"
                fill="none"
                stroke="var(--color-teal)"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeDasharray={2 * Math.PI * 14}
                strokeDashoffset={2 * Math.PI * 14 - (2 * Math.PI * 14 * progress.pct) / 100}
                className="transition-all duration-500"
              />
            </svg>
            <span className="absolute font-mono-data text-[9px] font-bold text-teal">
              {progress.done}/{progress.total}
            </span>
          </div>
        </div>
      </header>

      <div className="relative z-10 mx-auto grid min-h-0 w-full max-w-[1600px] flex-1 gap-4 px-3 pb-3 md:px-5 lg:grid-cols-[minmax(300px,1.05fr)_minmax(0,1.15fr)_minmax(280px,0.95fr)] lg:gap-5 lg:px-6 lg:pb-4">
        {/* LEFT — Clinic / Salon / Cafes */}
        <aside className="animate-rise order-2 flex min-h-0 flex-col gap-2.5 overflow-y-auto lg:order-1">
          {sections.map((sec, i) => {
            const Icon = sec.Icon
            const isOpen = open[sec.id] !== false
            const activeHere = scenario.category_slug === sec.id
            const done = sec.scenarios.filter((s) => {
              const x = statuses[s.id]
              return x === 'sent' || x === 'skipped'
            }).length
            return (
              <div
                key={sec.id}
                className={[
                  'panel overflow-hidden rounded-2xl shadow-sm transition duration-300',
                  activeHere
                    ? 'ring-2 ring-teal/25 shadow-[0_12px_32px_rgba(15,61,58,0.08)]'
                    : '',
                ].join(' ')}
                style={{ animationDelay: `${i * 60}ms` }}
              >
                <button
                  type="button"
                  onClick={() => {
                    setOpen((p) => ({ ...p, [sec.id]: !isOpen }))
                    const first = sec.scenarios[0]
                    if (first && !activeHere && !isOpen) selectScenario(first)
                  }}
                  className="flex w-full items-center gap-3 px-3.5 py-3 text-left"
                >
                  <span
                    className="flex h-10 w-10 items-center justify-center rounded-xl text-chalk"
                    style={{ background: sec.accent }}
                  >
                    <Icon size={18} />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="font-display text-lg font-bold tracking-tight">
                      {sec.label}
                    </div>
                    <div className="text-[11px] text-ink-muted">
                      {sec.scenarios.length} ready
                      {done ? ` · ${done} done` : ''}
                    </div>
                  </div>
                  <ChevronDown
                    size={16}
                    className={[
                      'text-ink-disabled transition',
                      isOpen ? 'rotate-0' : '-rotate-90',
                    ].join(' ')}
                  />
                </button>

                {isOpen && (
                  <div className="space-y-2.5 border-t border-hairline px-2 pb-3 pt-2">
                    {sec.stores.map((store) => (
                      <div key={store.id}>
                        <div className="mb-1 flex items-center gap-1.5 px-2 text-[10px] font-bold uppercase tracking-[0.12em] text-ink-disabled">
                          <MapPin size={10} />
                          <span className="truncate">
                            {store.name}
                            {store.city ? ` · ${store.city}` : ''}
                          </span>
                        </div>
                        <div className="space-y-1">
                          {store.scenarios.map((s) => {
                            const c = meta(s)
                            const active = s.id === scenarioId
                            const sst = statuses[s.id] || 'ready'
                            return (
                              <button
                                key={s.id}
                                type="button"
                                disabled={busy}
                                onClick={() => selectScenario(s)}
                                className={[
                                  'w-full rounded-xl px-3 py-2.5 text-left transition',
                                  active
                                    ? 'bg-lime text-teal-deep shadow-[0_8px_20px_rgba(200,241,53,0.28)]'
                                    : 'hover:bg-sunken/70',
                                  busy && !active ? 'opacity-40' : '',
                                ].join(' ')}
                              >
                                <div className="flex items-start justify-between gap-2">
                                  <span className="text-[13px] font-bold leading-snug">
                                    {c.title}
                                  </span>
                                  <Dot status={sst} active={active} />
                                </div>
                                <p
                                  className={[
                                    'mt-0.5 text-[11px] leading-snug',
                                    active ? 'text-teal-deep/70' : 'text-ink-muted',
                                  ].join(' ')}
                                >
                                  {c.subtitle}
                                </p>
                              </button>
                            )
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </aside>

        {/* CENTER — Phone */}
        <main className="animate-fade order-1 flex min-h-0 flex-col lg:order-2">
          <div className="mb-2 flex shrink-0 flex-wrap items-center justify-between gap-2">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <span
                  className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold text-chalk"
                  style={{ background: cat.accent }}
                >
                  <CatIcon size={11} />
                  {cat.label}
                </span>
                <span className="truncate text-[11px] font-semibold text-ink-muted">
                  {shortName(merchant.label)}
                </span>
              </div>
              <h1 className="mt-1 font-display text-xl font-bold leading-tight tracking-tight md:text-[1.5rem]">
                {m.title}
              </h1>
            </div>
            <button
              type="button"
              onClick={() => void regenerate()}
              disabled={loading || busy}
              className="flex shrink-0 items-center gap-1 rounded-full border border-hairline bg-chalk px-2.5 py-1 text-[11px] font-bold text-teal transition hover:bg-lime-soft disabled:opacity-40"
            >
              {loading ? <Loader2 size={12} className="animate-spin" /> : <Wand2 size={12} />}
              Rewrite
            </button>
          </div>

          <div className="relative mx-auto flex min-h-0 w-full max-w-[340px] flex-1 flex-col">
            <div className="animate-pop relative flex min-h-0 flex-1 flex-col overflow-hidden rounded-[28px] border-[2.5px] border-teal-deep/90 bg-teal-deep shadow-[0_20px_40px_rgba(11,31,36,0.14)]">
              <div className="absolute left-1/2 top-2 z-20 h-[18px] w-[92px] -translate-x-1/2 rounded-full bg-black/50" />

              <div className="flex shrink-0 items-center gap-2.5 bg-wa px-3 pb-2 pt-7 text-chalk">
                <div
                  className="flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold text-chalk"
                  style={{ background: cat.accent }}
                >
                  {sendAs.charAt(0)}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-[13px] font-semibold">{sendAs}</div>
                  <div className="text-[10px] text-chalk/65">
                    {busy ? 'typing…' : 'online'}
                  </div>
                </div>
                {st === 'sent' && (
                  <span className="rounded-full bg-lime/20 px-2 py-0.5 text-[9px] font-bold text-lime">
                    Sent
                  </span>
                )}
              </div>

              <div className="phone-wallpaper relative flex min-h-0 flex-1 flex-col overflow-y-auto px-2.5 py-2">
                <div className="mb-2 self-center rounded-full bg-ink/10 px-2.5 py-0.5 text-[9px] font-semibold text-ink-muted">
                  Today
                </div>

                <div className="mt-auto flex flex-col gap-2">
                  {loading && !draft && chat.length === 0 && (
                    <div className="flex items-center gap-2 self-start rounded-2xl rounded-tl-sm bg-bubble-out px-3 py-2 text-xs text-ink-muted shadow-sm">
                      <Loader2 size={13} className="animate-spin text-teal" />
                      Vera is writing…
                    </div>
                  )}

                  {!loading && chat.length === 0 && draft && (
                    <div
                      key={draftKey}
                      className="animate-rise max-h-[42vh] max-w-[94%] cursor-text overflow-y-auto self-start rounded-2xl rounded-tl-sm bg-bubble-out px-3 py-2.5 text-ink shadow-sm"
                      onClick={() => {
                        if (st === 'ready') {
                          setEditing(true)
                          window.setTimeout(() => textareaRef.current?.focus(), 0)
                        }
                      }}
                    >
                      {editing ? (
                        <textarea
                          ref={textareaRef}
                          value={draft}
                          onChange={(e) => setDraft(e.target.value)}
                          onBlur={() => setEditing(false)}
                          rows={Math.min(8, Math.max(3, draft.split('\n').length + 1))}
                          className="w-full resize-none whitespace-pre-wrap bg-transparent text-[13px] leading-[1.45] outline-none"
                        />
                      ) : (
                        <p className="whitespace-pre-wrap text-[13px] leading-[1.45]">
                          {draft}
                        </p>
                      )}
                      <div className="mt-1 flex justify-between text-[8px] font-semibold uppercase tracking-wide text-ink-disabled">
                        <span>{editing ? 'Editing' : 'Tap to edit'}</span>
                        <span className="font-mono-data normal-case">{draft.length}</span>
                      </div>
                    </div>
                  )}

                  {chat.map((line) => {
                    if (line.kind === 'typing') {
                      return (
                        <div
                          key={line.id}
                          className="animate-rise flex items-center gap-1 self-end rounded-2xl rounded-tr-sm bg-bubble-in px-3 py-2 shadow-sm"
                        >
                          <span className="typing-dot" />
                          <span className="typing-dot" style={{ animationDelay: '0.15s' }} />
                          <span className="typing-dot" style={{ animationDelay: '0.3s' }} />
                        </div>
                      )
                    }
                    if (line.kind === 'out') {
                      return (
                        <div
                          key={line.id}
                          className="animate-rise max-h-[42vh] max-w-[94%] overflow-y-auto self-start rounded-2xl rounded-tl-sm bg-bubble-out px-3 py-2.5 text-ink shadow-sm"
                        >
                          <p className="whitespace-pre-wrap text-[13px] leading-[1.45]">
                            {line.text}
                          </p>
                          <div className="mt-1 flex items-center justify-end gap-1 text-[9px] text-ink-disabled">
                            <span>now</span>
                            {line.ticks === 2 ? (
                              <CheckCheck size={13} className="text-[#53bdeb]" />
                            ) : (
                              <Check size={13} />
                            )}
                          </div>
                        </div>
                      )
                    }
                    return (
                      <div
                        key={line.id}
                        className="animate-pop max-w-[86%] self-end rounded-2xl rounded-tr-sm bg-bubble-in px-3 py-2.5 text-ink shadow-sm"
                      >
                        <p className="text-[13px] leading-[1.45]">{line.text}</p>
                        <div className="mt-1 text-right text-[9px] text-ink-disabled">now</div>
                      </div>
                    )
                  })}
                  <div ref={chatEndRef} />
                </div>
              </div>

              <div className="flex shrink-0 items-center gap-1.5 bg-sunken px-2 py-1.5">
                <Smile size={16} className="text-ink-disabled" />
                <button
                  type="button"
                  disabled={busy || st === 'sent' || loading}
                  onClick={() => {
                    setEditing(true)
                    window.setTimeout(() => textareaRef.current?.focus(), 0)
                  }}
                  className="flex-1 truncate rounded-full bg-chalk px-3 py-1.5 text-left text-[12px] text-ink-muted ring-1 ring-hairline disabled:opacity-40"
                >
                  {st === 'sent' ? 'Message sent' : 'Edit message…'}
                </button>
                <Paperclip size={15} className="text-ink-disabled" />
                <button
                  type="button"
                  disabled={busy || loading || !draft.trim() || st === 'sent' || st === 'skipped'}
                  onClick={() => void sendMessage()}
                  className="flex h-8 w-8 items-center justify-center rounded-full bg-lime text-teal-deep transition hover:scale-105 active:scale-95 disabled:opacity-35"
                  aria-label="Send"
                >
                  {busy && st === 'sending' ? (
                    <Loader2 size={15} className="animate-spin" />
                  ) : (
                    <Send size={15} />
                  )}
                </button>
              </div>
            </div>
          </div>

          <div className="mx-auto mt-2 flex w-full max-w-[340px] shrink-0 gap-2">
            <button
              type="button"
              disabled={busy || loading || !draft.trim() || st === 'sent' || st === 'skipped'}
              onClick={() => void sendMessage()}
              className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-lime py-2.5 text-[13px] font-bold text-teal-deep shadow-[0_8px_20px_rgba(200,241,53,0.3)] transition hover:bg-lime-hover active:scale-[0.98] disabled:opacity-40"
            >
              <Send size={14} />
              Send on WhatsApp
            </button>
            <button
              type="button"
              disabled={busy || st === 'sent' || st === 'skipped'}
              onClick={skipMessage}
              className="flex items-center gap-1.5 rounded-xl border border-hairline bg-chalk px-3 py-2.5 text-[13px] font-semibold text-ink-muted transition hover:bg-sunken disabled:opacity-40"
            >
              <SkipForward size={14} />
              Skip
            </button>
          </div>
        </main>

        {/* RIGHT — Context */}
        <aside
          className="animate-rise order-3 hidden min-h-0 flex-col gap-3 overflow-y-auto lg:flex"
          style={{ animationDelay: '80ms' }}
        >
          <div className="panel rounded-2xl p-4 shadow-sm">
            <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.14em] text-ink-disabled">
              <Sparkles size={13} className="text-teal" />
              Why now
            </div>
            <p className="mt-2.5 text-[13px] leading-relaxed text-ink/90">{m.why}</p>
          </div>

          <div className="panel rounded-2xl p-4 shadow-sm">
            <div className="text-[11px] font-bold uppercase tracking-[0.14em] text-ink-disabled">
              Store
            </div>
            <div className="mt-3 flex items-center gap-3">
              <div
                className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl font-display text-base font-bold text-chalk"
                style={{ background: cat.accent }}
              >
                {shortName(merchant.label).charAt(0)}
              </div>
              <div className="min-w-0">
                <div className="truncate text-[14px] font-bold">
                  {shortName(merchant.label)}
                </div>
                <div className="truncate text-[12px] text-ink-muted">
                  {locality || merchant.category_slug}
                </div>
              </div>
            </div>
          </div>

          {customerName ? (
            <div className="panel rounded-2xl p-4 shadow-sm">
              <div className="text-[11px] font-bold uppercase tracking-[0.14em] text-ink-disabled">
                Recipient
              </div>
              <div className="mt-3 flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-full bg-sunken">
                  <User size={18} className="text-ink-muted" />
                </div>
                <div className="min-w-0">
                  <div className="truncate text-[14px] font-bold">{customerName}</div>
                  <div className="text-[12px] text-ink-muted">WhatsApp · opted in</div>
                </div>
              </div>
            </div>
          ) : (
            <div className="panel rounded-2xl p-4 shadow-sm">
              <div className="text-[11px] font-bold uppercase tracking-[0.14em] text-ink-disabled">
                Recipient
              </div>
              <div className="mt-3 flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-full bg-lime-soft">
                  <span className="font-display font-bold text-teal">V</span>
                </div>
                <div>
                  <div className="text-[14px] font-bold">Merchant owner</div>
                  <div className="text-[12px] text-ink-muted">Direct from Vera</div>
                </div>
              </div>
            </div>
          )}

          <div className="mt-auto rounded-2xl border border-dashed border-hairline bg-chalk/60 px-4 py-3 text-[11px] leading-relaxed text-ink-muted">
            <div className="mb-1.5 flex items-center gap-1.5 font-bold text-ink">
              <Mic size={12} /> Shortcuts
            </div>
            <kbd className="kbd">⌘</kbd>+<kbd className="kbd">↵</kbd> send ·{' '}
            <kbd className="kbd">E</kbd> edit · <kbd className="kbd">R</kbd> rewrite ·{' '}
            <kbd className="kbd">S</kbd> skip
          </div>
        </aside>
      </div>

      <div className="fixed bottom-0 left-0 right-0 z-20 border-t border-hairline bg-chalk/90 p-2 backdrop-blur lg:hidden">
        <div className="flex gap-2 overflow-x-auto">
          {sections.map((sec) => (
            <button
              key={sec.id}
              type="button"
              onClick={() => {
                const first = sec.scenarios[0]
                if (first) selectScenario(first)
              }}
              className={[
                'shrink-0 rounded-full px-3 py-1.5 text-xs font-bold',
                scenario.category_slug === sec.id
                  ? 'bg-teal text-chalk'
                  : 'bg-sunken text-ink-muted',
              ].join(' ')}
            >
              {sec.label}
            </button>
          ))}
        </div>
      </div>

      {error && catalog && (
        <div className="fixed bottom-20 left-1/2 z-50 -translate-x-1/2 rounded-xl bg-alert px-4 py-2 text-sm text-chalk shadow-lg">
          {error}
        </div>
      )}
      {toast && (
        <div className="animate-pop fixed bottom-20 left-1/2 z-50 -translate-x-1/2 rounded-xl bg-teal px-4 py-2.5 text-sm font-bold text-chalk shadow-lg lg:bottom-6">
          {toast}
        </div>
      )}
    </div>
  )
}

function Dot({ status, active }: { status: DraftStatus; active: boolean }) {
  if (status === 'sent') {
    return (
      <span
        className={[
          'mt-0.5 h-2 w-2 shrink-0 rounded-full',
          active ? 'bg-teal-deep' : 'bg-success',
        ].join(' ')}
      />
    )
  }
  if (status === 'skipped') {
    return <span className="mt-0.5 h-2 w-2 shrink-0 rounded-full bg-ink-disabled" />
  }
  if (status === 'sending') {
    return <Loader2 size={12} className="mt-0.5 shrink-0 animate-spin text-teal" />
  }
  return (
    <span
      className={[
        'mt-0.5 h-2 w-2 shrink-0 rounded-full',
        active ? 'bg-teal-deep/40' : 'bg-teal',
      ].join(' ')}
    />
  )
}

function Confetti() {
  const bits = Array.from({ length: 18 }, (_, i) => i)
  const colors = ['#c8f135', '#2a6f7a', '#b86b3c', '#9b5b7a', '#0f3d3a']
  return (
    <div className="pointer-events-none fixed inset-0 z-40 overflow-hidden">
      {bits.map((i) => (
        <span
          key={i}
          className="confetti-bit"
          style={{
            left: `${8 + ((i * 5.3) % 84)}%`,
            top: `${12 + (i % 5) * 8}%`,
            background: colors[i % colors.length],
            animationDelay: `${i * 0.04}s`,
          }}
        />
      ))}
    </div>
  )
}

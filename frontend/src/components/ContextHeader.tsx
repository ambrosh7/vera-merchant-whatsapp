import { History, PanelRight, Search } from 'lucide-react'

type Props = {
  onToggleInspector: () => void
  inspectorOpen: boolean
}

export function ContextHeader({ onToggleInspector, inspectorOpen }: Props) {
  return (
    <section className="relative z-20 flex items-center justify-between border-b border-hairline bg-chalk px-6 py-3">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-bold uppercase tracking-wider text-ink-disabled">
            Engagement Studio
          </span>
          <span className="text-xs text-ink-disabled">/</span>
          <span className="font-mono-data text-xs text-ink-muted">Session #4902</span>
        </div>
        <div className="mt-0.5 flex flex-wrap items-baseline gap-2">
          <h1 className="font-display truncate text-lg font-bold tracking-tight text-ink">
            Dentists → Dr. Meera&apos;s Dental Clinic
          </h1>
          <span className="font-mono-data text-xs font-medium text-ink-muted">
            · Active trigger · Research digest · ctx v3 · synced 2m ago
          </span>
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-2">
        <div className="flex items-center gap-2 rounded-full bg-sunken/80 px-3 py-1.5">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-lime opacity-75" />
            <span className="live-dot relative inline-flex h-2 w-2 rounded-full bg-lime" />
          </span>
          <span className="text-xs font-semibold text-ink">Live · WhatsApp</span>
        </div>
        <button
          type="button"
          className="hidden items-center gap-1.5 rounded-[10px] bg-sunken px-3 py-1.5 text-xs font-semibold text-ink transition-colors hover:bg-hairline sm:flex"
        >
          <History size={14} />
          Audit trail
        </button>
        <button
          type="button"
          className="flex h-8 w-8 items-center justify-center rounded-[10px] bg-sunken text-ink-muted transition-colors hover:bg-hairline"
          aria-label="Search"
        >
          <Search size={16} />
        </button>
        <button
          type="button"
          onClick={onToggleInspector}
          className={[
            'flex h-8 w-8 items-center justify-center rounded-[10px] transition-colors xl:hidden',
            inspectorOpen ? 'bg-teal text-chalk' : 'bg-sunken text-ink-muted hover:bg-hairline',
          ].join(' ')}
          aria-label="Toggle inspector"
        >
          <PanelRight size={16} />
        </button>
      </div>
    </section>
  )
}

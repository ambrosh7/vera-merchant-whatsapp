import { ScanSearch, X } from 'lucide-react'
import type { ReactNode } from 'react'
import { contexts } from '../data/studio'

type Props = {
  open: boolean
  onClose: () => void
}

export function ContextInspector({ open, onClose }: Props) {
  return (
    <aside
      className={[
        'z-40 flex w-[360px] shrink-0 flex-col justify-between border-l border-hairline bg-chalk',
        'fixed inset-y-0 right-0 shadow-[-8px_0_24px_rgba(15,28,46,0.08)] transition-transform xl:static xl:translate-x-0 xl:shadow-none',
        open ? 'translate-x-0' : 'translate-x-full xl:translate-x-0',
      ].join(' ')}
    >
      <div className="border-b border-hairline p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ScanSearch size={18} className="text-teal" />
            <h2 className="font-display text-base font-bold text-ink">4-Context Inspector</h2>
          </div>
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-sunken px-2 py-0.5 font-mono-data text-[11px] font-bold text-ink">
              STRICT
            </span>
            <button
              type="button"
              onClick={onClose}
              className="flex h-7 w-7 items-center justify-center rounded-[8px] text-ink-muted hover:bg-sunken xl:hidden"
              aria-label="Close inspector"
            >
              <X size={16} />
            </button>
          </div>
        </div>
        <p className="mt-1 truncate font-mono-data text-[11px] text-ink-muted">
          compose(category, merchant, trigger, customer?)
        </p>
      </div>

      <div className="flex flex-1 flex-col gap-4 overflow-y-auto p-4">
        <InspectorCard accent="bg-sage" title={contexts.category.title} actionLabel="Use in compose">
          <p className="mt-1 text-[12px] text-ink-muted">
            <strong className="text-ink">Voice:</strong> {contexts.category.voice}
          </p>
          <div className="mt-2.5">
            <span className="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-ink-disabled">
              Catalog SKUs
            </span>
            <div className="flex flex-wrap gap-1">
              {contexts.category.offers.map((offer) => (
                <span
                  key={offer}
                  className={[
                    'rounded-[8px] bg-sunken px-2 py-0.5 font-mono-data text-[11px] text-ink',
                    offer.includes('199') ? 'font-semibold text-teal' : '',
                  ].join(' ')}
                >
                  {offer}
                </span>
              ))}
            </div>
          </div>
          <div className="mt-2 flex items-center justify-between border-t border-hairline pt-2 font-mono-data text-[11px] text-ink-muted">
            <span>{contexts.category.digest}</span>
            <span className="font-semibold text-success">Matched</span>
          </div>
        </InspectorCard>

        <InspectorCard accent="bg-ink" title={contexts.merchant.title} actionLabel="Use in compose">
          <p className="mt-0.5 font-mono-data text-[11px] text-ink-muted">
            {contexts.merchant.locality}
          </p>
          <div className="mt-2 grid grid-cols-2 gap-2 rounded-[10px] bg-sunken/70 p-2">
            <div>
              <span className="block font-mono-data text-[10px] uppercase text-ink-muted">
                Campaign CTR
              </span>
              <span className="font-mono-data text-xs font-bold text-ink">
                {contexts.merchant.ctr}{' '}
                <span className="text-[10px] font-normal text-ink-disabled">
                  (peer {contexts.merchant.peerCtr})
                </span>
              </span>
            </div>
            <div>
              <span className="block font-mono-data text-[10px] uppercase text-ink-muted">
                Adult Roster
              </span>
              <span className="font-mono-data text-xs font-bold text-ink">
                {contexts.merchant.roster}
              </span>
            </div>
          </div>
          <div className="mt-2 flex items-center gap-1.5 rounded-[8px] bg-alert/10 px-2 py-1 text-[11px] text-alert">
            <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-alert" />
            <span className="truncate font-semibold">{contexts.merchant.alert}</span>
          </div>
        </InspectorCard>

        <InspectorCard
          accent="bg-lime"
          title={`Trigger: ${contexts.trigger.id}`}
          badge="ACTIVE"
          ring
        >
          <div className="mt-2 space-y-1.5 text-[12px]">
            <div>
              <span className="font-semibold text-ink-muted">Kind:</span>
              <span className="ml-1 font-mono-data text-ink">{contexts.trigger.kind}</span>
            </div>
            <div>
              <span className="font-semibold text-ink-muted">Why now:</span>
              <span className="ml-1 text-ink">{contexts.trigger.why}</span>
            </div>
            <div className="rounded-[8px] bg-lime-soft p-2 text-[11px] leading-snug text-ink">
              <span className="font-bold text-teal">Suggested Action:</span> {contexts.trigger.action}
            </div>
          </div>
        </InspectorCard>

        <div className="relative overflow-hidden rounded-[14px] bg-sunken/60 p-3.5 pl-4 opacity-60">
          <div className="absolute bottom-0 left-0 top-0 w-1.5 bg-ink-disabled" />
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-ink-muted">Customer (optional)</span>
            <span className="font-mono-data text-[10px] font-semibold uppercase text-ink-disabled">
              Disabled
            </span>
          </div>
          <p className="mt-1.5 text-[11px] text-ink-muted">
            Not utilized for this merchant-facing digest broadcast. Pipeline targets clinic
            principal.
          </p>
          <div className="mt-2 border-t border-hairline pt-2 font-mono-data text-[10px] text-ink-disabled">
            status: pass-through · target: dr_meera_direct
          </div>
        </div>
      </div>

      <div className="border-t border-hairline bg-chalk p-4">
        <div className="flex items-center justify-between font-mono-data text-[11px] text-ink-muted">
          <span className="font-semibold text-ink">Version Matrix</span>
          <span>{contexts.versions}</span>
        </div>
        <p className="mt-1 text-[10px] leading-normal text-ink-disabled">
          Higher atomic context version invalidates and updates stale composer trees automatically.
        </p>
      </div>
    </aside>
  )
}

function InspectorCard({
  accent,
  title,
  actionLabel,
  badge,
  ring,
  children,
}: {
  accent: string
  title: string
  actionLabel?: string
  badge?: string
  ring?: boolean
  children: ReactNode
}) {
  return (
    <div
      className={[
        'relative overflow-hidden rounded-[14px] border border-hairline bg-chalk p-3.5 pl-4',
        ring ? 'ring-1 ring-lime' : '',
      ].join(' ')}
    >
      <div className={`absolute bottom-0 left-0 top-0 w-1.5 ${accent}`} />
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-bold text-ink">{title}</span>
        {badge ? (
          <span className="rounded-full bg-lime px-1.5 py-0.5 font-mono-data text-[10px] font-bold text-ink">
            {badge}
          </span>
        ) : actionLabel ? (
          <button type="button" className="text-[11px] font-bold text-success hover:underline">
            {actionLabel}
          </button>
        ) : null}
      </div>
      {children}
    </div>
  )
}

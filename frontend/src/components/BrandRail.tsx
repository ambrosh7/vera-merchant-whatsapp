import {
  BarChart3,
  ChevronsUpDown,
  Inbox,
  Megaphone,
  Network,
  Store,
} from 'lucide-react'
import type { NavItem } from '../data/studio'

const icons = {
  hub: Network,
  inbox: Inbox,
  store: Store,
  campaign: Megaphone,
  insights: BarChart3,
} as const

type Props = {
  items: NavItem[]
  activeId: string
  onNavigate: (id: string) => void
}

export function BrandRail({ items, activeId, onNavigate }: Props) {
  return (
    <aside className="fixed inset-y-0 left-0 z-50 hidden w-[240px] flex-col justify-between border-r border-hairline bg-chalk md:flex">
      <div className="flex flex-col">
        <div className="flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-[10px] bg-teal">
              <span className="font-display text-sm font-bold text-lime">V</span>
            </div>
            <div className="flex flex-col leading-none">
              <span className="font-display text-xl font-bold tracking-tight text-ink">
                Vera
              </span>
              <span className="mt-1 text-[11px] font-semibold text-ink-muted">
                by magicpin
              </span>
            </div>
          </div>
          <span className="rounded-full bg-lime px-2 py-0.5 font-mono-data text-[10px] font-semibold uppercase text-ink">
            Studio
          </span>
        </div>

        <div className="px-4 pb-2 pt-4">
          <span className="text-[11px] font-bold uppercase tracking-wider text-ink-disabled">
            Clinical Engine
          </span>
        </div>

        <nav className="flex flex-col gap-1 px-2">
          {items.map((item) => {
            const Icon = icons[item.icon]
            const active = item.id === activeId
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onNavigate(item.id)}
                className={[
                  'relative flex items-center justify-between rounded-[10px] px-3 py-2.5 text-left text-sm font-semibold transition-colors',
                  active
                    ? 'bg-chalk text-ink shadow-[0_1px_4px_rgba(15,28,46,0.06)] before:absolute before:bottom-2 before:left-0 before:top-2 before:w-1 before:rounded-r before:bg-lime'
                    : 'text-ink-muted hover:bg-sunken/60 hover:text-ink',
                ].join(' ')}
              >
                <span className="flex items-center gap-2.5">
                  <Icon size={18} strokeWidth={1.8} />
                  {item.label}
                </span>
                {item.badge != null && (
                  <span className="rounded-full bg-sunken px-1.5 py-0.5 font-mono-data text-[11px] text-ink">
                    {item.badge}
                  </span>
                )}
              </button>
            )
          })}
        </nav>
      </div>

      <div className="p-4">
        <button
          type="button"
          className="flex w-full items-center justify-between rounded-[14px] bg-sunken/70 p-2.5 transition-colors hover:bg-sunken"
        >
          <div className="flex min-w-0 items-center gap-2.5">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-teal text-[11px] font-bold text-lime">
              DM
            </div>
            <div className="min-w-0 text-left">
              <div className="truncate text-xs font-bold text-ink">
                Dr. Meera&apos;s Dental
              </div>
              <div className="truncate font-mono-data text-[11px] text-ink-muted">
                Lajpat Nagar, Delhi
              </div>
            </div>
          </div>
          <ChevronsUpDown size={16} className="shrink-0 text-ink-muted" />
        </button>
      </div>
    </aside>
  )
}

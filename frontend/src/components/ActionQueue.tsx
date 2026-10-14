import { CheckCircle2 } from 'lucide-react'
import type { actionQueue as ActionQueueData } from '../data/studio'

type Props = {
  items: typeof ActionQueueData
}

const statusStyles = {
  DRAFT: 'bg-lime text-ink',
  ALERT: 'bg-alert/15 text-alert',
  RECALL: 'bg-sunken text-ink',
} as const

export function ActionQueue({ items }: Props) {
  return (
    <div className="mx-auto mb-4 flex w-full max-w-4xl flex-col gap-2 px-6">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wider text-ink-disabled">
          Up next for this merchant
        </span>
        <span className="font-mono-data text-[11px] text-ink-muted">
          {items.length} queued actions
        </span>
      </div>
      <div className="grid grid-cols-1 gap-2.5 md:grid-cols-3">
        {items.map((item) => (
          <div
            key={item.id}
            className={[
              'flex flex-col justify-between rounded-[14px] bg-chalk p-3 shadow-sm',
              item.active ? 'ring-2 ring-teal' : 'border border-hairline',
            ].join(' ')}
          >
            <div>
              <div className="flex items-center justify-between">
                <span
                  className={[
                    'font-mono-data text-[11px]',
                    item.active ? 'font-bold text-ink' : 'font-semibold text-ink-muted',
                  ].join(' ')}
                >
                  {item.time}
                </span>
                <span
                  className={`rounded-full px-1.5 py-0.5 font-mono-data text-[10px] font-bold ${statusStyles[item.status]}`}
                >
                  {item.status}
                </span>
              </div>
              <div className="mt-1 text-xs font-bold text-ink">{item.title}</div>
              <p className="mt-0.5 line-clamp-1 text-[11px] text-ink-muted">{item.detail}</p>
            </div>
            {item.active ? (
              <span className="mt-2 flex items-center gap-1 text-[10px] font-semibold text-success">
                <CheckCircle2 size={12} /> Active in studio
              </span>
            ) : (
              <span className="mt-2 text-[10px] text-ink-muted">
                {item.status === 'ALERT' ? 'Suggested action' : 'Retention cadence'}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

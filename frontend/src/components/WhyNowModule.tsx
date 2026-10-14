import { Send } from 'lucide-react'
import type { whyNow as WhyNowData } from '../data/studio'

type Props = {
  data: typeof WhyNowData
  status: 'idle' | 'approved' | 'suppressed'
  onApprove: () => void
  onSuppress: () => void
}

export function WhyNowModule({ data, status, onApprove, onSuppress }: Props) {
  return (
    <div className="mx-auto mb-2 w-full max-w-4xl rounded-[18px] bg-chalk p-4 shadow-[0_4px_0_0_rgba(15,28,46,0.05),0_16px_32px_0_rgba(15,28,46,0.06)]">
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-display text-base font-bold text-ink">Why now?</span>
            <span className="rounded-full bg-lime px-2 py-0.5 font-mono-data text-[11px] font-bold uppercase text-ink">
              {data.kind}
            </span>
            {status === 'approved' && (
              <span className="rounded-full bg-success/15 px-2 py-0.5 text-[11px] font-bold text-success">
                Queued
              </span>
            )}
            {status === 'suppressed' && (
              <span className="rounded-full bg-alert/15 px-2 py-0.5 text-[11px] font-bold text-alert">
                Suppressed
              </span>
            )}
          </div>
          <p className="mt-1 text-[13px] text-ink">{data.reason}</p>
        </div>
        <div className="flex shrink-0 flex-col items-end">
          <span className="font-mono-data text-[11px] font-medium uppercase text-ink-muted">
            Optimal Window
          </span>
          <span className="font-mono-data text-xs font-bold text-ink">{data.window}</span>
        </div>
      </div>

      <div className="mt-3 flex flex-col justify-between gap-3 border-t border-hairline pt-3 md:flex-row md:items-center">
        <div className="flex min-w-[200px] items-center gap-2">
          <span className="text-xs text-ink-muted">Send Confidence</span>
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-sunken">
            <div className="h-full bg-lime" style={{ width: `${data.confidence}%` }} />
          </div>
          <span className="font-mono-data text-xs font-bold text-ink">{data.confidence}%</span>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <button
            type="button"
            onClick={onSuppress}
            disabled={status !== 'idle'}
            className="rounded-[10px] bg-sunken/80 px-3 py-2 text-xs font-medium text-alert transition-colors hover:bg-sunken disabled:opacity-40"
          >
            Suppress trigger
          </button>
          <button
            type="button"
            className="rounded-[10px] bg-sunken px-4 py-2 text-xs font-semibold text-ink transition-colors hover:bg-hairline"
          >
            Edit draft
          </button>
          <button
            type="button"
            onClick={onApprove}
            disabled={status !== 'idle'}
            className="flex items-center gap-1.5 rounded-[10px] bg-lime px-5 py-2 text-xs font-bold tracking-tight text-ink shadow-sm transition-all hover:bg-lime-hover disabled:opacity-40"
          >
            <Send size={14} />
            Approve &amp; Queue Now
          </button>
        </div>
      </div>
    </div>
  )
}

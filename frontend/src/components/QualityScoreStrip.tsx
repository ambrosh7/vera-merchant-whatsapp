import { BadgeCheck } from 'lucide-react'
import type { ScoreDimension } from '../data/studio'

type Props = {
  scores: ScoreDimension[]
  composite: string
}

export function QualityScoreStrip({ scores, composite }: Props) {
  return (
    <section className="flex items-center justify-between border-b border-hairline bg-chalk px-6 py-1.5">
      <div className="flex min-w-0 items-center gap-4">
        <div className="flex shrink-0 items-center gap-1.5">
          <BadgeCheck size={16} className="text-success" />
          <span className="text-[11px] font-bold uppercase tracking-wider text-ink">
            Judge-ready Quality
          </span>
        </div>
        <div className="hidden items-center gap-3 text-xs lg:flex">
          {scores.map((item, index) => (
            <div key={item.label} className="flex items-center gap-3">
              {index > 0 && <span className="text-ink-disabled">·</span>}
              <div className="flex items-center gap-1.5">
                <span className="text-ink-muted">{item.label}</span>
                <div className="h-1.5 w-10 overflow-hidden rounded-full bg-sunken">
                  <div
                    className={[
                      'h-full rounded-full',
                      item.score === item.max ? 'bg-teal' : 'bg-lime',
                    ].join(' ')}
                    style={{ width: `${(item.score / item.max) * 100}%` }}
                  />
                </div>
                <span className="font-mono-data font-semibold text-ink">{item.score}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-ink-muted">
          Composite
        </span>
        <span className="rounded-full bg-teal px-2.5 py-0.5 font-mono-data text-xs font-bold text-lime">
          {composite}
        </span>
      </div>
    </section>
  )
}

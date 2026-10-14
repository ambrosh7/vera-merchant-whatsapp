import { BookOpen, CheckCheck, FileText, Sparkles } from 'lucide-react'
import type { Message } from '../data/studio'

type Props = {
  messages: Message[]
}

function ContextChip({
  label,
  tone,
}: {
  label: string
  tone: 'neutral' | 'merchant' | 'trigger' | 'disabled'
}) {
  const styles = {
    neutral: 'bg-sunken text-ink-muted',
    merchant: 'bg-teal/10 text-teal',
    trigger: 'bg-lime text-ink font-semibold',
    disabled: 'bg-sunken text-ink-disabled line-through opacity-70',
  } as const

  return (
    <span className={`rounded-full px-2 py-0.5 font-mono-data text-[11px] ${styles[tone]}`}>
      {label}
    </span>
  )
}

export function ConversationCanvas({ messages }: Props) {
  return (
    <section className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-6 overflow-y-auto px-6 py-6">
      <div className="my-1 flex justify-center">
        <span className="rounded-full bg-chalk px-3 py-1 font-mono-data text-[11px] uppercase tracking-wider text-ink-muted shadow-sm">
          Today · 10:42 AM IST · Session Initialized
        </span>
      </div>

      {messages.map((message) => {
        if (message.kind === 'vera') {
          return (
            <div key={message.id} className="animate-rise flex max-w-[520px] flex-col items-start gap-1">
              <div className="mb-1 flex items-center gap-2 px-1">
                <div className="flex h-5 w-5 items-center justify-center rounded-full bg-teal text-lime">
                  <Sparkles size={11} />
                </div>
                <span className="text-xs font-bold text-ink">Vera</span>
                <span className="font-mono-data text-[11px] text-ink-muted">{message.label}</span>
              </div>
              <div className="relative rounded-[18px] rounded-tl-sm bg-chalk p-3.5 shadow-sm">
                <p className="text-[15px] leading-relaxed text-ink">
                  {message.body}
                  {message.highlight && (
                    <span className="font-semibold text-teal">{message.highlight}</span>
                  )}{' '}
                  Worth a look (2-min abstract). Want me to pull it + draft a patient-ed WhatsApp
                  you can share?
                </p>
                {message.source && (
                  <div className="mt-2 flex items-center justify-between border-t border-hairline pt-2 font-mono-data text-[11px] text-ink-muted">
                    <span className="flex items-center gap-1">
                      <BookOpen size={13} className="text-teal" />
                      {message.source}
                    </span>
                    <span className="text-[10px]">{message.time}</span>
                  </div>
                )}
              </div>
              <div className="mt-1 flex flex-wrap items-center gap-1.5 px-1">
                {message.contexts.map((chip) => (
                  <ContextChip key={chip.label} label={chip.label} tone={chip.tone} />
                ))}
              </div>
            </div>
          )
        }

        if (message.kind === 'merchant') {
          return (
            <div
              key={message.id}
              className="animate-rise flex max-w-[440px] flex-col items-end gap-1 self-end"
            >
              <div className="rounded-[18px] rounded-tr-sm bg-merchant-bubble px-3.5 py-2.5 shadow-sm">
                <p className="text-[15px] font-medium leading-snug text-ink">{message.body}</p>
                <div className="mt-1 flex items-center justify-end gap-1 font-mono-data text-[11px] text-ink-muted">
                  <span className="text-[10px]">{message.time}</span>
                  <CheckCheck size={14} className="text-teal" />
                </div>
              </div>
              <span className="px-1 text-[11px] font-medium text-ink-muted">{message.author}</span>
            </div>
          )
        }

        return (
          <div
            key={message.id}
            className="animate-rise my-1 flex max-w-[540px] flex-col items-start gap-1"
          >
            <div className="mb-1 flex items-center gap-2 px-1">
              <div className="flex h-5 w-5 items-center justify-center rounded-full bg-lime text-ink">
                <Sparkles size={11} />
              </div>
              <span className="text-xs font-bold text-ink">Vera Draft · Staged for Approval</span>
              <span className="live-dot h-2 w-2 rounded-full bg-lime" />
            </div>
            <div className="w-full rounded-[18px] rounded-tl-sm bg-lime-soft p-3.5 shadow-sm ring-1 ring-lime">
              <div className="mb-2 flex items-center justify-between pb-2">
                <span className="flex items-center gap-1 text-[11px] font-bold uppercase tracking-wider text-success">
                  <FileText size={14} />
                  Outbound Draft Payload
                </span>
                <span className="rounded-full bg-sunken px-2 py-0.5 font-mono-data text-[11px] text-ink">
                  {message.recipients} recipients targeted
                </span>
              </div>
              <p className="text-[15px] leading-relaxed text-ink">{message.body}</p>
              <div className="mt-2.5 rounded-[14px] bg-chalk p-3 ring-1 ring-lime/70">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-teal">
                  <FileText size={15} />
                  <span>{message.attachment.title}</span>
                </div>
                <p className="mt-1.5 text-[13px] leading-normal text-ink-muted">
                  {message.attachment.summary}
                </p>
                <div className="mt-2.5 flex items-center justify-between rounded-[10px] bg-sunken/70 px-2.5 py-1.5">
                  <span className="text-xs font-semibold text-teal">
                    Reciprocal clinic offer linked: {message.attachment.offer}
                  </span>
                  <span className="font-mono-data text-xs text-ink-muted">
                    magicpin SKU: {message.attachment.sku}
                  </span>
                </div>
              </div>
              <div className="mt-2 flex items-center justify-end gap-1.5 pt-1.5 font-mono-data text-[11px] text-ink-muted">
                <span className="text-[10px] text-ink-disabled">{message.time}</span>
                <span className="rounded bg-lime px-1.5 py-0.5 text-[10px] font-bold uppercase text-ink">
                  Staged
                </span>
              </div>
            </div>
          </div>
        )
      })}
    </section>
  )
}

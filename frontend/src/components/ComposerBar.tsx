import { Paperclip, Send, SmilePlus, Table2 } from 'lucide-react'

type Props = {
  value: string
  onChange: (value: string) => void
  onSend: () => void
}

export function ComposerBar({ value, onChange, onSend }: Props) {
  return (
    <footer className="z-30 border-t border-hairline bg-chalk p-4 shadow-[0_-2px_12px_rgba(15,28,46,0.03)]">
      <div className="mx-auto flex max-w-4xl flex-col gap-2">
        <div className="flex items-center gap-2 rounded-[14px] bg-canvas px-3 py-2 shadow-inner">
          <button
            type="button"
            className="flex h-8 w-8 items-center justify-center rounded-[10px] text-ink-muted transition-colors hover:bg-sunken"
            aria-label="Emoji"
          >
            <SmilePlus size={18} />
          </button>
          <button
            type="button"
            className="flex h-8 w-8 items-center justify-center rounded-[10px] text-ink-muted transition-colors hover:bg-sunken"
            aria-label="Templates"
          >
            <Table2 size={18} />
          </button>
          <button
            type="button"
            className="flex h-8 w-8 items-center justify-center rounded-[10px] text-ink-muted transition-colors hover:bg-sunken"
            aria-label="Attach"
          >
            <Paperclip size={18} />
          </button>
          <input
            className="flex-1 border-0 bg-transparent px-2 text-sm text-ink outline-none placeholder:text-ink-disabled"
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) onSend()
            }}
            placeholder="Edit Vera's draft or add a note…"
          />
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="rounded-[10px] bg-chalk px-3 py-1.5 text-xs font-semibold text-ink shadow-sm transition-colors hover:bg-sunken"
            >
              Preview WhatsApp
            </button>
            <button
              type="button"
              onClick={onSend}
              className="flex items-center gap-1.5 rounded-[10px] bg-teal px-4 py-1.5 text-xs font-bold text-chalk shadow-sm transition-colors hover:bg-teal-deep"
            >
              <Send size={14} />
              Send as Vera
            </button>
          </div>
        </div>
        <div className="flex items-center justify-between px-1">
          <span className="flex items-center gap-1 font-mono-data text-[11px] text-ink-muted">
            Grounding: Category + Merchant + Trigger contexts only · zero hallucinated offers
          </span>
          <span className="font-mono-data text-[11px] text-ink-disabled">
            ⌘ + Enter to approve
          </span>
        </div>
      </div>
    </footer>
  )
}

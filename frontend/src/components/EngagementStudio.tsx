import { useState } from 'react'
import {
  actionQueue,
  messages,
  navItems,
  qualityScores,
  whyNow,
} from '../data/studio'
import { ActionQueue } from './ActionQueue'
import { BrandRail } from './BrandRail'
import { ComposerBar } from './ComposerBar'
import { ContextHeader } from './ContextHeader'
import { ContextInspector } from './ContextInspector'
import { ConversationCanvas } from './ConversationCanvas'
import { QualityScoreStrip } from './QualityScoreStrip'
import { WhyNowModule } from './WhyNowModule'

export function EngagementStudio() {
  const [activeNav, setActiveNav] = useState('studio')
  const [inspectorOpen, setInspectorOpen] = useState(false)
  const [draftNote, setDraftNote] = useState('')
  const [triggerStatus, setTriggerStatus] = useState<'idle' | 'approved' | 'suppressed'>('idle')
  const [toast, setToast] = useState<string | null>(null)

  function flash(message: string) {
    setToast(message)
    window.setTimeout(() => setToast(null), 2200)
  }

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <BrandRail items={navItems} activeId={activeNav} onNavigate={setActiveNav} />

      <div className="pl-0 md:pl-[240px]">
        <div className="flex min-h-screen w-full bg-canvas">
          <main className="flex min-w-0 flex-1 flex-col">
            <ContextHeader
              inspectorOpen={inspectorOpen}
              onToggleInspector={() => setInspectorOpen((v) => !v)}
            />
            <QualityScoreStrip scores={qualityScores} composite="49 / 50" />

            <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
              <div className="flex min-h-0 flex-1 flex-col overflow-y-auto">
                <ConversationCanvas messages={messages} />
                <div className="px-6">
                  <WhyNowModule
                    data={whyNow}
                    status={triggerStatus}
                    onApprove={() => {
                      setTriggerStatus('approved')
                      flash('Draft approved · queued on WhatsApp')
                    }}
                    onSuppress={() => {
                      setTriggerStatus('suppressed')
                      flash('Trigger suppressed for this merchant')
                    }}
                  />
                </div>
                <ActionQueue items={actionQueue} />
              </div>
              <ComposerBar
                value={draftNote}
                onChange={setDraftNote}
                onSend={() => flash('Sent as Vera')}
              />
            </div>
          </main>

          <ContextInspector open={inspectorOpen} onClose={() => setInspectorOpen(false)} />
        </div>
      </div>

      {inspectorOpen && (
        <button
          type="button"
          className="fixed inset-0 z-30 bg-ink/20 xl:hidden"
          aria-label="Close inspector overlay"
          onClick={() => setInspectorOpen(false)}
        />
      )}

      {toast && (
        <div className="animate-rise fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-[10px] bg-teal px-4 py-2.5 text-sm font-semibold text-chalk shadow-lg md:left-[calc(50%+120px)]">
          {toast}
        </div>
      )}
    </div>
  )
}

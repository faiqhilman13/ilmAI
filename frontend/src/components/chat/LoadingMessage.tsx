import { Bot } from 'lucide-react'

export default function LoadingMessage() {
  return (
    <div className="message-wrapper assistant">
      <div className="message-avatar" aria-hidden="true">
        <Bot size={20} />
      </div>
      <div className="message-content glass-panel">
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: 4 }}>
          <div style={{ width: 8, height: 8, borderRadius: 999, background: 'var(--color-text-muted)' }} className="loading-dot" />
          <div style={{ width: 8, height: 8, borderRadius: 999, background: 'var(--color-text-muted)' }} className="loading-dot" />
          <div style={{ width: 8, height: 8, borderRadius: 999, background: 'var(--color-text-muted)' }} className="loading-dot" />
        </div>
      </div>
    </div>
  )
}

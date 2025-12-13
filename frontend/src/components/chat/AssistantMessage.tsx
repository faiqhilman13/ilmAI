import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Bot, BookOpen, Bookmark, Copy, Check } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import type { Message } from '../../types'
import CitationList from '../citation/CitationList'

interface AssistantMessageProps {
  message: Message
}

export default function AssistantMessage({ message }: AssistantMessageProps) {
  const { t } = useTranslation()
  const [copied, setCopied] = useState(false)
  const [showCitations, setShowCitations] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // Parse citation markers [1], [2], etc. in the text
  const renderContent = (content: string) => {
    // Replace citation markers with styled spans
    const parts = content.split(/(\[\d+\])/)
    return parts.map((part, index) => {
      const match = part.match(/\[(\d+)\]/)
      if (match) {
        const citationIndex = parseInt(match[1])
        return (
          <button
            key={index}
            onClick={() => setShowCitations(true)}
            className="citation-marker"
            title={`View source ${citationIndex}`}
          >
            {part}
          </button>
        )
      }
      return <span key={index}>{part}</span>
    })
  }

  return (
    <div className="message-wrapper assistant">
      <div className="message-avatar" aria-hidden="true">
        <Bot size={20} />
      </div>
      <div className="message-content glass-panel">
        <div className="message-text">
          <div style={{ whiteSpace: 'pre-wrap' }}>{renderContent(message.content)}</div>
        </div>

        {/* Disclaimer */}
        {message.disclaimer && (
          <div className="citations-container">
            <ReactMarkdown>{message.disclaimer}</ReactMarkdown>
          </div>
        )}

        {/* Citations */}
        {message.citations && message.citations.length > 0 && (
          <div className="citations-container">
            <button onClick={() => setShowCitations(!showCitations)} type="button" className="citations-header">
              <BookOpen size={14} />
              <span>
                {t('sources')} ({message.citations.length})
              </span>
            </button>
            {showCitations && (
              <div className="citations-list">
                <CitationList citations={message.citations} />
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 12, opacity: 0.9 }}>
          <button
            onClick={handleCopy}
            className="theme-toggle-btn"
            type="button"
            style={{ width: 'auto', padding: '6px 10px' }}
          >
            {copied ? (
              <>
                <Check size={14} />
                <span>Disalin!</span>
              </>
            ) : (
              <>
                <Copy size={14} />
                <span>Salin</span>
              </>
            )}
          </button>

          <button className="theme-toggle-btn" type="button" style={{ width: 'auto', padding: '6px 10px' }}>
            <Bookmark size={14} />
            <span>Simpan</span>
          </button>
        </div>
      </div>
    </div>
  )
}

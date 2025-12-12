import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { BookOpen, Bookmark, Copy, Check } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import type { Message, Citation } from '../../types'
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
    <div className="flex gap-3">
      {/* Avatar */}
      <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center flex-shrink-0">
        <BookOpen className="w-4 h-4 text-white" />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        {/* Main answer */}
        <div className="prose prose-sm max-w-none">
          <div className="text-gray-900 whitespace-pre-wrap">
            {renderContent(message.content)}
          </div>
        </div>

        {/* Disclaimer */}
        {message.disclaimer && (
          <div className="disclaimer mt-4">
            <ReactMarkdown>{message.disclaimer}</ReactMarkdown>
          </div>
        )}

        {/* Citations */}
        {message.citations && message.citations.length > 0 && (
          <div className="mt-4">
            <button
              onClick={() => setShowCitations(!showCitations)}
              className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
            >
              📚 {t('sources')} ({message.citations.length})
              <span className="text-xs">{showCitations ? '▲' : '▼'}</span>
            </button>

            {showCitations && (
              <div className="mt-2">
                <CitationList citations={message.citations} />
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2 mt-3">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 px-2 py-1 rounded hover:bg-gray-100"
          >
            {copied ? (
              <>
                <Check className="w-3 h-3" />
                <span>Disalin!</span>
              </>
            ) : (
              <>
                <Copy className="w-3 h-3" />
                <span>Salin</span>
              </>
            )}
          </button>

          <button className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 px-2 py-1 rounded hover:bg-gray-100">
            <Bookmark className="w-3 h-3" />
            <span>Simpan</span>
          </button>
        </div>
      </div>
    </div>
  )
}

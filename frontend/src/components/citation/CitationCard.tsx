import { useState } from 'react'
import { ChevronDown, ChevronUp, Book, ScrollText, Scale, FileText } from 'lucide-react'
import type { Citation, QuranCitation, HadithCitation, FiqhCitation, FatwaCitation } from '../../types'

interface CitationCardProps {
  citation: Citation
}

export default function CitationCard({ citation }: CitationCardProps) {
  const [expanded, setExpanded] = useState(false)

  const getIcon = () => {
    switch (citation.sourceType) {
      case 'quran':
        return <Book className="w-4 h-4" />
      case 'hadith':
        return <ScrollText className="w-4 h-4" />
      case 'fiqh':
        return <Scale className="w-4 h-4" />
      case 'fatwa':
        return <FileText className="w-4 h-4" />
    }
  }

  const getBadgeClass = () => {
    switch (citation.sourceType) {
      case 'quran':
        return 'badge-quran'
      case 'hadith':
        return 'badge-hadith'
      case 'fiqh':
        return 'badge-fiqh'
      case 'fatwa':
        return 'badge-fatwa'
    }
  }

  const getTitle = () => {
    switch (citation.sourceType) {
      case 'quran': {
        const q = citation as QuranCitation
        const ayahRange = q.ayahEnd ? `${q.ayahStart}-${q.ayahEnd}` : q.ayahStart
        return `Al-Quran - Surah ${q.surahName} (${q.surahNumber}:${ayahRange})`
      }
      case 'hadith': {
        const h = citation as HadithCitation
        return `${h.collection} - Hadis #${h.hadithNumber}`
      }
      case 'fiqh': {
        const f = citation as FiqhCitation
        return `Fiqh ${f.madhab.charAt(0).toUpperCase() + f.madhab.slice(1)} - ${f.topic}`
      }
      case 'fatwa': {
        const fa = citation as FatwaCitation
        return `Fatwa ${fa.issuingAuthority} - ${fa.topic}`
      }
    }
  }

  const renderGradingBadge = () => {
    if (citation.sourceType !== 'hadith') return null
    const h = citation as HadithCitation

    const gradingLabels: Record<string, string> = {
      sahih: 'Sahih',
      hasan: 'Hasan',
      daif: "Da'if",
      mawdu: "Mawdu'",
    }

    return (
      <span className={`text-xs px-2 py-0.5 rounded grading-${h.grading}`}>
        {gradingLabels[h.grading]}
      </span>
    )
  }

  const renderExpandedContent = () => {
    switch (citation.sourceType) {
      case 'quran': {
        const q = citation as QuranCitation
        return (
          <div className="space-y-2">
            {q.arabicText && (
              <p className="arabic-text text-lg">{q.arabicText}</p>
            )}
            {q.translation && (
              <p className="text-gray-700 italic border-l-2 border-green-500 pl-3">
                {q.translation}
              </p>
            )}
          </div>
        )
      }
      case 'hadith': {
        const h = citation as HadithCitation
        return (
          <div className="space-y-2">
            <p className="text-gray-700">{h.textSnippet}</p>
            {h.narratorChain && (
              <p className="text-sm text-gray-500">
                <span className="font-medium">Sanad:</span> {h.narratorChain}
              </p>
            )}
          </div>
        )
      }
      default:
        return <p className="text-gray-700">{citation.textSnippet}</p>
    }
  }

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 p-3 bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <span className={`p-1.5 rounded ${getBadgeClass()}`}>
          {getIcon()}
        </span>

        <span className="font-medium text-sm text-primary-600">[{citation.index}]</span>

        <span className="flex-1 text-left text-sm font-medium text-gray-900 truncate">
          {getTitle()}
        </span>

        {renderGradingBadge()}

        {expanded ? (
          <ChevronUp className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        )}
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="p-4 bg-white border-t border-gray-200">
          {renderExpandedContent()}
        </div>
      )}
    </div>
  )
}

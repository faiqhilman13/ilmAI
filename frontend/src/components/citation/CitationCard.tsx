import type { Citation, QuranCitation, HadithCitation, FiqhCitation, FatwaCitation } from '../../types'

interface CitationCardProps {
  citation: Citation
}

export default function CitationCard({ citation }: CitationCardProps) {
  const typeLabel = (() => {
    switch (citation.sourceType) {
      case 'quran':
        return 'Quran'
      case 'hadith': {
        const h = citation as HadithCitation
        return h.grading ? `Hadith · ${h.grading}` : 'Hadith'
      }
      case 'fiqh':
        return 'Fiqh'
      case 'fatwa':
        return 'Fatwa'
    }
  })()

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

  return (
    <div className="citation-card">
      <span className="citation-type">{typeLabel}</span>
      <span className="citation-source">
        [{citation.index}] {getTitle()}
      </span>
      <span className="citation-detail">{citation.textSnippet}</span>
    </div>
  )
}

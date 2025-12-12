import type { Citation } from '../../types'
import CitationCard from './CitationCard'

interface CitationListProps {
  citations: Citation[]
}

export default function CitationList({ citations }: CitationListProps) {
  return (
    <div className="space-y-2">
      {citations.map((citation) => (
        <CitationCard key={citation.index} citation={citation} />
      ))}
    </div>
  )
}

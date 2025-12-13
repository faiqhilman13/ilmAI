import type { Citation } from '../../types'
import CitationCard from './CitationCard'

interface CitationListProps {
  citations: Citation[]
}

export default function CitationList({ citations }: CitationListProps) {
  return (
    <>
      {citations.map((citation) => (
        <CitationCard key={citation.index} citation={citation} />
      ))}
    </>
  )
}

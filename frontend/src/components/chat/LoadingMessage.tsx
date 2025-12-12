import { BookOpen } from 'lucide-react'

export default function LoadingMessage() {
  return (
    <div className="flex gap-3">
      {/* Avatar */}
      <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center flex-shrink-0">
        <BookOpen className="w-4 h-4 text-white" />
      </div>

      {/* Loading animation */}
      <div className="flex items-center gap-1 py-2">
        <div className="w-2 h-2 bg-gray-400 rounded-full loading-dot" />
        <div className="w-2 h-2 bg-gray-400 rounded-full loading-dot" />
        <div className="w-2 h-2 bg-gray-400 rounded-full loading-dot" />
      </div>
    </div>
  )
}

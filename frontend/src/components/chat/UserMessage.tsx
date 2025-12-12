import { User } from 'lucide-react'
import type { Message } from '../../types'

interface UserMessageProps {
  message: Message
}

export default function UserMessage({ message }: UserMessageProps) {
  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0">
        <User className="w-4 h-4 text-gray-600" />
      </div>
      <div className="flex-1">
        <p className="text-gray-900">{message.content}</p>
      </div>
    </div>
  )
}

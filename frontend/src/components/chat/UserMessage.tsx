import { User } from 'lucide-react'
import type { Message } from '../../types'

interface UserMessageProps {
  message: Message
}

export default function UserMessage({ message }: UserMessageProps) {
  return (
    <div className="message-wrapper user">
      <div className="message-avatar" aria-hidden="true">
        <User size={20} />
      </div>
      <div className="message-content glass-panel">
        <div className="message-text">
          <p>{message.content}</p>
        </div>
      </div>
    </div>
  )
}

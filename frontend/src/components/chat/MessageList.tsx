import type { Message } from '../../types'
import UserMessage from './UserMessage'
import AssistantMessage from './AssistantMessage'
import LoadingMessage from './LoadingMessage'

interface MessageListProps {
  messages: Message[]
  isLoading: boolean
}

export default function MessageList({ messages, isLoading }: MessageListProps) {
  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
      {messages.map((message) =>
        message.role === 'user' ? (
          <UserMessage key={message.id} message={message} />
        ) : (
          <AssistantMessage key={message.id} message={message} />
        )
      )}
      {isLoading && <LoadingMessage />}
    </div>
  )
}

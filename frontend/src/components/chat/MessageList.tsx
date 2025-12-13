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
    <>
      {messages.map((message) =>
        message.role === 'user' ? (
          <UserMessage key={message.id} message={message} />
        ) : (
          <AssistantMessage key={message.id} message={message} />
        )
      )}
      {isLoading && <LoadingMessage />}
    </>
  )
}

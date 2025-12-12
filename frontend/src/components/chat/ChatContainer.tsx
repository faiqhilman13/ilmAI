import { useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useChatStore } from '../../stores/chatStore'
import MessageList from './MessageList'
import ChatInput from './ChatInput'
import SuggestedQuestions from './SuggestedQuestions'
import chatService from '../../services/chatService'
import type { Message, Language } from '../../types'

export default function ChatContainer() {
  const { t, i18n } = useTranslation()
  const {
    messages,
    isLoading,
    setIsLoading,
    addMessage,
    currentConversation,
  } = useChatStore()

  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return

    setError(null)
    setIsLoading(true)

    // Add user message immediately
    const userMessage: Message = {
      id: `temp-user-${Date.now()}`,
      role: 'user',
      content,
      createdAt: new Date().toISOString(),
    }
    addMessage(userMessage)

    try {
      const response = await chatService.sendMessage({
        message: content,
        conversationId: currentConversation?.id,
        language: i18n.language as Language,
      })

      // Add assistant message
      const assistantMessage: Message = {
        id: response.messageId,
        role: 'assistant',
        content: response.answer,
        citations: response.citations,
        disclaimer: response.disclaimer,
        topics: response.topics,
        createdAt: new Date().toISOString(),
      }
      addMessage(assistantMessage)
    } catch (err: any) {
      setError(err.response?.data?.detail || t('networkError'))
      console.error('Chat error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSuggestedQuestion = (question: string) => {
    handleSendMessage(question)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center p-4">
            <div className="max-w-2xl w-full text-center">
              {/* Welcome message */}
              <div className="mb-8">
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                  Assalamualaikum! 👋
                </h2>
                <p className="text-gray-600">
                  {i18n.language === 'ms'
                    ? 'Saya IlmuAI, pembantu anda untuk soalan tentang Islam. Tanya apa sahaja tentang solat, puasa, zakat, atau hukum-hukum Islam yang lain.'
                    : "I'm IlmuAI, your assistant for questions about Islam. Ask anything about prayer, fasting, zakat, or other Islamic rulings."}
                </p>
              </div>

              {/* Suggested questions */}
              <SuggestedQuestions onSelect={handleSuggestedQuestion} />
            </div>
          </div>
        ) : (
          <MessageList messages={messages} isLoading={isLoading} />
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Error message */}
      {error && (
        <div className="px-4 py-2 bg-red-50 text-red-600 text-sm text-center">
          {error}
        </div>
      )}

      {/* Input area */}
      <div className="border-t border-gray-200 bg-white p-4">
        <div className="max-w-3xl mx-auto">
          <ChatInput onSend={handleSendMessage} disabled={isLoading} />
          <p className="text-xs text-gray-400 text-center mt-2">
            {i18n.language === 'ms'
              ? 'IlmuAI boleh membuat kesilapan. Sentiasa sahkan dengan sumber yang dipercayai.'
              : 'IlmuAI can make mistakes. Always verify with trusted sources.'}
          </p>
        </div>
      </div>
    </div>
  )
}

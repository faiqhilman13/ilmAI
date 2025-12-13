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
    <div className="chat-container">
      <div className="chat-history">
        {messages.length === 0 ? (
          <div className="message-wrapper assistant" style={{ maxWidth: '100%' }}>
            <div className="message-avatar" aria-hidden="true">
              IA
            </div>
            <div className="message-content glass-panel" style={{ width: '100%' }}>
              <div className="message-text">
                <p style={{ fontWeight: 700 }}>Assalamualaikum! 👋</p>
                <p>
                  {i18n.language === 'ms'
                    ? 'Saya IlmuAI, pembantu anda untuk soalan tentang Islam. Tanya apa sahaja tentang solat, puasa, zakat, atau hukum-hukum Islam yang lain.'
                    : "I'm IlmuAI, your assistant for questions about Islam. Ask anything about prayer, fasting, zakat, or other Islamic rulings."}
                </p>
              </div>
              <div style={{ marginTop: 16 }}>
                <SuggestedQuestions onSelect={handleSuggestedQuestion} />
              </div>
            </div>
          </div>
        ) : (
          <MessageList messages={messages} isLoading={isLoading} />
        )}
        <div ref={messagesEndRef} />
      </div>

      {error && (
        <div style={{ padding: '8px 12px', color: '#fecaca', textAlign: 'center', fontSize: 14 }}>
          {error}
        </div>
      )}

      <div className="input-area glass-panel">
        <ChatInput onSend={handleSendMessage} disabled={isLoading} />
      </div>
    </div>
  )
}

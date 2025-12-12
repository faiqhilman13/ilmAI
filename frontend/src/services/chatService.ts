import api from './api'
import type { ChatRequest, ChatResponse, Language } from '../types'

export const chatService = {
  /**
   * Send a message and get AI response
   */
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await api.post<ChatResponse>('/chat', {
      message: request.message,
      conversation_id: request.conversationId,
      language: request.language || 'ms',
    })
    return response.data
  },

  /**
   * Send message with streaming response
   */
  async sendMessageStreaming(
    request: ChatRequest,
    onChunk: (chunk: string) => void,
    signal?: AbortSignal
  ): Promise<ChatResponse> {
    const response = await fetch(`${import.meta.env.VITE_API_URL || '/api'}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${localStorage.getItem('token') || ''}`,
      },
      body: JSON.stringify({
        message: request.message,
        conversation_id: request.conversationId,
        language: request.language || 'ms',
      }),
      signal,
    })

    if (!response.ok) {
      throw new Error('Failed to send message')
    }

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()
    let fullResponse = ''
    let meta: Partial<ChatResponse> = {}
    let buffer = ''

    if (reader) {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value)
        const parts = buffer.split('\n\n')
        buffer = parts.pop() || ''

        for (const part of parts) {
          const lines = part.split('\n').filter(Boolean)
          let eventType = 'chunk'
          let dataLines: string[] = []

          for (const line of lines) {
            if (line.startsWith('event:')) {
              eventType = line.slice(6).trim()
            } else if (line.startsWith('data:')) {
              dataLines.push(line.slice(5).trim())
            }
          }

          const data = dataLines.join('\n')
          if (eventType === 'done' || data === '[DONE]') {
            continue
          }

          if (eventType === 'meta') {
            try {
              const parsed = JSON.parse(data)
              meta = {
                citations: parsed.citations || [],
                topics: parsed.topics || [],
                language: parsed.language || request.language || 'ms',
                disclaimer: parsed.disclaimer,
              }
            } catch {
              // ignore meta parse errors
            }
            continue
          }

          // default: chunk
          fullResponse += data
          onChunk(data)
        }
      }
    }

    return {
      answer: fullResponse,
      citations: meta.citations || [],
      topics: meta.topics || [],
      disclaimer: meta.disclaimer,
      language: meta.language || request.language || 'ms',
      messageId: '',
      conversationId: request.conversationId || '',
    }
  },

  /**
   * Get suggested questions based on current question
   */
  async getSuggestions(question: string, language: Language = 'ms'): Promise<string[]> {
    const response = await api.get<{ suggestions: string[] }>('/chat/suggestions', {
      params: { question, language },
    })
    return response.data.suggestions
  },
}

export default chatService

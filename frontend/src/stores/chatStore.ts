import { create } from 'zustand'
import type { Message, Conversation } from '../types'

interface ChatState {
  // Current conversation
  currentConversation: Conversation | null
  messages: Message[]
  isLoading: boolean
  isStreaming: boolean
  streamingContent: string

  // Actions
  setCurrentConversation: (conversation: Conversation | null) => void
  setMessages: (messages: Message[]) => void
  addMessage: (message: Message) => void
  updateMessage: (messageId: string, updates: Partial<Message>) => void
  clearMessages: () => void
  setIsLoading: (isLoading: boolean) => void
  setIsStreaming: (isStreaming: boolean) => void
  setStreamingContent: (content: string) => void
  appendStreamingContent: (chunk: string) => void
}

export const useChatStore = create<ChatState>((set) => ({
  currentConversation: null,
  messages: [],
  isLoading: false,
  isStreaming: false,
  streamingContent: '',

  setCurrentConversation: (conversation) =>
    set({
      currentConversation: conversation,
      messages: conversation?.messages || [],
    }),

  setMessages: (messages) => set({ messages }),

  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),

  updateMessage: (messageId, updates) =>
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === messageId ? { ...msg, ...updates } : msg
      ),
    })),

  clearMessages: () =>
    set({
      messages: [],
      currentConversation: null,
      streamingContent: '',
    }),

  setIsLoading: (isLoading) => set({ isLoading }),

  setIsStreaming: (isStreaming) => set({ isStreaming }),

  setStreamingContent: (content) => set({ streamingContent: content }),

  appendStreamingContent: (chunk) =>
    set((state) => ({
      streamingContent: state.streamingContent + chunk,
    })),
}))

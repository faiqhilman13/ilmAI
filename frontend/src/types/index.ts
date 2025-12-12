// Source types
export type SourceType = 'quran' | 'hadith' | 'fiqh' | 'fatwa'
export type HadithGrading = 'sahih' | 'hasan' | 'daif' | 'mawdu'
export type Language = 'ms' | 'en'

// Citation types
export interface BaseCitation {
  index: number
  sourceType: SourceType
  textSnippet: string
}

export interface QuranCitation extends BaseCitation {
  sourceType: 'quran'
  surahNumber: number
  surahName: string
  ayahStart: number
  ayahEnd?: number
  arabicText?: string
  translation?: string
}

export interface HadithCitation extends BaseCitation {
  sourceType: 'hadith'
  collection: string
  hadithNumber: string
  grading: HadithGrading
  bookName?: string
  narratorChain?: string
}

export interface FiqhCitation extends BaseCitation {
  sourceType: 'fiqh'
  madhab: string
  topic: string
  sourceBook?: string
  scholar?: string
  evidence?: string
}

export interface FatwaCitation extends BaseCitation {
  sourceType: 'fatwa'
  issuingAuthority: string
  fatwaNumber?: string
  date?: string
  topic: string
}

export type Citation = QuranCitation | HadithCitation | FiqhCitation | FatwaCitation

// Message types
export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  disclaimer?: string
  topics?: string[]
  createdAt: string
}

// Conversation types
export interface Conversation {
  id: string
  title?: string
  language: Language
  messages: Message[]
  createdAt: string
  updatedAt: string
}

export interface ConversationListItem {
  id: string
  title?: string
  language: Language
  createdAt: string
  updatedAt: string
  messageCount: number
}

// User types
export interface User {
  id: string
  email: string
  displayName?: string
  preferredLanguage: Language
  preferredMadhab: string
  isActive: boolean
  createdAt: string
}

// Auth types
export interface Token {
  accessToken: string
  tokenType: string
  user: User
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  displayName?: string
  preferredLanguage?: Language
}

// Chat types
export interface ChatRequest {
  message: string
  conversationId?: string
  language?: Language
}

export interface ChatResponse {
  answer: string
  citations: Citation[]
  disclaimer?: string
  topics: string[]
  language: string
  messageId: string
  conversationId: string
}

// Bookmark types
export interface Bookmark {
  id: string
  messageId: string
  message: Message
  note?: string
  tags: string[]
  createdAt: string
}

// Settings types
export interface UserSettings {
  language: Language
  theme: 'light' | 'dark'
  madhab: string
  showArabic: boolean
  fontSize: 'small' | 'medium' | 'large'
}

// API Response wrapper
export interface ApiResponse<T> {
  data: T
  message?: string
}

export interface ApiError {
  detail: string
  status?: number
}

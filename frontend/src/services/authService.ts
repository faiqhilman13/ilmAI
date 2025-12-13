import api from './api'
import type { Token, LoginCredentials, RegisterData, User } from '../types'

type TokenResponse = {
  access_token: string
  token_type: string
  user: User
}

export const authService = {
  /**
   * Login user
   */
  async login(credentials: LoginCredentials): Promise<Token> {
    const response = await api.post<TokenResponse>('/auth/login', credentials)
    return {
      accessToken: response.data.access_token,
      tokenType: response.data.token_type,
      user: response.data.user,
    }
  },

  /**
   * Register new user
   */
  async register(data: RegisterData): Promise<Token> {
    const response = await api.post<TokenResponse>('/auth/register', {
      email: data.email,
      password: data.password,
      display_name: data.displayName,
      preferred_language: data.preferredLanguage || 'ms',
    })
    return {
      accessToken: response.data.access_token,
      tokenType: response.data.token_type,
      user: response.data.user,
    }
  },

  /**
   * Get current user info
   */
  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/auth/me')
    return response.data
  },
}

export default authService

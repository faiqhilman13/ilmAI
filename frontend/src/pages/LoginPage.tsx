import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { BookOpen, Loader2 } from 'lucide-react'
import { useAuthStore } from '../stores/authStore'
import authService from '../services/authService'

export default function LoginPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      const response = await authService.login({ email, password })
      setAuth(response.user, response.accessToken)
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail || t('networkError'))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100 py-12 px-4">
      <div className="max-w-md w-full">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-600 rounded-2xl mb-4">
            <BookOpen className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900">{t('appName')}</h1>
          <p className="text-gray-600 mt-2">{t('tagline')}</p>
        </div>

        {/* Login form */}
        <div className="card p-8">
          <h2 className="text-2xl font-semibold text-center mb-6">{t('login')}</h2>

          {error && (
            <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-4 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('email')}
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('password')}
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input"
                required
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full flex items-center justify-center"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                t('login')
              )}
            </button>
          </form>

          <p className="text-center mt-6 text-sm text-gray-600">
            {t('noAccount')}{' '}
            <Link to="/register" className="text-primary-600 hover:text-primary-700 font-medium">
              {t('register')}
            </Link>
          </p>
        </div>

        {/* Continue without account */}
        <p className="text-center mt-4 text-sm text-gray-500">
          <Link to="/" className="hover:text-gray-700">
            Teruskan tanpa akaun →
          </Link>
        </p>
      </div>
    </div>
  )
}

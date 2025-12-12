import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { Menu, BookOpen, User, LogOut, Globe } from 'lucide-react'
import { useAuthStore } from '../../stores/authStore'
import { useState } from 'react'

interface HeaderProps {
  onMenuClick: () => void
}

export default function Header({ onMenuClick }: HeaderProps) {
  const { t, i18n } = useTranslation()
  const { user, isAuthenticated, logout } = useAuthStore()
  const [showUserMenu, setShowUserMenu] = useState(false)

  const toggleLanguage = () => {
    const newLang = i18n.language === 'ms' ? 'en' : 'ms'
    i18n.changeLanguage(newLang)
  }

  return (
    <header className="bg-white border-b border-gray-200 px-4 py-3">
      <div className="flex items-center justify-between">
        {/* Left side */}
        <div className="flex items-center gap-3">
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 hover:bg-gray-100 rounded-lg"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-white" />
            </div>
            <span className="font-semibold text-lg text-gray-900 hidden sm:block">
              {t('appName')}
            </span>
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-2">
          {/* Language toggle */}
          <button
            onClick={toggleLanguage}
            className="flex items-center gap-1 px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            <Globe className="w-4 h-4" />
            <span>{i18n.language === 'ms' ? 'BM' : 'EN'}</span>
          </button>

          {/* User menu */}
          {isAuthenticated ? (
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-2 px-3 py-2 hover:bg-gray-100 rounded-lg"
              >
                <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                  <User className="w-4 h-4 text-primary-600" />
                </div>
                <span className="text-sm font-medium hidden sm:block">
                  {user?.displayName || user?.email?.split('@')[0]}
                </span>
              </button>

              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
                  <div className="px-4 py-2 border-b border-gray-100">
                    <p className="text-sm font-medium">{user?.displayName || 'User'}</p>
                    <p className="text-xs text-gray-500">{user?.email}</p>
                  </div>
                  <button
                    onClick={() => {
                      logout()
                      setShowUserMenu(false)
                    }}
                    className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                  >
                    <LogOut className="w-4 h-4" />
                    {t('logout')}
                  </button>
                </div>
              )}
            </div>
          ) : (
            <Link
              to="/login"
              className="btn-primary text-sm"
            >
              {t('login')}
            </Link>
          )}
        </div>
      </div>
    </header>
  )
}

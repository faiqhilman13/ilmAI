import { useTranslation } from 'react-i18next'
import { NavLink } from 'react-router-dom'
import { Home, MessageSquare, BookOpen, Settings, ChevronLeft, ChevronRight, Sun, Moon, Globe } from 'lucide-react'
import { useAuthStore } from '../../stores/authStore'
import { useUIStore } from '../../stores/uiStore'

interface SidebarProps {
  onClose: () => void
  mobileOpen: boolean
}

export default function Sidebar({ onClose, mobileOpen }: SidebarProps) {
  const { t, i18n } = useTranslation()
  const { user, isAuthenticated } = useAuthStore()
  const { theme, toggleTheme, sidebarCollapsed, toggleSidebarCollapsed } = useUIStore()

  const toggleLanguage = () => {
    const newLang = i18n.language === 'ms' ? 'en' : 'ms'
    i18n.changeLanguage(newLang)
  }

  const menuItems = [
    { icon: Home, label: 'Dashboard', path: '/dashboard' },
    { icon: MessageSquare, label: 'Chat Assistant', path: '/' },
    { icon: BookOpen, label: 'Knowledge Base', path: '/library' },
    { icon: Settings, label: 'Settings', path: '/settings' },
  ] as const

  return (
    <div className={['sidebar glass-panel', sidebarCollapsed ? 'collapsed' : '', mobileOpen ? 'open' : ''].filter(Boolean).join(' ')}>
      <div className="sidebar-header">
        {!sidebarCollapsed ? (
          <div className="logo-container">
            <div className="logo-icon">I</div>
            <span className="logo-text">IlmuAI</span>
          </div>
        ) : (
          <div className="logo-icon" style={{ margin: '0 auto' }}>
            I
          </div>
        )}

        <button className="collapse-btn" onClick={toggleSidebarCollapsed} type="button" aria-label="Toggle sidebar">
          {sidebarCollapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
        </button>
      </div>

      <nav className="sidebar-nav" onClick={() => mobileOpen && onClose()}>
        {menuItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            title={sidebarCollapsed ? item.label : undefined}
          >
            <item.icon size={22} className="nav-icon" />
            {!sidebarCollapsed && <span className="nav-label">{item.label}</span>}
            {item.path === '/' && !sidebarCollapsed && <span className="badge">New</span>}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <button className="theme-toggle-btn" onClick={toggleLanguage} type="button" title="Switch Language">
          <Globe size={20} />
          {!sidebarCollapsed && <span className="nav-label">{i18n.language === 'ms' ? 'BM' : 'EN'}</span>}
        </button>

        <button className="theme-toggle-btn" onClick={toggleTheme} type="button" title="Switch Theme">
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
          {!sidebarCollapsed && <span className="nav-label">{theme === 'dark' ? t('light') : t('dark')}</span>}
        </button>

        {!sidebarCollapsed && (
          <div className="user-profile">
            <div className="avatar">{(user?.displayName || user?.email || 'A')[0]?.toUpperCase()}</div>
            <div className="user-info">
              <span className="name">{user?.displayName || (isAuthenticated ? user?.email : 'Guest')}</span>
              <span className="role">{isAuthenticated ? 'Member' : 'Sign in to save chats'}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

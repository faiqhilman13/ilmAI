import { useEffect, useMemo, useState } from 'react'
import { Menu } from 'lucide-react'
import Sidebar from '../common/Sidebar'
import { useUIStore } from '../../stores/uiStore'

interface AppShellProps {
  children: React.ReactNode
}

function useIsDesktop(breakpointPx = 1024) {
  const query = useMemo(() => `(min-width: ${breakpointPx}px)`, [breakpointPx])
  const [isDesktop, setIsDesktop] = useState(() => window.matchMedia(query).matches)

  useEffect(() => {
    const mql = window.matchMedia(query)
    const onChange = () => setIsDesktop(mql.matches)
    onChange()
    mql.addEventListener('change', onChange)
    return () => mql.removeEventListener('change', onChange)
  }, [query])

  return isDesktop
}

export default function AppShell({ children }: AppShellProps) {
  const isDesktop = useIsDesktop(1024)
  const sidebarCollapsed = useUIStore((s) => s.sidebarCollapsed)
  const [mobileOpen, setMobileOpen] = useState(false)

  const leftOffset = isDesktop ? (sidebarCollapsed ? 80 : 280) : 0

  useEffect(() => {
    if (isDesktop) setMobileOpen(false)
  }, [isDesktop])

  return (
    <div className="app-container">
      {!isDesktop && (
        <button
          type="button"
          className="collapse-btn"
          onClick={() => setMobileOpen(true)}
          aria-label="Open menu"
          style={{ position: 'fixed', top: 16, left: 16, zIndex: 60 }}
        >
          <Menu size={20} />
        </button>
      )}

      {mobileOpen && !isDesktop && (
        <div
          onClick={() => setMobileOpen(false)}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.55)',
            zIndex: 45,
          }}
        />
      )}

      <Sidebar mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} />

      <main
        className="main-content"
        style={{
          marginLeft: leftOffset,
          width: isDesktop ? `calc(100% - ${leftOffset}px)` : '100%',
          transition: 'margin-left 0.25s ease, width 0.25s ease',
        }}
      >
        <div className="content-wrapper">{children}</div>
      </main>
    </div>
  )
}


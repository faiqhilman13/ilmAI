import { useEffect } from 'react'
import { useUIStore } from '../../stores/uiStore'

export default function ThemeInit() {
  const theme = useUIStore((s) => s.theme)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  return null
}


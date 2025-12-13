import AppShell from '../components/layout/AppShell'

interface PlaceholderPageProps {
  title: string
}

export default function PlaceholderPage({ title }: PlaceholderPageProps) {
  return (
    <AppShell>
      <div className="glass-panel" style={{ padding: 24, borderRadius: 20 }}>
        <h2 style={{ fontFamily: 'var(--font-serif)', fontSize: 24, color: 'var(--color-accent)' }}>{title}</h2>
        <p style={{ marginTop: 10, color: 'var(--color-text-muted)', lineHeight: 1.6 }}>
          Coming soon — this section is part of the new frontend revamp.
        </p>
      </div>
    </AppShell>
  )
}


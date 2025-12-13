import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Activity, ArrowRight, Book, Search, Shield } from 'lucide-react'
import AppShell from '../components/layout/AppShell'

export default function DashboardPage() {
  const navigate = useNavigate()

  const stats = useMemo(
    () => [
      { label: 'Verified Sources', value: '27,088', icon: Book, color: '#D4AF37' },
      { label: 'Hadith Collections', value: '18,724', icon: Shield, color: '#1B5C3E' },
      { label: 'Active Learners', value: '12.4k', icon: Activity, color: '#3b82f6' },
    ],
    [],
  )

  const recentQueries = useMemo(
    () => [
      { query: "Conditions for valid prayer (Shafi'i)", time: '2 hours ago' },
      { query: 'Zakat calculation on gold', time: 'Yesterday' },
      { query: 'Understanding Surah Al-Fatiha', time: '2 days ago' },
    ],
    [],
  )

  return (
    <AppShell>
      <div className="dashboard-container">
        <div className="hero-section fade-in">
          <h1 className="hero-title">
            Knowledge Without <span className="text-gold">Barriers.</span>
            <br />
            Wisdom Without <span className="text-gold">Boundaries.</span>
          </h1>
          <p className="hero-subtitle">
            Access authentic Islamic scholarship powered by advanced AI. Verified, contextual, and tailored for the
            Malaysian Ummah.
          </p>

          <div className="search-bar-container">
            <div className="search-input-wrapper">
              <Search className="search-icon" size={24} />
              <input
                type="text"
                placeholder="Ask a question about Islamic jurisprudence, history, or spirituality..."
                className="search-input"
              />
              <button className="search-button" type="button" onClick={() => navigate('/')}>
                Ask IlmuAI
              </button>
            </div>
            <div className="search-tags">
              <span>Popular:</span>
              <span className="tag" onClick={() => navigate('/')}>
                Syarat Sah Solat
              </span>
              <span className="tag" onClick={() => navigate('/')}>
                Zakat Fitrah
              </span>
              <span className="tag" onClick={() => navigate('/')}>
                Puasa Ganti
              </span>
            </div>
          </div>
        </div>

        <div className="stats-grid">
          {stats.map((stat) => (
            <div key={stat.label} className="stat-card glass-panel">
              <div className="stat-icon-wrapper" style={{ backgroundColor: `${stat.color}20` }}>
                <stat.icon size={24} color={stat.color} />
              </div>
              <div className="stat-content">
                <span className="stat-value">{stat.value}</span>
                <span className="stat-label">{stat.label}</span>
              </div>
            </div>
          ))}
        </div>

        <div className="content-grid">
          <div className="section-card glass-panel large">
            <div className="card-header">
              <h3>Daily Wisdom</h3>
              <span className="source-badge">Sahih Al-Bukhari</span>
            </div>
            <div className="wisdom-content">
              <p className="arabic-text">إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ</p>
              <p className="translation">"actions are but by intentions"</p>
              <p className="commentary">
                This fundamental hadith emphasizes that the validity and reward of deeds depend primarily on the
                intention behind them. In the Shafi'i school, Niyyah (intention) is a pillar (Rukun) for acts of worship
                like Prayer and Fasting.
              </p>
            </div>
          </div>

          <div className="section-card glass-panel">
            <div className="card-header">
              <h3>Recent Activity</h3>
              <button className="view-all" type="button">
                View All
              </button>
            </div>
            <div className="activity-list">
              {recentQueries.map((item) => (
                <div key={item.query} className="activity-item">
                  <div className="activity-icon">
                    <Search size={14} />
                  </div>
                  <div className="activity-details">
                    <span className="query-text">{item.query}</span>
                    <span className="time-text">{item.time}</span>
                  </div>
                  <ArrowRight size={14} className="arrow-icon" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  )
}


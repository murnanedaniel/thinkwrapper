import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import axios from 'axios'

function Dashboard({ isLoggedIn, user }) {
  const [newsletters, setNewsletters] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    if (!isLoggedIn) {
      setIsLoading(false)
      return
    }

    async function fetchNewsletters() {
      try {
        const response = await axios.get('/api/newsletters')
        if (response.data.success) {
          setNewsletters(response.data.data)
        } else {
          setError('Failed to load newsletters')
        }
      } catch (err) {
        if (err.response?.status === 401) {
          setError('Please log in to view your newsletters')
        } else {
          setError('Failed to load newsletters')
        }
      } finally {
        setIsLoading(false)
      }
    }
    fetchNewsletters()
  }, [isLoggedIn])

  if (!isLoggedIn) {
    return (
      <div className="dashboard container" style={{ textAlign: 'center', padding: '3rem' }}>
        <h1>Your Newsletters</h1>
        <p>Please log in to view your newsletters.</p>
        <Link to="/login" className="btn btn-primary">Log In</Link>
      </div>
    )
  }

  if (isLoading) return <div className="loading">Loading your newsletters...</div>
  if (error) return <div className="error container">{error}</div>

  return (
    <div className="dashboard container">
      <div className="dashboard-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '2rem 0' }}>
        <h1>Your Newsletters</h1>
        <Link to="/create" className="btn btn-primary">Create New</Link>
      </div>

      {user && (
        <div style={{ marginBottom: '1rem', padding: '0.75rem 1rem', background: '#f0f0f0', borderRadius: '4px', fontSize: '0.9rem' }}>
          Subscription: <strong>{user.subscription_status || 'None'}</strong>
          {user.has_subscription && ' — Active'}
        </div>
      )}

      {newsletters.length === 0 ? (
        <div className="empty-state" style={{ textAlign: 'center', padding: '3rem' }}>
          <p>You don&apos;t have any newsletters yet.</p>
          <Link to="/create" className="btn btn-primary">Create Your First Newsletter</Link>
        </div>
      ) : (
        <div className="newsletters-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
          {newsletters.map(newsletter => (
            <div key={newsletter.id} className="newsletter-card" style={{ background: 'white', padding: '1.5rem', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.12)' }}>
              <h2 style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>{newsletter.name}</h2>
              <p style={{ color: '#666' }}>Topic: {newsletter.topic}</p>
              <p>Schedule: {newsletter.schedule}</p>
              <p>Issues sent: {newsletter.issue_count}</p>
              {newsletter.last_sent_at && <p>Last sent: {new Date(newsletter.last_sent_at).toLocaleDateString()}</p>}
              <div style={{ marginTop: '1rem' }}>
                <span style={{
                  padding: '0.25rem 0.75rem', borderRadius: '12px', fontSize: '0.8rem',
                  background: newsletter.status === 'active' ? '#e8f5e9' : '#fff3e0',
                  color: newsletter.status === 'active' ? '#2e7d32' : '#e65100',
                }}>
                  {newsletter.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default Dashboard

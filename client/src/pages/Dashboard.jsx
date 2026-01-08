import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import NewsletterGenerator from '../components/NewsletterGenerator'

function Dashboard() {
  const [newsletters, setNewsletters] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [generatingNewsletter, setGeneratingNewsletter] = useState(null)
  const [userEmail, setUserEmail] = useState('murnane2@gmail.com') // Default fallback

  useEffect(() => {
    // Fetch authenticated user's email
    async function fetchUser() {
      try {
        const response = await axios.get('/api/auth/user')
        if (response.data.authenticated && response.data.email) {
          setUserEmail(response.data.email)
        }
      } catch (err) {
        console.error('Failed to fetch user email:', err)
      }
    }
    fetchUser()
  }, [])

  useEffect(() => {
    async function fetchNewsletters() {
      try {
        const response = await axios.get('/api/newsletters')
        if (response.data.success) {
          setNewsletters(response.data.newsletters.map(nl => ({
            id: nl.id,
            name: nl.name,
            topic: nl.topic,
            schedule: nl.schedule,
            style: 'professional', // Default style for existing newsletters
            lastSent: nl.last_sent_at ? new Date(nl.last_sent_at).toISOString().split('T')[0] : null,
            issueCount: nl.issue_count
          })))
        }
      } catch (err) {
        setError('Failed to load newsletters')
      } finally {
        setIsLoading(false)
      }
    }
    fetchNewsletters()
  }, [])

  const handleGenerateNow = (newsletter) => {
    setGeneratingNewsletter(newsletter)
  }

  const handleCloseGenerator = () => {
    setGeneratingNewsletter(null)
  }

  if (isLoading) return <div className="loading">Loading your newsletters...</div>
  if (error) return <div className="error-message">{error}</div>

  return (
    <>
      <div className="dashboard container">
        <div className="dashboard-header">
          <h1>Your Newsletters</h1>
          <Link to="/create" className="btn btn-primary">
            Create New
          </Link>
        </div>

        {newsletters.length === 0 ? (
          <div className="empty-state">
            <p>You don't have any newsletters yet.</p>
            <Link to="/create" className="btn btn-primary">
              Create Your First Newsletter
            </Link>
          </div>
        ) : (
          <div className="newsletters-grid">
            {newsletters.map(newsletter => (
              <div key={newsletter.id} className="newsletter-card">
                <h2>{newsletter.name}</h2>
                <p className="newsletter-topic">{newsletter.topic}</p>
                <div className="newsletter-meta">
                  <span className="meta-item">
                    <strong>Schedule:</strong> {newsletter.schedule}
                  </span>
                  <span className="meta-item">
                    <strong>Issues:</strong> {newsletter.issueCount}
                  </span>
                  {newsletter.lastSent && (
                    <span className="meta-item">
                      <strong>Last sent:</strong> {newsletter.lastSent}
                    </span>
                  )}
                </div>
                <div className="card-actions">
                  <button 
                    className="btn btn-primary"
                    onClick={() => handleGenerateNow(newsletter)}
                    disabled={generatingNewsletter && generatingNewsletter.id === newsletter.id}
                  >
                    {generatingNewsletter && generatingNewsletter.id === newsletter.id ? 'Generating...' : 'Generate Now'}
                  </button>
                  <Link to={`/newsletter/${newsletter.id}/edit`} className="btn btn-outline">
                    Edit
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {generatingNewsletter && (
        <NewsletterGenerator
          newsletter={generatingNewsletter}
          onClose={handleCloseGenerator}
          userEmail={userEmail}
        />
      )}
    </>
  )
}

export default Dashboard 
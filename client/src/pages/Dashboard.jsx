import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'

function Dashboard() {
  const [newsletters, setNewsletters] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    // In a real app, we would fetch actual data from the API
    // For now, we'll simulate it with mock data
    const mockNewsletters = [
      {
        id: 1,
        name: 'AI Weekly',
        topic: 'Artificial Intelligence',
        schedule: 'weekly',
        lastSent: '2025-05-15',
        issueCount: 12
      },
      {
        id: 2,
        name: 'Tech Roundup',
        topic: 'Technology News',
        schedule: 'monthly',
        lastSent: '2025-05-01',
        issueCount: 3
      }
    ]
    
    // Simulate API call
    setTimeout(() => {
      setNewsletters(mockNewsletters)
      setIsLoading(false)
    }, 500)
    
    // Real implementation would be:
    // async function fetchNewsletters() {
    //   try {
    //     const response = await axios.get('/api/newsletters')
    //     setNewsletters(response.data)
    //   } catch (err) {
    //     setError('Failed to load newsletters')
    //   } finally {
    //     setIsLoading(false)
    //   }
    // }
    // fetchNewsletters()
  }, [])

  const handlePause = (id) => {
    // In a real app, would call API to pause/unpause
    setNewsletters(newsletters.map(nl => 
      nl.id === id ? {...nl, paused: !nl.paused} : nl
    ))
  }

  if (isLoading) return <div className="loading">Loading your newsletters...</div>
  if (error) return <div className="error">{error}</div>

  return (
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
              <p className="topic">Topic: {newsletter.topic}</p>
              <p>Schedule: {newsletter.schedule}</p>
              <p>Last sent: {newsletter.lastSent}</p>
              <p>Total issues: {newsletter.issueCount}</p>
              <div className="card-actions">
                <button 
                  className="btn btn-outline"
                  onClick={() => handlePause(newsletter.id)}
                >
                  {newsletter.paused ? 'Resume' : 'Pause'}
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
  )
}

export default Dashboard 
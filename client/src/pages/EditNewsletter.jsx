import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import axios from 'axios'

function EditNewsletter() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    topic: '',
    schedule: 'weekly',
    style: 'professional'
  })

  useEffect(() => {
    async function fetchNewsletter() {
      try {
        const response = await axios.get(`/api/newsletters/${id}`)
        if (response.data.success) {
          const nl = response.data.newsletter
          setFormData({
            name: nl.name || '',
            topic: nl.topic || '',
            schedule: nl.schedule || 'weekly',
            style: nl.style || 'professional'
          })
        } else {
          setError('Newsletter not found')
        }
      } catch (err) {
        setError('Failed to load newsletter')
        console.error(err)
      } finally {
        setIsLoading(false)
      }
    }
    fetchNewsletter()
  }, [id])

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const response = await axios.put(`/api/newsletters/${id}`, formData)
      if (response.data.success) {
        navigate('/dashboard')
      } else {
        setError('Failed to update newsletter')
      }
    } catch (err) {
      setError('Failed to update newsletter')
      console.error(err)
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  if (isLoading) return <div className="loading">Loading newsletter...</div>
  if (error) return <div className="error-message">{error}</div>

  return (
    <div className="create-newsletter container">
      <div className="create-header">
        <h1>Edit Newsletter</h1>
        <p className="subtitle">Update your newsletter settings</p>
      </div>
      
      <form onSubmit={handleSubmit} className="newsletter-form">
        <div className="form-group">
          <label htmlFor="name">Newsletter Name</label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
            placeholder="My Awesome Newsletter"
            className="form-input"
          />
        </div>

        <div className="form-group">
          <label htmlFor="topic">Topic</label>
          <input
            type="text"
            id="topic"
            name="topic"
            value={formData.topic}
            onChange={handleChange}
            required
            placeholder="AI, Technology, Finance, etc."
            className="form-input"
          />
          <p className="form-hint">Describe what your newsletter should cover</p>
        </div>

        <div className="form-group">
          <label htmlFor="schedule">Schedule</label>
          <select
            id="schedule"
            name="schedule"
            value={formData.schedule}
            onChange={handleChange}
            className="form-select"
          >
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="biweekly">Bi-weekly</option>
            <option value="monthly">Monthly</option>
          </select>
        </div>

        <div className="form-actions" style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
          <button type="button" className="btn btn-outline" onClick={() => navigate('/dashboard')}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary btn-large">
            Save Changes
          </button>
        </div>
      </form>
      
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
    </div>
  )
}

export default EditNewsletter

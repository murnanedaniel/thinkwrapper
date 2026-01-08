import { useState } from 'react'
import axios from 'axios'

function CreateNewsletter() {
  const [formData, setFormData] = useState({
    name: '',
    topic: '',
    schedule: 'weekly',
    style: 'professional'
  })
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)
    
    try {
      // Create newsletter in database
      const response = await axios.post('/api/newsletters', {
        name: formData.name,
        topic: formData.topic,
        schedule: formData.schedule
      })
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.error || 'An error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="create-newsletter container">
      <div className="create-header">
        <h1>Create Your Newsletter</h1>
        <p className="subtitle">Set up an AI-powered newsletter on any topic</p>
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
        
        <button 
          type="submit" 
          className="btn btn-primary btn-large"
          disabled={isLoading}
        >
          {isLoading ? 'Creating...' : 'Create Newsletter'}
        </button>
      </form>
      
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
      
      {result && (
        <div className="success-message">
          <h3>Newsletter Created!</h3>
          <p>Your first issue will be generated according to your selected schedule.</p>
        </div>
      )}
    </div>
  )
}

export default CreateNewsletter 
import { useState } from 'react'
import axios from 'axios'

function CreateNewsletter() {
  const [formData, setFormData] = useState({
    name: '',
    topic: '',
    schedule: 'weekly'
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
      const response = await axios.post('/api/generate', formData)
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.error || 'An error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="create-newsletter container">
      <h1>Create Your Newsletter</h1>
      
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
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="schedule">Schedule</label>
          <select
            id="schedule"
            name="schedule"
            value={formData.schedule}
            onChange={handleChange}
          >
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="biweekly">Bi-weekly</option>
            <option value="monthly">Monthly</option>
          </select>
        </div>
        
        <button 
          type="submit" 
          className="btn btn-primary"
          disabled={isLoading}
        >
          {isLoading ? 'Generating...' : 'Create Newsletter'}
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
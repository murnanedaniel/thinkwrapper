import { useState } from 'react'

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
    setResult(null)
    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to create newsletter')
      }
      const data = await response.json()
      setResult({ message: data.message || 'Newsletter created and issue generated!' })
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto py-12 px-4">
      <h1 className="text-2xl text-gray-900 mb-10 text-center font-normal">
        Create Your Newsletter
      </h1>
      
      <div className="border border-gray-300 rounded">
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div>
            <label htmlFor="name" className="block text-sm text-gray-700 mb-1">
              Newsletter Name
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              placeholder="e.g., AI Insights Weekly"
              className="w-full px-3 py-2 border border-gray-300 rounded placeholder-gray-400 focus:outline-none focus:border-accent-500"
            />
          </div>
          
          <div>
            <label htmlFor="topic" className="block text-sm text-gray-700 mb-1">
              Topic
            </label>
            <input
              type="text"
              id="topic"
              name="topic"
              value={formData.topic}
              onChange={handleChange}
              required
              placeholder="e.g., Artificial Intelligence, Sustainable Energy"
              className="w-full px-3 py-2 border border-gray-300 rounded placeholder-gray-400 focus:outline-none focus:border-accent-500"
            />
          </div>
          
          <div>
            <label htmlFor="schedule" className="block text-sm text-gray-700 mb-1">
              Schedule
            </label>
            <select
              id="schedule"
              name="schedule"
              value={formData.schedule}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded bg-white focus:outline-none focus:border-accent-500"
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="biweekly">Bi-weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>
          
          <button 
            type="submit" 
            className={`w-full px-4 py-2 border border-gray-300 rounded text-gray-800 hover:border-gray-400 ${isLoading ? 'opacity-70 cursor-wait' : ''}`}
            disabled={isLoading}
          >
            {isLoading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-gray-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Generating...
              </span>
            ) : 'Create Newsletter'}
          </button>
        </form>
      </div>
      
      {error && (
        <div className="mt-6 border-l-4 border-red-400 p-4">
          <div className="flex">
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}
      
      {result && result.message && (
        <div className="mt-6 border-l-4 border-green-400 p-4">
          <div className="flex">
            <div className="ml-3">
              <p className="text-sm text-green-800">{result.message}</p>
              <a href="/dashboard" className="text-indigo-600 hover:underline text-sm">Go to Dashboard</a>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default CreateNewsletter 
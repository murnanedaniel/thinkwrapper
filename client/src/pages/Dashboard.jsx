import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

function Dashboard() {
  const [newsletters, setNewsletters] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchNewsletters = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const response = await fetch('/api/newsletters')
        if (!response.ok) {
          if (response.status === 401) {
            setError('Please log in to view your newsletters.')
            return
          }
          const errorData = await response.json()
          throw new Error(errorData.error || 'Failed to fetch newsletters')
        }
        const data = await response.json()
        setNewsletters(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setIsLoading(false)
      }
    }

    fetchNewsletters()
  }, [])

  if (isLoading) return (
    <div className="max-w-4xl mx-auto py-16 px-4 text-center">
      <p className="text-gray-600">Loading your newsletters...</p>
    </div>
  )
  
  if (error) return (
    <div className="max-w-4xl mx-auto py-16 px-4 text-center">
      <p className="text-red-600 text-lg">{error}</p>
      {error === 'Please log in to view your newsletters.' && (
        <Link 
          to="/login" 
          className="mt-4 inline-block px-6 py-2 border border-transparent text-base font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
        >
          Go to Login
        </Link>
      )}
    </div>
  )

  return (
    <div className="max-w-4xl mx-auto py-12 px-4">
      <div className="flex justify-between items-center mb-10">
        <h1 className="text-3xl font-bold text-gray-800">Your Newsletters</h1>
        <Link 
          to="/create" 
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          Create New Newsletter
        </Link>
      </div>

      {newsletters.length === 0 ? (
        <div className="text-center py-20 bg-white shadow-sm rounded-lg">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path vectorEffect="non-scaling-stroke" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
          </svg>
          <h3 className="mt-2 text-lg font-medium text-gray-900">No newsletters yet</h3>
          <p className="mt-1 text-sm text-gray-500">Get started by creating your first newsletter.</p>
          <div className="mt-6">
            <Link 
              to="/create" 
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Create First Newsletter
            </Link>
          </div>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul role="list" className="divide-y divide-gray-200">
            {newsletters.map(newsletter => (
              <li key={newsletter.id}>
                <Link to={`/newsletter/${newsletter.id}`} className="block hover:bg-gray-50">
                  <div className="px-4 py-4 sm:px-6">
                    <div className="flex items-center justify-between">
                      <p className="text-lg font-medium text-indigo-600 truncate">{newsletter.name}</p>
                      <div className="ml-2 flex-shrink-0 flex">
                        <Link 
                          to={`/newsletter/${newsletter.id}/edit`}
                          onClick={(e) => e.stopPropagation()}
                          className="ml-3 px-3 py-1 border border-gray-300 rounded text-sm text-gray-700 hover:border-gray-400 hover:bg-gray-100"
                        >
                          Edit
                        </Link>
                      </div>
                    </div>
                    <div className="mt-2 sm:flex sm:justify-between">
                      <div className="sm:flex">
                        <p className="flex items-center text-sm text-gray-500">
                          <svg className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                            <path fillRule="evenodd" d="M17.707 9.293a1 1 0 010 1.414l-7 7a1 1 0 01-1.414 0l-7-7A.997.997 0 012 10V5a1 1 0 011-1h12a1 1 0 011 1v4.293zM14 5H4v5.293l6 6 6-6V5z" clipRule="evenodd" />
                            <path d="M6 7a1 1 0 11-2 0 1 1 0 012 0z" />
                          </svg>
                          Topic: {newsletter.topic}
                        </p>
                        <p className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0 sm:ml-6">
                          <svg className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                          </svg>
                          Schedule: {newsletter.schedule || 'Not set'}
                        </p>
                      </div>
                      <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                        <svg className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                           <path fillRule="evenodd" d="M2 5a2 2 0 012-2h8l4 4v10a2 2 0 01-2 2H4a2 2 0 01-2-2V5zm2-1a1 1 0 00-1 1v10a1 1 0 001 1h10a1 1 0 001-1V9h-4V4H4zm5 4a1 1 0 100 2h4a1 1 0 100-2H9zm0 4a1 1 0 100 2h2a1 1 0 100-2H9z" clipRule="evenodd" />
                        </svg>
                        {newsletter.issue_count} Issues
                      </div>
                    </div>
                     <div className="mt-2 text-xs text-gray-400">
                        Created: {new Date(newsletter.created_at).toLocaleDateString()} | Last Sent: {newsletter.last_sent_at ? new Date(newsletter.last_sent_at).toLocaleDateString() : 'Never'}
                    </div>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export default Dashboard 
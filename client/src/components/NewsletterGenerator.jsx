import { useState, useEffect } from 'react'
import axios from 'axios'

function NewsletterGenerator({ newsletter, onClose, userEmail = 'murnane2@gmail.com' }) {
  const [stage, setStage] = useState('starting') // starting, topic_seeding, searching, generating, complete, error
  const [progress, setProgress] = useState(0)
  const [progressMessage, setProgressMessage] = useState('Initializing...')
  const [taskId, setTaskId] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [emailStatus, setEmailStatus] = useState(null)
  const [searchTopics, setSearchTopics] = useState([])
  const [hasStarted, setHasStarted] = useState(false)

  useEffect(() => {
    // Prevent duplicate triggers (React StrictMode runs effects twice in dev)
    if (!hasStarted) {
      setHasStarted(true)
      generateNewsletter()
    }
  }, [hasStarted])

  const generateNewsletter = async () => {
    try {
      setStage('starting')
      setProgress(5)
      setProgressMessage('Initializing newsletter generation...')

      // Start generation with schedule for date filtering
      const response = await axios.post('/api/generate', {
        newsletter_id: newsletter.id,
        topic: newsletter.topic,
        style: newsletter.style || 'professional',
        schedule: newsletter.schedule || 'weekly'
      })

      if (response.data.success) {
        setTaskId(response.data.task_id)
        setProgress(10)
        setProgressMessage('Task queued...')
        
        // Poll for task completion
        pollTaskStatus(response.data.task_id)
      } else {
        throw new Error(response.data.error || 'Failed to start generation')
      }
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Failed to generate newsletter')
      setStage('error')
    }
  }

  const pollTaskStatus = async (id) => {
    const maxAttempts = 120 // 120 seconds max (increased for multi-search)
    let attempts = 0
    let isComplete = false

    const poll = setInterval(async () => {
      // Don't continue polling if we've already completed
      if (isComplete) {
        clearInterval(poll)
        return
      }

      attempts++
      
      try {
        const response = await axios.get(`/api/task/${id}`)
        const { state, result: taskResult, progress: progressData } = response.data

        if (state === 'SUCCESS') {
          isComplete = true
          clearInterval(poll)
          
          // Only update state if we haven't already set a result
          setResult(prevResult => {
            if (prevResult) return prevResult // Already have a result, don't update
            return taskResult
          })
          setProgress(100)
          setStage('complete')
          setProgressMessage('Newsletter generated successfully!')
          
          // Store search topics if available
          if (taskResult && taskResult.search_topics) {
            setSearchTopics(taskResult.search_topics)
          }
        } else if (state === 'FAILURE' || state === 'REVOKED') {
          isComplete = true
          clearInterval(poll)
          setError('Newsletter generation failed')
          setStage('error')
        } else if (state === 'PROGRESS') {
          // Handle detailed progress updates
          if (progressData) {
            setStage(progressData.stage)
            setProgress(progressData.percent)
            setProgressMessage(progressData.message)
          }
        } else if (state === 'PENDING' || state === 'STARTED') {
          // Update progress with generic message
          const progressValue = 10 + (attempts / maxAttempts) * 20
          setProgress(Math.min(progressValue, 30))
          setProgressMessage('Processing...')
        }

        if (attempts >= maxAttempts) {
          isComplete = true
          clearInterval(poll)
          setError('Generation timeout - please try again')
          setStage('error')
        }
      } catch (err) {
        isComplete = true
        clearInterval(poll)
        setError('Failed to check generation status')
        setStage('error')
      }
    }, 1000)

    // Cleanup function
    return () => {
      isComplete = true
      clearInterval(poll)
    }
  }

  const sendEmail = async (newsletterData) => {
    try {
      setEmailStatus('sending')
      
      const response = await axios.post('/api/send-newsletter', {
        to_email: userEmail, // Use authenticated user's email
        subject: newsletterData.subject,
        content: newsletterData.content
      })

      if (response.data.success) {
        setEmailStatus('sent')
      } else {
        setEmailStatus('failed')
      }
    } catch (err) {
      setEmailStatus('failed')
    }
  }

  const getStageText = () => {
    return progressMessage || 'Processing...'
  }

  const getStageIcon = (stageName) => {
    if (stage === 'error') return '❌'
    
    const stageOrder = ['starting', 'topic_seeding', 'searching', 'generating', 'complete']
    const currentIndex = stageOrder.indexOf(stage)
    const stageIndex = stageOrder.indexOf(stageName)
    
    if (currentIndex > stageIndex) return '✓'
    if (currentIndex === stageIndex) return getLoadingIcon(stageName)
    return '○'
  }

  const getLoadingIcon = (stageName) => {
    switch (stageName) {
      case 'topic_seeding': return '🌱'
      case 'searching': return '🔍'
      case 'generating': return '✍️'
      case 'complete': return '✓'
      default: return '⏳'
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content newsletter-generator" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Generating: {newsletter.name}</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="generator-body">
          {/* Progress Bar */}
          <div className="progress-section">
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="progress-text">{getStageText()}</p>
          </div>

          {/* Stage Indicators */}
          <div className="stage-indicators">
            <div className={`stage-item ${['topic_seeding', 'searching', 'generating', 'complete'].includes(stage) ? 'active' : ''} ${!['starting', 'topic_seeding', 'error'].includes(stage) ? 'completed' : ''}`}>
              <div className="stage-icon">
                {getStageIcon('topic_seeding')}
              </div>
              <span>Topic Seeding</span>
            </div>
            <div className={`stage-item ${['searching', 'generating', 'complete'].includes(stage) ? 'active' : ''} ${['generating', 'complete'].includes(stage) ? 'completed' : ''}`}>
              <div className="stage-icon">
                {getStageIcon('searching')}
              </div>
              <span>Multi-Search</span>
            </div>
            <div className={`stage-item ${['generating', 'complete'].includes(stage) ? 'active' : ''} ${stage === 'complete' ? 'completed' : ''}`}>
              <div className="stage-icon">
                {getStageIcon('generating')}
              </div>
              <span>Generating</span>
            </div>
            <div className={`stage-item ${stage === 'complete' ? 'active completed' : ''}`}>
              <div className="stage-icon">
                {getStageIcon('complete')}
              </div>
              <span>Complete</span>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="error-message">
              <strong>Error:</strong> {error}
            </div>
          )}

          {/* Result Display */}
          {result && (
            <div className="result-section">
              <h3>Preview</h3>
              
              {result.search_topics && result.search_topics.length > 0 && (
                <div className="search-topics-section">
                  <p><strong>🌱 Topics Searched ({result.search_topics.length}):</strong></p>
                  <ul className="search-topics-list">
                    {result.search_topics.map((topic, idx) => (
                      <li key={idx}>{topic}</li>
                    ))}
                  </ul>
                  {result.freshness && (
                    <p className="freshness-info"><em>Time period: {result.freshness}</em></p>
                  )}
                </div>
              )}
              
              <div className="newsletter-preview">
                <h4 className="preview-subject">{result.subject}</h4>
                <div 
                  className="preview-content" 
                  dangerouslySetInnerHTML={{ __html: result.content?.substring(0, 500) + '...' }}
                />
                {result.articles && result.articles.length > 0 && (
                  <div className="preview-articles">
                    <p><strong>📰 Sources ({result.articles.length} unique articles):</strong></p>
                    <ul>
                      {result.articles.slice(0, 5).map((article, idx) => (
                        <li key={idx}>
                          <a href={article.url} target="_blank" rel="noopener noreferrer">
                            {article.title}
                          </a>
                          {article.search_topic && (
                            <span className="article-topic"> (from: {article.search_topic})</span>
                          )}
                        </li>
                      ))}
                      {result.articles.length > 5 && (
                        <li><em>...and {result.articles.length - 5} more</em></li>
                      )}
                    </ul>
                  </div>
                )}
              </div>

              {emailStatus && (
                <div className={`email-status ${emailStatus}`}>
                  {emailStatus === 'sending' && '📧 Sending email...'}
                  {emailStatus === 'sent' && '✅ Email sent successfully!'}
                  {emailStatus === 'failed' && '❌ Email sending failed'}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="modal-footer">
          {stage === 'complete' && (
            <>
              <button 
                className="btn btn-secondary" 
                onClick={() => sendEmail(result)}
                disabled={emailStatus === 'sending'}
              >
                {emailStatus === 'sending' ? 'Sending...' : emailStatus === 'sent' ? 'Email Sent ✓' : 'Send Newsletter'}
              </button>
              <button className="btn btn-primary" onClick={onClose}>
                Done
              </button>
            </>
          )}
          {stage === 'error' && (
            <button className="btn btn-primary" onClick={onClose}>
              Close
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default NewsletterGenerator

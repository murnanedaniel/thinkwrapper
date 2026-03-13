import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { getConfig } from '../config'

const STATES = {
  INPUT: 'INPUT',
  GENERATING: 'GENERATING',
  PREVIEW: 'PREVIEW',
  NEEDS_LOGIN: 'NEEDS_LOGIN',
  NEEDS_PAYMENT: 'NEEDS_PAYMENT',
  CREATING: 'CREATING',
  SUCCESS: 'SUCCESS',
}

function CreateNewsletter({ isLoggedIn, user, paddleReady, refreshUser }) {
  const navigate = useNavigate()
  const [step, setStep] = useState(STATES.INPUT)
  const [formData, setFormData] = useState({
    topic: '',
    description: '',
    style: 'professional',
    schedule: 'weekly',
    name: '',
  })
  const [preview, setPreview] = useState(null)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [taskId, setTaskId] = useState(null)
  const [stages, setStages] = useState({ searching: [], reading: [], writing: [] })
  const [activeStage, setActiveStage] = useState(null) // 'searching' | 'reading' | 'writing' | 'done'

  const classifyMessage = (status) => {
    if (status.startsWith('Searching:')) return { stage: 'searching', detail: status.slice(10).trim() }
    if (status.startsWith('Reading article:')) return { stage: 'reading', detail: status.slice(16).trim() }
    if (status.startsWith('Writing')) return { stage: 'writing', detail: null }
    return null
  }

  // Poll task progress when generating
  useEffect(() => {
    if (!taskId || step !== STATES.GENERATING) return
    const poll = setInterval(async () => {
      try {
        const res = await axios.get(`/api/task/${taskId}`)
        const { state, status, result: taskResult } = res.data
        if (state === 'PROGRESS' && status) {
          const classified = classifyMessage(status)
          if (classified) {
            setActiveStage(classified.stage)
            if (classified.detail) {
              setStages(s => {
                const prev = s[classified.stage]
                if (prev[prev.length - 1] === classified.detail) return s
                return { ...s, [classified.stage]: [...prev, classified.detail] }
              })
            }
          }
        } else if (state === 'SUCCESS' && taskResult) {
          clearInterval(poll)
          setActiveStage('done')
          setPreview(taskResult)
          setStep(STATES.PREVIEW)
          setTaskId(null)
        } else if (state === 'FAILURE') {
          clearInterval(poll)
          setError(status || 'Generation failed')
          setStep(STATES.INPUT)
          setTaskId(null)
        }
      } catch (_) {}
    }, 2000)
    return () => clearInterval(poll)
  }, [taskId, step])

  // Restore state after OAuth redirect
  useEffect(() => {
    const saved = localStorage.getItem('create_newsletter_draft')
    if (saved) {
      try {
        const { formData: savedForm, preview: savedPreview } = JSON.parse(saved)
        if (savedForm) setFormData(savedForm)
        if (savedPreview) { setPreview(savedPreview); setStep(STATES.PREVIEW) }
      } catch (_) {}
      localStorage.removeItem('create_newsletter_draft')
    }
  }, [])

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const handleGeneratePreview = async (e) => {
    e.preventDefault()
    setStep(STATES.GENERATING)
    setError(null)
    setStages({ searching: [], reading: [], writing: [] })
    setActiveStage(null)

    try {
      const response = await axios.post('/api/newsletter/preview', {
        topic: formData.topic,
        description: formData.description,
        style: formData.style,
      })
      if (response.data.success && response.data.data?.task_id) {
        setTaskId(response.data.data.task_id)
        setProgressMsg('Starting...')
      } else {
        setError(response.data.error || 'Generation failed')
        setStep(STATES.INPUT)
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to generate preview')
      setStep(STATES.INPUT)
    }
  }

  const handleConfirm = async () => {
    if (!isLoggedIn) {
      setStep(STATES.NEEDS_LOGIN)
      return
    }
    if (!user?.has_subscription) {
      setStep(STATES.NEEDS_PAYMENT)
      openPaddleCheckout()
      return
    }
    await createNewsletter()
  }

  const openPaddleCheckout = () => {
    const config = getConfig()
    if (!paddleReady || !config.paddle_price_id) {
      setError('Payment system not configured. Please contact support.')
      setStep(STATES.PREVIEW)
      return
    }

    window.Paddle.Checkout.open({
      items: [{ priceId: config.paddle_price_id, quantity: 1 }],
      customer: { email: user?.email },
      customData: { user_email: user?.email },
      settings: {
        displayMode: 'overlay',
        variant: 'one-page',
      },
    })
  }

  // Set up Paddle event listener (called once when entering payment state)
  if (typeof window !== 'undefined' && window.Paddle && !window._paddleListenerSet) {
    window.Paddle.Update({
      eventCallback: async (event) => {
        if (event.name === 'checkout.completed') {
          setStep(STATES.CREATING)
          try {
            // Activate subscription immediately via checkout data (webhook may lag)
            const txnData = event.data?.transaction || {}
            await axios.post('/api/payment/activate-by-checkout', {
              transaction_id: txnData.id,
              customer_id: txnData.customer?.id,
            })
            if (refreshUser) await refreshUser()

            // Create the newsletter
            const response = await axios.post('/api/newsletters', {
              topic: formData.topic,
              name: formData.name || formData.topic,
              description: formData.description,
              style: formData.style,
              schedule: formData.schedule,
              subject: preview?.subject,
              content: preview?.content,
            })
            if (response.data.success) {
              setResult(response.data.data)
              setStep(STATES.SUCCESS)
            } else {
              setError(response.data.error)
              setStep(STATES.PREVIEW)
            }
          } catch (err) {
            setError(err.response?.data?.error || 'Failed to create newsletter after payment')
            setStep(STATES.PREVIEW)
          }
        } else if (event.name === 'checkout.closed') {
          if (step !== STATES.CREATING && step !== STATES.SUCCESS) {
            setStep(STATES.PREVIEW)
          }
        }
      }
    })
    window._paddleListenerSet = true
  }

  const createNewsletter = async () => {
    setStep(STATES.CREATING)
    setError(null)

    try {
      const response = await axios.post('/api/newsletters', {
        topic: formData.topic,
        name: formData.name || formData.topic,
        description: formData.description,
        style: formData.style,
        schedule: formData.schedule,
        subject: preview.subject,
        content: preview.content,
      })
      if (response.data.success) {
        setResult(response.data.data)
        setStep(STATES.SUCCESS)
      } else {
        setError(response.data.error || 'Failed to create newsletter')
        setStep(STATES.PREVIEW)
      }
    } catch (err) {
      const msg = err.response?.data?.error || 'Failed to create newsletter'
      if (err.response?.status === 403) {
        setStep(STATES.NEEDS_PAYMENT)
        setError('Payment is still processing. Please wait a moment and try again.')
      } else if (err.response?.status === 401) {
        setStep(STATES.NEEDS_LOGIN)
      } else {
        setError(msg)
        setStep(STATES.PREVIEW)
      }
    }
  }

  const handleLogin = () => {
    localStorage.setItem('create_newsletter_draft', JSON.stringify({ formData, preview }))
    window.location.href = '/api/auth/login?next=/create'
  }

  // --- RENDER ---

  if (step === STATES.SUCCESS) {
    return (
      <div className="create-newsletter container">
        <div className="success-panel">
          <h1>Your Newsletter is Live!</h1>
          <p>Your first issue has been {result?.email_sent ? 'sent to your email' : 'created'}.</p>
          <p>We&apos;ll send you a new issue every {formData.schedule}.</p>
          <div style={{ marginTop: '2rem' }}>
            <button className="btn btn-primary" onClick={() => navigate('/dashboard')}>
              Go to Dashboard
            </button>
            <button className="btn btn-outline" onClick={() => {
              setStep(STATES.INPUT)
              setPreview(null)
              setFormData({ topic: '', description: '', style: 'professional', schedule: 'weekly', name: '' })
            }}>
              Create Another
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="create-newsletter container">
      <h1>{step === STATES.PREVIEW ? 'Preview Your Newsletter' : 'Create Your Newsletter'}</h1>

      {error && <div className="error-message">{error}</div>}

      {(step === STATES.INPUT || step === STATES.GENERATING) && (
        <form onSubmit={handleGeneratePreview} className="newsletter-form">
          <div className="form-group">
            <label htmlFor="topic">Topic *</label>
            <input
              type="text" id="topic" name="topic"
              value={formData.topic} onChange={handleChange}
              required placeholder="e.g., AI in Healthcare, Quantum Computing"
            />
          </div>
          <div className="form-group">
            <label htmlFor="description">Description (what should the newsletter focus on?)</label>
            <textarea
              id="description" name="description" rows="3"
              value={formData.description} onChange={handleChange}
              placeholder="e.g., Recent breakthroughs, practical applications, upcoming conferences..."
              style={{ width: '100%', padding: '0.8rem', borderRadius: '4px', border: '1px solid #ddd' }}
            />
          </div>
          <div className="form-group">
            <label htmlFor="name">Newsletter Name (optional)</label>
            <input
              type="text" id="name" name="name"
              value={formData.name} onChange={handleChange}
              placeholder="e.g., The AI Health Digest"
            />
          </div>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <div className="form-group" style={{ flex: 1 }}>
              <label htmlFor="style">Style</label>
              <select id="style" name="style" value={formData.style} onChange={handleChange}>
                <option value="professional">Professional</option>
                <option value="casual">Casual</option>
                <option value="technical">Technical</option>
              </select>
            </div>
            <div className="form-group" style={{ flex: 1 }}>
              <label htmlFor="schedule">Frequency</label>
              <select id="schedule" name="schedule" value={formData.schedule} onChange={handleChange}>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="biweekly">Bi-weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>
          </div>
          <button type="submit" className="btn btn-primary" disabled={step === STATES.GENERATING}>
            {step === STATES.GENERATING ? 'Working...' : 'Generate Preview (Free)'}
          </button>
        </form>
      )}

      {step === STATES.GENERATING && taskId && (
        <div style={{ marginTop: '1.5rem' }}>
          <style>{`
            @keyframes spin { to { transform: rotate(360deg); } }
            .stage-card { border: 1px solid #e0e0e0; borderRadius: 8px; padding: 1rem 1.25rem; background: #fff; transition: all 0.3s; }
          `}</style>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            {[
              { key: 'searching', icon: '🔍', label: 'Searching' },
              { key: 'reading',   icon: '📖', label: 'Reading' },
              { key: 'writing',   icon: '✍️',  label: 'Writing' },
            ].map(({ key, icon, label }) => {
              const isActive = activeStage === key
              const isDone = activeStage !== null && ['searching','reading','writing','done'].indexOf(activeStage) > ['searching','reading','writing','done'].indexOf(key)
              const isPending = !isActive && !isDone
              const details = stages[key]
              return (
                <div key={key} style={{
                  flex: '1 1 180px', border: `1px solid ${isActive ? '#4a90e2' : isDone ? '#4caf50' : '#e0e0e0'}`,
                  borderRadius: 8, padding: '1rem 1.25rem', background: isActive ? '#f0f7ff' : isDone ? '#f0fff4' : '#fafafa',
                  transition: 'all 0.3s',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: details.length ? '0.75rem' : 0 }}>
                    <span style={{ fontSize: '1.3rem' }}>{isDone ? '✅' : icon}</span>
                    <strong style={{ color: isPending ? '#aaa' : '#333' }}>{label}</strong>
                    {isActive && <div style={{ marginLeft: 'auto', width: 12, height: 12, borderRadius: '50%', border: '2px solid #4a90e2', borderTopColor: 'transparent', animation: 'spin 0.8s linear infinite' }} />}
                  </div>
                  {details.length > 0 && (
                    <div style={{ fontSize: '0.78rem', color: '#555', lineHeight: 1.5 }}>
                      {details.map((d, i) => (
                        <div key={i} style={{ opacity: i === details.length - 1 && isActive ? 1 : 0.6, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {d}
                        </div>
                      ))}
                    </div>
                  )}
                  {key === 'writing' && isActive && (
                    <div style={{ fontSize: '0.78rem', color: '#555' }}>Composing your newsletter…</div>
                  )}
                  {isPending && <div style={{ fontSize: '0.78rem', color: '#bbb' }}>Waiting…</div>}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {step === STATES.PREVIEW && preview && (
        <div className="preview-section">
          <div style={{ marginBottom: '1rem', padding: '0.5rem 1rem', background: '#e8f4fd', borderRadius: '4px', fontSize: '0.9rem' }}>
            Sources: {preview.search_source === 'brave' || preview.search_source === 'agent' ? 'Real web articles' : 'Sample data'}
            {preview.articles?.length > 0 && ` (${preview.articles.length} articles)`}
          </div>
          <div
            className="preview-content"
            dangerouslySetInnerHTML={{ __html: preview.html_preview }}
            style={{ border: '1px solid #ddd', borderRadius: '8px', marginBottom: '1.5rem' }}
          />
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <button className="btn btn-primary" onClick={handleConfirm}>
              I want this! &mdash; $1/month
            </button>
            <button className="btn btn-outline" onClick={() => {
              setStep(STATES.GENERATING)
              setError(null)
              axios.post('/api/newsletter/preview', {
                topic: formData.topic, description: formData.description, style: formData.style,
              }).then(res => {
                if (res.data.success) { setPreview(res.data.data); setStep(STATES.PREVIEW) }
                else { setError('Regeneration failed'); setStep(STATES.PREVIEW) }
              }).catch(() => { setError('Regeneration failed'); setStep(STATES.PREVIEW) })
            }}>
              Regenerate
            </button>
            <button className="btn btn-outline" onClick={() => setStep(STATES.INPUT)}>
              Edit Topic
            </button>
          </div>
        </div>
      )}

      {step === STATES.NEEDS_LOGIN && (
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <h2>Sign up to get this newsletter</h2>
          <p style={{ margin: '1rem 0' }}>Create a free account to subscribe.</p>
          <button className="btn btn-primary" onClick={handleLogin}>
            Sign in with Google
          </button>
        </div>
      )}

      {step === STATES.NEEDS_PAYMENT && (
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <h2>Subscribe for $1/month</h2>
          <p>AI-generated newsletter on &ldquo;{formData.topic}&rdquo; delivered every {formData.schedule}.</p>
          {error && <p className="error-message">{error}</p>}
          {!error && <p style={{ color: '#888' }}>Opening payment...</p>}
          <button className="btn btn-outline" onClick={() => { setError(null); setStep(STATES.PREVIEW) }}>
            Go Back
          </button>
        </div>
      )}

      {step === STATES.CREATING && (
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <h2>Setting up your newsletter...</h2>
          <p>Sending your first issue now.</p>
        </div>
      )}
    </div>
  )
}

export default CreateNewsletter

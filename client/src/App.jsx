import { useState, useEffect, useCallback } from 'react'
import { Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import Dashboard from './pages/Dashboard'
import CreateNewsletter from './pages/CreateNewsletter'
import Login from './pages/Login'
import Header from './components/Header'
import { loadConfig, getConfig } from './config'
import './index.css'

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [paddleReady, setPaddleReady] = useState(false)

  const refreshUser = useCallback(() => {
    return fetch('/api/auth/user')
      .then(res => res.json())
      .then(data => {
        if (data.authenticated) {
          setIsLoggedIn(true)
          setUser(data)
        } else {
          setIsLoggedIn(false)
          setUser(null)
        }
        return data
      })
  }, [])

  useEffect(() => {
    // Load config and init Paddle, then check auth
    Promise.all([loadConfig(), refreshUser()])
      .then(([config]) => {
        // Initialize Paddle.js if available
        if (window.Paddle && config.paddle_client_token) {
          if (config.paddle_sandbox) {
            window.Paddle.Environment.set('sandbox')
          }
          window.Paddle.Initialize({
            token: config.paddle_client_token,
          })
          setPaddleReady(true)
        }
        setLoading(false)
      })
      .catch(err => {
        console.error('Init error:', err)
        setLoading(false)
      })
  }, [refreshUser])

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  return (
    <div className="app-container">
      <Header
        isLoggedIn={isLoggedIn}
        setIsLoggedIn={setIsLoggedIn}
        user={user}
        setUser={setUser}
      />
      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/dashboard" element={
            <Dashboard isLoggedIn={isLoggedIn} user={user} />
          } />
          <Route path="/create" element={
            <CreateNewsletter
              isLoggedIn={isLoggedIn}
              user={user}
              paddleReady={paddleReady}
              refreshUser={refreshUser}
            />
          } />
        </Routes>
      </main>
      <footer>
        <p>&copy; 2026 ThinkWrapper</p>
      </footer>
    </div>
  )
}

export default App

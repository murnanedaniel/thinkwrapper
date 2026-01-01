import { useState, useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import Dashboard from './pages/Dashboard'
import CreateNewsletter from './pages/CreateNewsletter'
import Login from './pages/Login'
import Header from './components/Header'
import './App.css'

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // Check authentication status on mount
  useEffect(() => {
    fetch('/api/auth/user')
      .then(res => res.json())
      .then(data => {
        if (data.authenticated) {
          setIsLoggedIn(true)
          setUser(data)
        }
        setLoading(false)
      })
      .catch(err => {
        console.error('Error checking auth:', err)
        setLoading(false)
      })
  }, [])

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
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/create" element={<CreateNewsletter />} />
        </Routes>
      </main>
      <footer>
        <p>© 2025 ThinkWrapper</p>
      </footer>
    </div>
  )
}

export default App 
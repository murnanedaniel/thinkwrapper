import React, { useState, useEffect } from 'react'
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import HomePage from './pages/HomePage'
import Dashboard from './pages/Dashboard'
import CreateNewsletter from './pages/CreateNewsletter'
import Header from './components/Header'
import LoginForm from './components/auth/LoginForm'
import RegistrationForm from './components/auth/RegistrationForm'

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  // Check login status on mount and on route change
  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        const response = await fetch('/auth/status')
        if (response.ok) {
          setIsLoggedIn(true)
          // If user is logged in and on an auth page, redirect to dashboard
          if (location.pathname === '/login' || location.pathname === '/register') {
            navigate('/dashboard')
          }
        } else {
          setIsLoggedIn(false)
          // If user is not logged in and on a protected route, redirect to login
          if (location.pathname === '/dashboard' || location.pathname === '/create') {
            navigate('/login')
          }
        }
      } catch (error) {
        console.error('Failed to fetch auth status:', error)
        setIsLoggedIn(false)
        // if (location.pathname === '/dashboard' || location.pathname === '/create') {
        //   navigate('/login')
        // }
      }
    }
    checkAuthStatus()
  }, [navigate, location.pathname])

  return (
    <div className="min-h-screen flex flex-col bg-white">
      <Header isLoggedIn={isLoggedIn} setIsLoggedIn={setIsLoggedIn} />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginForm setIsLoggedIn={setIsLoggedIn} />} />
          <Route path="/register" element={<RegistrationForm setIsLoggedIn={setIsLoggedIn} />} />
          {/* Protected Routes */}
          <Route 
            path="/dashboard" 
            element={isLoggedIn ? <Dashboard /> : <LoginForm setIsLoggedIn={setIsLoggedIn} />}
          />
          <Route 
            path="/create" 
            element={isLoggedIn ? <CreateNewsletter /> : <LoginForm setIsLoggedIn={setIsLoggedIn} />}
          />
        </Routes>
      </main>
      <footer className="py-6 text-center text-gray-500 text-xs border-t border-gray-100">
        <div className="container mx-auto px-4">
          <p>© 2025 ThinkWrapper</p>
        </div>
      </footer>
    </div>
  )
}

export default App 
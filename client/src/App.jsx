import { useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import Dashboard from './pages/Dashboard'
import CreateNewsletter from './pages/CreateNewsletter'
import Header from './components/Header'
import './App.css'

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  return (
    <div className="app-container">
      <Header isLoggedIn={isLoggedIn} setIsLoggedIn={setIsLoggedIn} />
      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
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
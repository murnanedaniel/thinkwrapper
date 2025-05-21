import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth0 } from '@auth0/auth0-react'
import HomePage from './pages/HomePage'
import Dashboard from './pages/Dashboard'
import CreateNewsletter from './pages/CreateNewsletter'
import Header from './components/Header'

// Protected route component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth0();
  
  if (isLoading) {
    return <div className="text-center py-10">Loading...</div>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/" />;
  }
  
  return children;
};

function App() {
  const { isLoading } = useAuth0();

  if (isLoading) {
    return <div className="text-center py-10">Loading...</div>;
  }

  return (
    <div className="min-h-screen flex flex-col bg-white">
      <Header />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<HomePage />} />
          {/* Protected Routes */}
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route 
            path="/create" 
            element={
              <ProtectedRoute>
                <CreateNewsletter />
              </ProtectedRoute>
            }
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
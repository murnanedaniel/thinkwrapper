import { Link } from 'react-router-dom'

function Header({ isLoggedIn, setIsLoggedIn, user, setUser }) {
  const handleLogout = () => {
    // Call the backend logout endpoint
    fetch('/api/auth/logout')
      .then(() => {
        setIsLoggedIn(false)
        setUser(null)
        window.location.href = '/'
      })
      .catch(err => console.error('Logout error:', err))
  }

  return (
    <header className="header">
      <div className="container header-container">
        <Link to="/" className="logo">
          ThinkWrapper
        </Link>
        <nav>
          <ul>
            {isLoggedIn ? (
              <>
                <li>
                  <Link to="/dashboard">Dashboard</Link>
                </li>
                <li>
                  <Link to="/create">Create New</Link>
                </li>
                <li>
                  <span className="user-name">{user?.name || user?.email}</span>
                </li>
                <li>
                  <button onClick={handleLogout} className="btn-link">
                    Logout
                  </button>
                </li>
              </>
            ) : (
              <>
                <li>
                  <Link to="/login">Login</Link>
                </li>
                <li>
                  <Link to="/login" className="btn btn-primary">
                    Sign Up
                  </Link>
                </li>
              </>
            )}
          </ul>
        </nav>
      </div>
    </header>
  )
}

export default Header 
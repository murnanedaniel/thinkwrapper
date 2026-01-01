import { Link, useNavigate } from 'react-router-dom'

// Route constants
const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  DASHBOARD: '/dashboard',
  CREATE: '/create',
  LOGOUT_API: '/api/auth/logout'
}

function Header({ isLoggedIn, setIsLoggedIn, user, setUser }) {
  const navigate = useNavigate()

  const handleLogout = () => {
    // Call the backend logout endpoint
    fetch(ROUTES.LOGOUT_API)
      .then(() => {
        setIsLoggedIn(false)
        setUser(null)
        navigate(ROUTES.HOME)
      })
      .catch(err => console.error('Logout error:', err))
  }

  return (
    <header className="header">
      <div className="container header-container">
        <Link to={ROUTES.HOME} className="logo">
          ThinkWrapper
        </Link>
        <nav>
          <ul>
            {isLoggedIn ? (
              <>
                <li>
                  <Link to={ROUTES.DASHBOARD}>Dashboard</Link>
                </li>
                <li>
                  <Link to={ROUTES.CREATE}>Create New</Link>
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
                  <Link to={ROUTES.LOGIN}>Login</Link>
                </li>
                <li>
                  <Link to={ROUTES.LOGIN} className="btn btn-primary">
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
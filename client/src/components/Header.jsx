import { Link } from 'react-router-dom'

function Header({ isLoggedIn, setIsLoggedIn }) {
  const handleLogout = () => {
    // In a real app, we would call an API endpoint to logout
    setIsLoggedIn(false)
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
                  <Link to="/signup" className="btn btn-primary">
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
import { Link } from 'react-router-dom'

function Header({ isLoggedIn, setIsLoggedIn }) {
  const handleLogout = () => {
    // In a real app, we would call an API endpoint to logout
    setIsLoggedIn(false)
  }

  return (
    <header className="border-b border-gray-100 py-4">
      <div className="container mx-auto px-4 md:px-8 flex justify-between items-center">
        <Link to="/" className="text-xl font-normal text-gray-900">
          ThinkWrapper
        </Link>
        <nav>
          <ul className="flex space-x-8 items-center">
            {isLoggedIn ? (
              <>
                <li>
                  <Link 
                    to="/dashboard" 
                    className="text-gray-700 hover:text-gray-900"
                  >
                    Dashboard
                  </Link>
                </li>
                <li>
                  <Link 
                    to="/create"
                    className="text-gray-700 hover:text-gray-900"
                  >
                    Create New
                  </Link>
                </li>
                <li>
                  <button 
                    onClick={handleLogout} 
                    className="text-gray-700 hover:text-gray-900"
                  >
                    Logout
                  </button>
                </li>
              </>
            ) : (
              <>
                <li>
                  <Link 
                    to="/login"
                    className="text-gray-700 hover:text-gray-900"
                  >
                    Login
                  </Link>
                </li>
                <li>
                  <Link 
                    to="/signup" 
                    className="text-gray-700 hover:text-gray-900"
                  >
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
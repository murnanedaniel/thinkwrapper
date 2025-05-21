import { Link } from 'react-router-dom'
import { useAuth0 } from '@auth0/auth0-react'
import Auth0LoginButton from './Auth0LoginButton'
import Auth0LogoutButton from './Auth0LogoutButton'

function Header() {
  const { isAuthenticated, user, isLoading } = useAuth0();

  if (isLoading) {
    return (
      <header className="border-b border-gray-100 py-4">
        <div className="container mx-auto px-4 md:px-8 flex justify-between items-center">
          <Link to="/" className="text-xl font-normal text-gray-900">
            ThinkWrapper
          </Link>
          <div>Loading...</div>
        </div>
      </header>
    );
  }

  return (
    <header className="border-b border-gray-100 py-4">
      <div className="container mx-auto px-4 md:px-8 flex justify-between items-center">
        <Link to="/" className="text-xl font-normal text-gray-900">
          ThinkWrapper
        </Link>
        <nav>
          <ul className="flex space-x-8 items-center">
            {isAuthenticated ? (
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
                  <span className="text-gray-700 mr-2">
                    {user?.name || user?.email}
                  </span>
                </li>
                <li>
                  <Auth0LogoutButton />
                </li>
              </>
            ) : (
              <>
                <li>
                  <Auth0LoginButton />
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
import React from 'react';
import { Link, useNavigate } from 'react-router-dom';

function Header({ isLoggedIn, setIsLoggedIn }) {
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      const response = await fetch('/auth/logout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      if (response.ok) {
        setIsLoggedIn(false);
        navigate('/login');
      } else {
        console.error('Logout failed');
        // Optionally, show an error message to the user
      }
    } catch (error) {
      console.error('Error during logout:', error);
      // Optionally, show an error message to the user
    }
  };

  return (
    <header className="bg-white border-b border-gray-100 sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between py-4">
          <Link to="/" className="text-2xl font-bold text-gray-800 hover:text-indigo-600 transition-colors">
            ThinkWrapper
          </Link>
          <nav className="space-x-4">
            {isLoggedIn ? (
              <>
                <Link 
                  to="/dashboard" 
                  className="text-gray-600 hover:text-indigo-600 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Dashboard
                </Link>
                <Link 
                  to="/create" 
                  className="text-gray-600 hover:text-indigo-600 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Create Newsletter
                </Link>
                <button
                  onClick={handleLogout}
                  className="text-gray-600 hover:text-indigo-600 px-3 py-2 rounded-md text-sm font-medium transition-colors focus:outline-none"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link 
                  to="/login" 
                  className="text-gray-600 hover:text-indigo-600 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Login
                </Link>
                <Link 
                  to="/register" 
                  className="bg-indigo-600 text-white hover:bg-indigo-700 px-4 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Sign Up
                </Link>
              </>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
}

export default Header; 
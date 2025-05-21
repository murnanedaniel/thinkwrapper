import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';

const Auth0LoginButton = () => {
  const { loginWithRedirect } = useAuth0();

  return (
    <button 
      onClick={() => loginWithRedirect()}
      className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
    >
      Log In
    </button>
  );
};

export default Auth0LoginButton; 
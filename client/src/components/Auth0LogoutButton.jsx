import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';

const Auth0LogoutButton = () => {
  const { logout } = useAuth0();

  return (
    <button 
      onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}
      className="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
    >
      Log Out
    </button>
  );
};

export default Auth0LogoutButton; 
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Auth0Provider } from '@auth0/auth0-react'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Auth0Provider
      domain="dev-26w2jl00f1tc85cq.us.auth0.com"
      clientId="Wo2xo4VE3fHctnAzRm1U6WIzXtNkgyUY"
      authorizationParams={{
        redirect_uri: window.location.origin,
        audience: `https://dev-26w2jl00f1tc85cq.us.auth0.com/api/v2/`,
        scope: "openid profile email"
      }}
    >
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </Auth0Provider>
  </React.StrictMode>,
) 
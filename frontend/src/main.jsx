/**
 * main.jsx — the entry point of the React application.
 * React mounts the <App /> component into the #root div in index.html.
 */

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'   // Global Tailwind CSS styles
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

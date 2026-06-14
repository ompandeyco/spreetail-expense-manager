/**
 * AuthContext — React Context for sharing auth state app-wide.
 *
 * Instead of passing `user` and `login()` as props through every component,
 * we put them in a Context. Any component can read them with `useAuth()`.
 */

import { createContext, useContext, useState, useEffect } from 'react'
import { getMe, login as loginService, logout as logoutService } from '../services/authService'

// Step 1: Create the context (starts empty)
const AuthContext = createContext(null)

/**
 * Step 2: AuthProvider wraps the whole app and provides the context value.
 * Place this in main.jsx around <App />.
 */
export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)  // null = not logged in
  const [loading, setLoading] = useState(true)  // true while checking existing session

  // On first load: if a token exists in localStorage, fetch the user profile
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      getMe()
        .then(setUser)
        .catch(() => setUser(null))  // Token expired or invalid
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  // Call this from the Login page
  async function login(username, password) {
    await loginService(username, password)
    const profile = await getMe()
    setUser(profile)
  }

  // Call this from the Navbar or settings
  function logout() {
    logoutService()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

/**
 * Step 3: Custom hook so components can easily read the context.
 * Usage: const { user, login, logout } = useAuth()
 */
export function useAuth() {
  return useContext(AuthContext)
}

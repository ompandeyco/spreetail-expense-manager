/**
 * ProtectedRoute — wraps routes that require a logged-in user.
 *
 * If the user is not logged in, redirect them to /login.
 * If we're still checking (loading), show nothing yet.
 */

import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()

  // Wait until we know if the user is logged in
  if (loading) return <div>Loading...</div>

  // Not logged in → send to login page
  if (!user) return <Navigate to="/login" replace />

  // Logged in → render the actual page
  return children
}

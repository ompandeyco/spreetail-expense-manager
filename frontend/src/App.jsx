/**
 * App.jsx — defines all client-side routes.
 *
 * React Router reads the URL and renders the matching page component.
 * Routes inside <ProtectedRoute> require the user to be logged in.
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'

import LoginPage      from './pages/LoginPage'
import DashboardPage  from './pages/DashboardPage'
import ExpensesPage   from './pages/ExpensesPage'
import GroupsPage     from './pages/GroupsPage'
import SettlementsPage from './pages/SettlementsPage'

export default function App() {
  return (
    // AuthProvider makes auth state available to every component below
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public routes — no login required */}
          <Route path="/login" element={<LoginPage />} />

          {/* Redirect root to dashboard */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          {/* Protected routes — redirect to /login if not authenticated */}
          <Route path="/dashboard"   element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/expenses"    element={<ProtectedRoute><ExpensesPage /></ProtectedRoute>} />
          <Route path="/groups"      element={<ProtectedRoute><GroupsPage /></ProtectedRoute>} />
          <Route path="/settlements" element={<ProtectedRoute><SettlementsPage /></ProtectedRoute>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

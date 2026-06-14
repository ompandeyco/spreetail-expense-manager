/**
 * DashboardPage — landing page after login.
 * Business logic (fetching totals, charts, etc.) will be added later.
 */

import { useAuth } from '../context/AuthContext'

export default function DashboardPage() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">Dashboard</h1>
          <button
            onClick={logout}
            className="bg-red-500 text-white px-4 py-2 rounded-lg text-sm hover:bg-red-600 transition"
          >
            Logout
          </button>
        </div>

        <p className="text-gray-600">Welcome back, <strong>{user?.username}</strong>!</p>

        {/* Placeholder cards — real data will come from API */}
        <div className="grid grid-cols-3 gap-6 mt-8">
          {['Total Expenses', 'Pending Settlements', 'Active Groups'].map((label) => (
            <div key={label} className="bg-white rounded-xl shadow p-6">
              <p className="text-sm text-gray-500">{label}</p>
              <p className="text-2xl font-bold text-gray-800 mt-2">—</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

/**
 * Auth service — wraps all auth-related API calls in one place.
 * Views import these functions instead of calling axios directly.
 */

import api from './api'

/**
 * Log in with username + password.
 * Django SimpleJWT returns { access, refresh } tokens.
 * We store them in localStorage so they persist across page reloads.
 */
export async function login(username, password) {
  const response = await api.post('/token/', { username, password })
  const { access, refresh } = response.data

  localStorage.setItem('access_token', access)
  localStorage.setItem('refresh_token', refresh)

  return response.data
}

/**
 * Remove tokens from localStorage.
 * The user is now "logged out" on the frontend side.
 */
export function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

/**
 * Register a new user account.
 */
export async function register(userData) {
  const response = await api.post('/users/register/', userData)
  return response.data
}

/**
 * Fetch the currently logged-in user's profile.
 */
export async function getMe() {
  const response = await api.get('/users/me/')
  return response.data
}

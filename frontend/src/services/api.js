/**
 * axios instance pre-configured for our Django API.
 *
 * Instead of writing `http://localhost:8000/api/...` everywhere,
 * we create one shared axios instance with the base URL set.
 * Every API call in the app imports this instead of plain axios.
 */

import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api', // Use VITE_API_URL if available, else fallback to Vite proxy
})

/**
 * Request interceptor — runs before every API call.
 * Reads the JWT access token from localStorage and attaches it
 * to the Authorization header automatically.
 */
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default api

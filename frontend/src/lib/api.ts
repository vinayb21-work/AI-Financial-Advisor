import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
})

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth-storage')
  if (token) {
    try {
      const parsed = JSON.parse(token)
      if (parsed.state?.token) {
        config.headers.Authorization = `Bearer ${parsed.state.token}`
      }
    } catch (e) {
      console.error('Error parsing token:', e)
    }
  }
  return config
})

// Auth APIs
export const authApi = {
  getGoogleLoginUrl: () => api.get('/auth/google/login'),
  getHubspotConnectUrl: () => api.get('/auth/hubspot/connect'),
  getCurrentUser: () => api.get('/auth/me'),
}

// Chat APIs
export const chatApi = {
  sendMessage: (data: { content: string; thread_id?: string; context?: string }) =>
    api.post('/chat/message', data),
  getThreads: () => api.get('/chat/threads'),
  getThread: (threadId: string) => api.get(`/chat/threads/${threadId}`),
  updateThread: (threadId: string, data: { title: string }) =>
    api.patch(`/chat/threads/${threadId}`, data),
  deleteThread: (threadId: string) => api.delete(`/chat/threads/${threadId}`),
}

// Integration APIs
export const integrationApi = {
  syncGmail: () => api.post('/integrations/sync/gmail'),
  syncCalendar: () => api.post('/integrations/sync/calendar'),
  syncHubspot: () => api.post('/integrations/sync/hubspot'),
  getSyncStatus: () => api.get('/integrations/sync/status'),
}


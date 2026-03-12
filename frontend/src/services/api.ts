import axios from 'axios'
import { ApiResponse, SystemStatus } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor para adicionar token JWT
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export async function sendMessage(query: string, conversationId?: string): Promise<ApiResponse> {
  try {
    const response = await api.post('/chat', { 
      query,
      conversation_id: conversationId 
    })
    return response.data
  } catch (error) {
    console.error('Error sending message:', error)
    throw error
  }
}

export async function uploadFile(file: File): Promise<{ success: boolean; message: string }> {
  try {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

    return response.data
  } catch (error) {
    console.error('Error uploading file:', error)
    throw error
  }
}

export async function getSystemStatus(): Promise<SystemStatus> {
  try {
    const response = await api.get('/health')
    return response.data
  } catch (error) {
    console.error('Error getting system status:', error)
    return {
      openrag: false,
      opensearch: false,
      langflow: false,
      overall: false,
    }
  }
}

export async function getAnalytics() {
  try {
    const response = await api.get('/analytics')
    return response.data
  } catch (error) {
    console.error('Error getting analytics:', error)
    throw error
  }
}

// ============================================
// AUTENTICAÇÃO
// ============================================

export interface LoginCredentials {
  username: string
  password: string
}

export interface RegisterData {
  username: string
  email: string
  password: string
  full_name?: string
}

export interface User {
  id: string
  username: string
  email: string
  full_name: string
  is_active: boolean
  is_admin: boolean
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export async function login(credentials: LoginCredentials): Promise<AuthResponse> {
  try {
    const formData = new URLSearchParams()
    formData.append('username', credentials.username)
    formData.append('password', credentials.password)
    
    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
    
    // Salvar token
    localStorage.setItem('access_token', response.data.access_token)
    localStorage.setItem('user', JSON.stringify(response.data.user))
    
    return response.data
  } catch (error) {
    console.error('Error logging in:', error)
    throw error
  }
}

export async function register(data: RegisterData): Promise<User> {
  try {
    const response = await api.post('/auth/register', data)
    return response.data
  } catch (error) {
    console.error('Error registering:', error)
    throw error
  }
}

export async function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user')
}

export async function getCurrentUser(): Promise<User> {
  try {
    const response = await api.get('/auth/me')
    return response.data
  } catch (error) {
    console.error('Error getting current user:', error)
    throw error
  }
}

export async function changePassword(oldPassword: string, newPassword: string) {
  try {
    const response = await api.post('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    })
    return response.data
  } catch (error) {
    console.error('Error changing password:', error)
    throw error
  }
}

// ============================================
// HISTÓRICO DE CONVERSAS
// ============================================

export interface Conversation {
  id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
}

export interface ConversationMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export async function getConversations(limit: number = 50): Promise<Conversation[]> {
  try {
    const response = await api.get(`/chat/conversations?limit=${limit}`)
    return response.data.conversations
  } catch (error) {
    console.error('Error getting conversations:', error)
    throw error
  }
}

export async function getConversationHistory(conversationId: string): Promise<ConversationMessage[]> {
  try {
    const response = await api.get(`/chat/history/${conversationId}`)
    return response.data
  } catch (error) {
    console.error('Error getting conversation history:', error)
    throw error
  }
}

export async function deleteConversation(conversationId: string) {
  try {
    const response = await api.delete(`/chat/history/${conversationId}`)
    return response.data
  } catch (error) {
    console.error('Error deleting conversation:', error)
    throw error
  }
}

export default api

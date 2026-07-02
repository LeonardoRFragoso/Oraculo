import axios from 'axios'
import { ApiResponse, SystemStatus } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

export const api = axios.create({
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

export async function sendMessage(query: string, conversationId?: string, sourceIds?: string[]): Promise<ApiResponse> {
  try {
    const response = await api.post('/chat', { 
      query,
      conversation_id: conversationId,
      source_ids: sourceIds,
    })
    return response.data
  } catch (error) {
    console.error('Error sending message:', error)
    throw error
  }
}

export interface ExportResponse {
  download_url: string
  filename: string
  format: string
}

export async function exportChat(query: string, conversationId?: string, sourceIds?: string[]): Promise<ExportResponse> {
  try {
    const response = await api.post('/chat/export', {
      query,
      conversation_id: conversationId,
      source_ids: sourceIds,
    })
    return response.data
  } catch (error) {
    console.error('Error exporting chat:', error)
    throw error
  }
}

export async function uploadFile(file: File): Promise<{ success: boolean; message: string; file_id: string; filename: string }> {
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
  plan?: string
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

// ============================================
// DATA SOURCES (Sprint 1-2)
// ============================================

export interface DataSource {
  id: string
  name: string
  connector_type: string
  status: string
  description?: string
  tags: string[]
  created_at: string
  updated_at: string
  datasets: any[]
  domain_summary: any
  schema_info: any
}

export async function listDataSources(): Promise<DataSource[]> {
  const response = await api.get('/datasources')
  return response.data.sources
}

export async function getDataSource(id: string): Promise<DataSource> {
  const response = await api.get(`/datasources/${id}`)
  return response.data
}

export async function registerDataSource(payload: {
  name: string
  connector_type: string
  config: Record<string, any>
  description?: string
}): Promise<DataSource> {
  const response = await api.post('/datasources', payload)
  return response.data
}

export async function connectDataSource(id: string): Promise<any> {
  const response = await api.post(`/datasources/${id}/connect`)
  return response.data
}

export async function deleteDataSource(id: string): Promise<void> {
  await api.delete(`/datasources/${id}`)
}

export async function uploadDataSource(
  file: File,
  name?: string
): Promise<DataSource> {
  const form = new FormData()
  form.append('file', file)
  if (name) form.append('name', name)
  const response = await api.post('/datasources/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

// ============================================
// AI ANALYST (Sprint 5)
// ============================================

export interface AnalysisReport {
  source_id: string
  source_name: string
  connector_type: string
  analyzed_at: string
  executive_summary: string
  total_kpis: number
  total_anomalies: number
  critical_count: number
  datasets: Array<{
    dataset_name: string
    domain: string
    row_count: number
    kpis: Array<{ name: string; value: any; unit: string; status: string; description: string }>
    anomalies: Array<{ type: string; severity: string; column: string; message: string; emoji: string }>
    summary: string
  }>
}

export async function analyzeDataSource(id: string): Promise<AnalysisReport> {
  const response = await api.post(`/datasources/${id}/analyze`)
  return response.data
}

// ============================================
// AGENT ACTIONS (Sprint 6)
// ============================================

export interface ActResult {
  source_id: string
  source_name: string
  instruction: string | null
  dry_run: boolean
  plan: Array<{ action: string; params: Record<string, any> }>
  actions_executed: number
  results: Array<{
    action: string
    status: string
    message: string
    artifact?: string
    details: any
  }>
  anomaly_count: number
  kpi_count: number
}

export async function actOnSource(
  id: string,
  instruction?: string,
  params?: Record<string, any>,
  dryRun = false
): Promise<ActResult> {
  const response = await api.post(`/datasources/${id}/act`, {
    instruction,
    params,
    dry_run: dryRun,
  })
  return response.data
}

export async function listAlerts(limit = 50): Promise<{ alerts: any[]; total: number }> {
  const response = await api.get(`/datasources/alerts?limit=${limit}`)
  return response.data
}

export async function listActionCatalog(): Promise<any[]> {
  const response = await api.get('/datasources/actions/catalog')
  return response.data.actions
}

// ============================================
// KNOWLEDGE GRAPH (Sprint 7)
// ============================================

export interface GraphData {
  nodes: Array<{ id: string; label: string; type: string; color: string; size: number; frequency: number; [k: string]: any }>
  edges: Array<{ from: string; to: string; type: string; weight: number; count: number }>
}

export interface GraphResponse {
  source_id: string
  source_name: string
  stats: {
    node_count: number
    edge_count: number
    entity_types: Record<string, number>
    relation_types: Record<string, number>
    density: number
    avg_degree: number
    top_entities: Array<{ id: string; label: string; type: string; degree: number }>
  }
  graph: GraphData
}

export async function buildGraph(id: string): Promise<GraphResponse> {
  const response = await api.post(`/datasources/${id}/graph`)
  return response.data
}

export async function getGraph(id: string): Promise<GraphResponse> {
  const response = await api.get(`/datasources/${id}/graph`)
  return response.data
}

export async function searchGraph(id: string, q: string): Promise<any[]> {
  const response = await api.get(`/datasources/${id}/graph/search?q=${encodeURIComponent(q)}`)
  return response.data.results
}

export async function getGraphEntity(id: string, entityId: string, depth = 1): Promise<any> {
  const response = await api.get(
    `/datasources/${id}/graph/entity/${encodeURIComponent(entityId)}?depth=${depth}`
  )
  return response.data
}

// ============================================
// NL2SQL / HYBRID QUERY (Sprint 3-4)
// ============================================

export interface QueryResponse {
  question: string
  query_type: string
  answer: string
  sql?: string
  sql_explanation?: string
  sql_confidence?: number
  columns?: string[]
  rows?: any[]
  row_count?: number
  execution_time_ms?: number
  sources_used?: string[]
  error?: string
}

export async function queryAllSources(question: string): Promise<QueryResponse> {
  const response = await api.post('/query', { question })
  return response.data
}

export async function queryDataSource(
  id: string,
  question: string,
  explain = true
): Promise<QueryResponse> {
  const response = await api.post(`/datasources/${id}/query`, { question, explain })
  return response.data
}

export default api

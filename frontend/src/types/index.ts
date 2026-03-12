export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  isInsight?: boolean
}

export interface ChatContextType {
  messages: Message[]
  isLoading: boolean
  conversationId: string
  addMessage: (message: Message) => void
  clearMessages: () => void
  updateLastMessage: (content: string) => void
  setIsLoading: (loading: boolean) => void
}

export interface ApiResponse {
  response: string
  insights?: Insight[]
  suggestions?: string[]
}

export interface Insight {
  id: string
  type: 'trend' | 'anomaly' | 'opportunity' | 'risk'
  title: string
  description: string
  confidence: number
  data?: any
}

export interface UploadedFile {
  id: string
  name: string
  size: number
  type: string
  uploadedAt: Date
  status: 'uploading' | 'processing' | 'completed' | 'error'
}

export interface SystemStatus {
  openrag: boolean
  opensearch: boolean
  langflow: boolean
  overall: boolean
}

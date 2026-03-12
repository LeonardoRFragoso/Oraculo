import { useEffect, useState } from 'react'
import { MessageSquare, Trash2, Clock } from 'lucide-react'
import { getConversations, deleteConversation, Conversation } from '../services/api'
import { toast } from 'react-hot-toast'

interface ConversationListProps {
  onSelectConversation: (conversationId: string) => void
  currentConversationId?: string
}

export default function ConversationList({ onSelectConversation, currentConversationId }: ConversationListProps) {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadConversations()
  }, [])

  const loadConversations = async () => {
    try {
      const data = await getConversations(50)
      setConversations(data)
    } catch (error) {
      console.error('Error loading conversations:', error)
      toast.error('Erro ao carregar conversas')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async (conversationId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    
    if (!confirm('Deseja realmente deletar esta conversa?')) {
      return
    }

    try {
      await deleteConversation(conversationId)
      setConversations(conversations.filter(c => c.id !== conversationId))
      toast.success('Conversa deletada')
    } catch (error) {
      console.error('Error deleting conversation:', error)
      toast.error('Erro ao deletar conversa')
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Agora'
    if (diffMins < 60) return `${diffMins}m atrás`
    if (diffHours < 24) return `${diffHours}h atrás`
    if (diffDays < 7) return `${diffDays}d atrás`
    
    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })
  }

  if (isLoading) {
    return (
      <div className="p-4 text-center text-gray-500 dark:text-gray-400">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary mx-auto"></div>
      </div>
    )
  }

  if (conversations.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500 dark:text-gray-400">
        <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p className="text-sm">Nenhuma conversa ainda</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="px-4 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
        Conversas Recentes
      </div>
      
      {conversations.map((conversation) => (
        <button
          key={conversation.id}
          onClick={() => onSelectConversation(conversation.id)}
          className={`w-full px-4 py-3 text-left rounded-lg transition-all group hover:bg-gray-100 dark:hover:bg-gray-800 ${
            currentConversationId === conversation.id
              ? 'bg-primary/10 border-l-4 border-primary'
              : ''
          }`}
        >
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                {conversation.title}
              </p>
              <div className="flex items-center gap-2 mt-1 text-xs text-gray-500 dark:text-gray-400">
                <Clock className="w-3 h-3" />
                <span>{formatDate(conversation.updated_at)}</span>
                <span>•</span>
                <span>{conversation.message_count} msgs</span>
              </div>
            </div>
            
            <button
              onClick={(e) => handleDelete(conversation.id, e)}
              className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/20 transition-opacity"
              title="Deletar conversa"
            >
              <Trash2 className="w-4 h-4 text-red-600 dark:text-red-400" />
            </button>
          </div>
        </button>
      ))}
    </div>
  )
}

import { MessageSquare, BarChart3, Upload, Trash2, Plus, History } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import { useChat } from '../contexts/ChatContext'
import { useState } from 'react'
import { uploadFile } from '../services/api'
import toast from 'react-hot-toast'
import ConversationList from './ConversationList'

export default function Sidebar() {
  const location = useLocation()
  const { clearMessages, messages, conversationId, setConversationId } = useChat()
  const [showUpload, setShowUpload] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const [isUploading, setIsUploading] = useState(false)

  const isActive = (path: string) => location.pathname === path

  const navItems = [
    { path: '/', icon: MessageSquare, label: 'Chat' },
    { path: '/analytics', icon: BarChart3, label: 'Analytics' },
  ]

  const handleNewChat = () => {
    if (messages.length > 0) {
      if (confirm('Iniciar nova conversa? A conversa atual será perdida.')) {
        clearMessages()
      }
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    try {
      const response = await uploadFile(file)
      
      // Salvar arquivo na lista de anexados
      const attachedFiles = JSON.parse(localStorage.getItem('attached_files') || '[]')
      attachedFiles.push({
        filename: file.name,
        file_id: response.file_id,
        uploaded_at: new Date().toISOString(),
        size: file.size
      })
      localStorage.setItem('attached_files', JSON.stringify(attachedFiles))
      
      // Disparar evento para atualizar componente
      window.dispatchEvent(new Event('files-updated'))
      
      toast.success(`Arquivo "${file.name}" processado e indexado com sucesso! Agora você pode fazer perguntas sobre ele.`)
      setShowUpload(false)
    } catch (error) {
      console.error('Error uploading file:', error)
      toast.error('Erro ao processar arquivo. Tente novamente.')
    } finally {
      setIsUploading(false)
      e.target.value = ''
    }
  }

  return (
    <aside className="w-64 border-r border-light-border dark:border-dark-border bg-white dark:bg-dark-surface flex flex-col">
      {/* New Chat Button */}
      <div className="p-4">
        <button
          onClick={handleNewChat}
          className="w-full btn-primary flex items-center justify-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Nova Conversa
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 space-y-2">
        {navItems.map(({ path, icon: Icon, label }) => (
          <Link
            key={path}
            to={path}
            className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
              isActive(path)
                ? 'bg-primary text-white shadow-lg'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-bg'
            }`}
          >
            <Icon className="w-5 h-5" />
            <span className="font-medium">{label}</span>
          </Link>
        ))}
      </nav>

      {/* Upload Section */}
      <div className="p-4 border-t border-light-border dark:border-dark-border">
        <button
          onClick={() => setShowUpload(!showUpload)}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-bg transition-all"
        >
          <Upload className="w-5 h-5" />
          <span className="font-medium">Upload Dados</span>
        </button>

        {showUpload && (
          <div className="mt-2 p-3 bg-gray-50 dark:bg-dark-bg rounded-lg">
            <input
              type="file"
              accept=".xlsx,.xls,.csv,.pdf,.docx,.txt,.json"
              className="w-full text-sm"
              onChange={handleFileUpload}
              disabled={isUploading}
            />
            {isUploading && (
              <p className="text-xs text-primary mt-2">Processando arquivo...</p>
            )}
          </div>
        )}
      </div>

      {/* Conversation History */}
      {showHistory && (
        <div className="flex-1 overflow-y-auto">
          <ConversationList
            onSelectConversation={(id) => {
              setConversationId(id)
              setShowHistory(false)
            }}
            currentConversationId={conversationId || undefined}
          />
        </div>
      )}

      {/* Stats */}
      {!showHistory && (
        <div className="mt-auto pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="px-4 py-3 bg-gray-50 dark:bg-gray-800 rounded-xl">
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Mensagens</div>
            <div className="text-2xl font-bold gradient-text">{messages.length}</div>
          </div>
        </div>
      )}

      {/* Clear Chat */}
      {messages.length > 0 && (
        <div className="p-4 border-t border-light-border dark:border-dark-border">
          <button
            onClick={() => {
              if (confirm('Limpar histórico de chat?')) {
                clearMessages()
              }
            }}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-all"
          >
            <Trash2 className="w-4 h-4" />
            <span className="text-sm font-medium">Limpar Chat</span>
          </button>
        </div>
      )}
    </aside>
  )
}

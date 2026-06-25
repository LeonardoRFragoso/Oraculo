import { useState, useRef, useEffect } from 'react'
import { Send, Sparkles, Database, Download } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import { useChat } from '../contexts/ChatContext'
import ChatMessage from '../components/ChatMessage'
import TypingIndicator from '../components/TypingIndicator'
import WelcomeMessage from '../components/WelcomeMessage'
import QuickActions from '../components/QuickActions'
import AttachedFiles from '../components/AttachedFiles'
import { sendMessage, listDataSources, getConversationHistory, exportChat, DataSource } from '../services/api'
import { api } from '../services/api'
import toast from 'react-hot-toast'

export default function ChatPage() {
  const { messages, isLoading, conversationId, addMessage, setIsLoading, setConversationId, setMessages } = useChat()
  const [input, setInput] = useState('')
  const [sources, setSources] = useState<DataSource[]>([])
  const [selectedSourceId, setSelectedSourceId] = useState<string>('')
  const [showExport, setShowExport] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [searchParams, setSearchParams] = useSearchParams()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    listDataSources().then(data => {
      const connected = data.filter(s => s.status === 'connected')
      setSources(connected)
      const paramId = searchParams.get('source')
      if (paramId && connected.some(s => s.id === paramId)) {
        setSelectedSourceId(paramId)
      } else {
        setSelectedSourceId('')
      }
    })
  }, [searchParams])

  useEffect(() => {
    if (!conversationId) {
      setMessages([])
      return
    }
    getConversationHistory(conversationId)
      .then(history => {
        setMessages(history.map((m, index) => ({
          id: `${conversationId}-${index}`,
          role: m.role,
          content: m.content,
          timestamp: new Date(m.timestamp),
        })))
      })
      .catch(() => toast.error('Erro ao carregar histórico'))
  }, [conversationId])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: input.trim(),
      timestamp: new Date(),
    }

    addMessage(userMessage)
    setInput('')
    setIsLoading(true)

    try {
      const response = await sendMessage(
        input.trim(),
        conversationId || undefined,
        selectedSourceId ? [selectedSourceId] : undefined
      )

      if (response.conversation_id) {
        setConversationId(response.conversation_id)
      }

      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content: response.response,
        timestamp: new Date(),
      }

      addMessage(assistantMessage)

      // Adicionar insights se houver
      if (response.insights && response.insights.length > 0) {
        response.insights.forEach((insight, index) => {
          const insightMessage = {
            id: (Date.now() + 2 + index).toString(),
            role: 'assistant' as const,
            content: `💡 **${insight.title}**\n\n${insight.description}`,
            timestamp: new Date(),
            isInsight: true,
          }
          addMessage(insightMessage)
        })
      }
    } catch (error) {
      console.error('Error sending message:', error)
      toast.error('Erro ao enviar mensagem. Tente novamente.')
      
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content: 'Desculpe, encontrei uma dificuldade ao processar sua mensagem. Por favor, tente novamente.',
        timestamp: new Date(),
      }
      addMessage(errorMessage)
    } finally {
      setIsLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const handleQuickAction = (question: string) => {
    setInput(question)
    inputRef.current?.focus()
  }

  const handleExport = async (format: string) => {
    if (!selectedSourceId) {
      toast.error('Selecione uma fonte de dados para exportar')
      return
    }
    setExporting(true)
    setShowExport(false)
    try {
      const query = `Gere um arquivo ${format.toUpperCase()} completo e atualizado com base na fonte de dados selecionada`
      const result = await exportChat(query, conversationId || undefined, [selectedSourceId])
      const fileResponse = await api.get(result.download_url, { responseType: 'blob' })
      const blob = new Blob([fileResponse.data])
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', result.filename)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      toast.success(`Arquivo ${result.format.toUpperCase()} gerado`)
    } catch {
      toast.error('Erro ao gerar arquivo')
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="h-full flex flex-col bg-light-bg dark:bg-dark-bg">
      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.length === 0 ? (
            <>
              <WelcomeMessage />
              <QuickActions onSelect={handleQuickAction} />
            </>
          ) : (
            messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))
          )}

          {isLoading && <TypingIndicator />}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t border-light-border dark:border-dark-border bg-white dark:bg-dark-surface">
        <div className="max-w-4xl mx-auto p-4">
          {sources.length > 0 && (
            <div className="mb-3 flex items-center gap-2">
              <Database className="w-4 h-4 text-primary" />
              <select
                className="input text-sm flex-1"
                value={selectedSourceId}
                onChange={e => {
                  const id = e.target.value
                  setSelectedSourceId(id)
                  if (id) {
                    setSearchParams({ source: id })
                  } else {
                    setSearchParams({})
                  }
                }}
              >
                <option value="">Todas as fontes conectadas</option>
                {sources.map(s => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>
          )}
          <AttachedFiles />

          <div className="flex items-center gap-2 mb-3">
            <button
              type="button"
              onClick={() => setShowExport(!showExport)}
              disabled={exporting || !selectedSourceId}
              className="btn-secondary flex items-center gap-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {exporting ? <Sparkles className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
              {exporting ? 'Gerando...' : 'Exportar'}
            </button>
            {showExport && (
              <div className="flex items-center gap-2">
                {['html', 'pdf', 'md', 'txt'].map(fmt => (
                  <button
                    key={fmt}
                    type="button"
                    onClick={() => handleExport(fmt)}
                    className="px-3 py-1.5 text-xs rounded-lg bg-primary/10 text-primary hover:bg-primary/20 font-medium uppercase"
                  >
                    {fmt}
                  </button>
                ))}
              </div>
            )}
          </div>

          <form onSubmit={handleSubmit} className="relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Digite sua pergunta..."
              className="w-full px-6 py-4 pr-14 rounded-2xl bg-light-surface dark:bg-dark-bg 
                       border-2 border-light-border dark:border-dark-border
                       focus:border-primary focus:ring-4 focus:ring-primary/10
                       resize-none transition-all duration-200
                       text-gray-900 dark:text-gray-100
                       placeholder:text-gray-400 dark:placeholder:text-gray-500"
              rows={1}
              style={{
                minHeight: '56px',
                maxHeight: '200px',
              }}
            />
            
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="absolute right-3 bottom-3 p-3 rounded-xl
                       gradient-primary text-white
                       disabled:opacity-50 disabled:cursor-not-allowed
                       hover:shadow-glow transition-all duration-200
                       hover:-translate-y-0.5"
            >
              {isLoading ? (
                <Sparkles className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </form>

          <p className="text-xs text-gray-400 dark:text-gray-500 text-center mt-2">
            Pressione Enter para enviar, Shift+Enter para nova linha
          </p>
        </div>
      </div>
    </div>
  )
}

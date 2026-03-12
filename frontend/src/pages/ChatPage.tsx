import { useState, useRef, useEffect } from 'react'
import { Send, Sparkles } from 'lucide-react'
import { useChat } from '../contexts/ChatContext'
import ChatMessage from '../components/ChatMessage'
import TypingIndicator from '../components/TypingIndicator'
import WelcomeMessage from '../components/WelcomeMessage'
import QuickActions from '../components/QuickActions'
import { sendMessage } from '../services/api'
import toast from 'react-hot-toast'

export default function ChatPage() {
  const { messages, isLoading, conversationId, addMessage, setIsLoading, setConversationId } = useChat()
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

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
      const response = await sendMessage(input.trim())
      
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

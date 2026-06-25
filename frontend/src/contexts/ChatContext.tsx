import { createContext, useContext, useState, ReactNode } from 'react'
import { Message, ChatContextType } from '../types'

const ChatContext = createContext<ChatContextType | undefined>(undefined)

export function ChatProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)

  const addMessage = (message: Message) => {
    setMessages(prev => [...prev, message])
  }

  const setMessagesList = (messages: Message[]) => {
    setMessages(messages)
  }

  const clearMessages = () => {
    setMessages([])
    setConversationId(null)
  }

  const updateLastMessage = (content: string) => {
    setMessages(prev => {
      const newMessages = [...prev]
      if (newMessages.length > 0) {
        newMessages[newMessages.length - 1].content = content
      }
      return newMessages
    })
  }

  return (
    <ChatContext.Provider
      value={{
        messages,
        isLoading,
        conversationId,
        addMessage,
        setMessages: setMessagesList,
        clearMessages,
        updateLastMessage,
        setIsLoading,
        setConversationId,
      }}
    >
      {children}
    </ChatContext.Provider>
  )
}

export function useChat() {
  const context = useContext(ChatContext)
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider')
  }
  return context
}

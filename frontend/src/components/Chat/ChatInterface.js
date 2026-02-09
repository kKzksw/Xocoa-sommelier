import { useState, useRef, useEffect } from 'react'
import ChatMessage from './ChatMessage'
import FixedChatInput from './FixedChatInput'
import ChocolateRecommendations from '../Recommendations/ChocolateRecommendations'

export default function ChatInterface() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'assistant',
      content: "Welcome to XOCOA. I am your personal Chocolate Sommelier.\n\nI can help you discover artisanal chocolates based on your taste, whether you prefer dark, milk, fruity, or nutty notes.\n\nTell me what you are looking for today.",
      timestamp: new Date()
    }
  ])
  
  const [recommendations, setRecommendations] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [userPreferences, setUserPreferences] = useState({})
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async (content) => {
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: content,
          preferences: userPreferences,
          conversationHistory: messages.map(msg => ({
            type: msg.type,
            content: msg.content
          })),
          last_ranked_products: recommendations
        })
      })

      const result = await response.json()

      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: result.message,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])

      if (result.preferences) {
        setUserPreferences(prev => ({ ...prev, ...result.preferences }))
      }

      setRecommendations(result.recommendations || [])

    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: "I apologize, but I'm having trouble connecting to the cellar right now. Please try again.",
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="chat-wrapper">
      <div className="chat-container chat-messages-container" style={{
        background: 'var(--color-bg-main)',
        border: 'none',
        padding: 'var(--space-md)',
        paddingBottom: '180px',
        minHeight: '100vh'
      }}>
        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            message={message}
            isLoading={isLoading && message === messages[messages.length - 1]}
          />
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-charcoal rounded-2xl px-4 py-3 max-w-xs">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-accent-gold rounded-full animate-pulse"></div>
                <div className="w-2 h-2 bg-accent-gold rounded-full animate-pulse delay-75"></div>
                <div className="w-2 h-2 bg-accent-gold rounded-full animate-pulse delay-150"></div>
              </div>
            </div>
          </div>
        )}

        {recommendations.length > 0 && (
          <div className="border-t border-warm-gray p-6 mt-4">
            <ChocolateRecommendations recommendations={recommendations} />
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <FixedChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
    </div>
  )
}
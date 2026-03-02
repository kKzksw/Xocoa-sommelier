import { useState, useRef, useEffect } from 'react'
import ChatMessage from './ChatMessage'
import FixedChatInput from './FixedChatInput'
import ChocolateRecommendations from '../Recommendations/ChocolateRecommendations'

export default function ChatInterface() {
  const SEGMENT_OPTIONS = [
    { key: 'A', label: 'Taste & flavor experience' },
    { key: 'B', label: 'Health & ethical sourcing' },
    { key: 'C', label: 'Good value & familiar brands' }
  ]

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
  const [conversationState, setConversationState] = useState({})
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

    const nextMessages = [...messages, userMessage]
    setMessages(nextMessages)
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
          conversationHistory: nextMessages.map(msg => ({
            type: msg.type,
            content: msg.content
          })),
          last_ranked_products: recommendations,
          state: conversationState
        })
      })

      const result = await response.json()
      const fallbackFollowups = Array.isArray(result.followup_questions) && result.followup_questions.length > 0
        ? result.followup_questions.map((q, idx) => `${idx + 1}. ${q}`).join('\n')
        : ''
      const assistantContent = result.message || fallbackFollowups || "I couldn't process that. Please try again."

      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: assistantContent,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
      setConversationState(prev => result.conversation_state || prev)

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

  const handleSegmentSelection = async (segmentKey) => {
    if (isLoading) return
    await handleSendMessage(segmentKey)
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

        {!conversationState.segment && (
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '0.5rem',
            margin: '0 2rem 1rem'
          }}>
            {SEGMENT_OPTIONS.map((option) => (
              <button
                key={option.key}
                type="button"
                disabled={isLoading}
                onClick={() => handleSegmentSelection(option.key)}
                style={{
                  border: '1px solid var(--color-primary)',
                  background: '#fff',
                  color: 'var(--color-primary)',
                  borderRadius: '999px',
                  padding: '0.5rem 0.9rem',
                  fontFamily: 'var(--font-body)',
                  fontSize: 'var(--text-sm)',
                  cursor: isLoading ? 'not-allowed' : 'pointer',
                  opacity: isLoading ? 0.65 : 1
                }}
              >
                {option.key}) {option.label}
              </button>
            ))}
          </div>
        )}

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

        <div ref={messagesEndRef} />

        {recommendations.length > 0 && (
          <div className="border-t border-warm-gray p-6 mt-4">
            <ChocolateRecommendations recommendations={recommendations} />
          </div>
        )}
      </div>

      <FixedChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
    </div>
  )
}

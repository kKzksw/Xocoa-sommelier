import { useState, useRef, useEffect } from 'react'

export default function FixedChatInput({ onSendMessage, disabled }) {
  const [message, setMessage] = useState('')
  const [isMobile, setIsMobile] = useState(false)
  const textareaRef = useRef(null)

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth <= 768)
    }

    // Set initial value
    handleResize()

    // Add event listener
    window.addEventListener('resize', handleResize)

    // Cleanup
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (message.trim() && !disabled) {
      onSendMessage(message.trim())
      setMessage('')
    }
  }

  const handleKeyDown = (e) => {
    // Send with Enter (Standard)
    // Shift + Enter allows for line breaks
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="chat-input-container" style={{
      position: 'fixed',
      bottom: '0',
      left: '0',
      right: '0',
      background: 'var(--color-bg-main)',
      borderTop: '2px solid var(--color-primary)',
      padding: '1rem 1.5rem 1.5rem',
      zIndex: '100'
    }}>
      <div className="chat-input-wrapper" style={{
        maxWidth: '1200px',
        margin: '0 auto',
        position: 'relative'
      }}>
        <form onSubmit={handleSubmit}>
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe your chocolate preferences... (Press Enter to send)"
            className="chat-textarea"
            disabled={disabled}
            rows={4}
            style={{
              width: '100%',
              minHeight: isMobile ? '80px' : '100px',
              maxHeight: isMobile ? '80px' : '100px',
              height: isMobile ? '80px' : '100px',
              resize: 'none',
              background: 'var(--color-bg-card)',
              border: '2px solid var(--color-primary)',
              borderRadius: '12px',
              padding: isMobile ? '0.75rem 2.5rem 0.75rem 0.75rem' : '1rem 3rem 1rem 1rem',
              color: 'var(--color-text-primary)',
              fontFamily: 'var(--font-body)',
              fontSize: 'var(--text-sm)',
              fontWeight: '400',
              lineHeight: '1.6',
              transition: 'all 0.3s ease',
              overflowY: 'auto',
              outline: 'none'
            }}
            onFocus={(e) => {
              e.target.style.borderColor = 'var(--color-primary-dark)'
              e.target.style.boxShadow = '0 0 0 3px rgba(45, 139, 127, 0.1)'
            }}
            onBlur={(e) => {
              e.target.style.borderColor = 'var(--color-primary)'
              e.target.style.boxShadow = 'none'
            }}
          />

          <button
            type="submit"
            disabled={disabled || !message.trim()}
            className="send-button"
            style={{
              position: 'absolute',
              right: isMobile ? '0.5rem' : '1rem',
              bottom: isMobile ? '0.5rem' : '1rem',
              background: 'var(--color-btn-primary-bg)',
              border: 'none',
              borderRadius: '20px',
              padding: isMobile ? '0.5rem 1rem' : '0.75rem 1.5rem',
              color: 'var(--color-btn-primary-text)',
              fontWeight: '600',
              cursor: disabled ? 'not-allowed' : 'pointer',
              transition: 'all 0.3s ease',
              opacity: disabled ? '0.5' : '1',
              fontFamily: 'var(--font-body)',
              fontSize: 'var(--text-sm)'
            }}
            onMouseEnter={(e) => {
              if (!disabled && message.trim()) {
                e.target.style.background = '#2A2A2A'
                e.target.style.transform = 'translateY(-2px)'
              }
            }}
            onMouseLeave={(e) => {
              e.target.style.background = 'var(--color-btn-primary-bg)'
              e.target.style.transform = 'translateY(0)'
            }}
          >
            {disabled ? 'Sending...' : 'Send'}
          </button>
        </form>
      </div>
    </div>
  )
}
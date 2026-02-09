import { formatDistanceToNow } from 'date-fns'
import { fr } from 'date-fns/locale'

export default function ChatMessage({ message }) {
  const isUser = message.type === 'user'

  return (
    <div className={`message-wrapper ${isUser ? 'user' : 'sommelier'}`} style={{
      display: 'flex',
      alignItems: 'flex-start',
      marginBottom: '1rem',
      flexDirection: isUser ? 'row-reverse' : 'row'
    }}>
      {/* Message Bubble */}
      <div className={`message-bubble ${isUser ? 'message-user' : 'message-sommelier'}`} style={{
        position: 'relative',
        padding: '1rem 1.25rem',
        maxWidth: '80%',
        borderRadius: '12px',
        ...(isUser ? {
          background: 'var(--color-user-bg)',
          color: 'var(--color-text-light)',
          marginLeft: 'auto',
          marginRight: '2rem'
        } : {
          background: 'var(--color-sommelier-bg)',
          border: '2px solid var(--color-sommelier-border)',
          color: 'var(--color-text-primary)',
          marginLeft: '2rem',
          boxShadow: '0 2px 8px rgba(45, 139, 127, 0.1)'
        })
      }}>
        <p style={{
          fontFamily: 'var(--font-body)',
          fontSize: 'var(--text-sm)',
          fontWeight: '400',
          lineHeight: '1.6',
          margin: '0',
          whiteSpace: 'pre-wrap',
          color: isUser ? 'var(--color-text-light)' : 'var(--color-text-primary)'
        }}>
          {message.content}
        </p>
      </div>
    </div>
  )
}
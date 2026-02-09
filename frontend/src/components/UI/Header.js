import Link from 'next/link'
import { useRouter } from 'next/router'

export default function Header() {
  const router = useRouter();
  
  const navLinkStyle = (path) => ({
    textDecoration: 'none',
    color: router.pathname === path ? 'var(--color-primary)' : 'var(--color-text-primary)',
    fontFamily: 'var(--font-body)',
    fontWeight: '600',
    fontSize: '1.1rem',
    transition: 'all 0.3s ease',
    borderBottom: router.pathname === path ? '2px solid var(--color-primary)' : '2px solid transparent',
    paddingBottom: '4px'
  });

  return (
    <header style={{
      backgroundColor: 'var(--color-bg-main)',
      padding: '0',
      position: 'relative',
      borderBottom: '1px solid rgba(0,0,0,0.05)'
    }}>
      <nav style={{
        position: 'absolute',
        top: '30px',
        right: '60px',
        display: 'flex',
        gap: '30px',
        alignItems: 'center',
        zIndex: 10
      }}>
        <Link href="/" style={navLinkStyle('/')}>
          Home
        </Link>
        <Link href="/about" style={navLinkStyle('/about')}>
          About Us
        </Link>
        <a 
          href="mailto:hello@xocoa.co" 
          className="btn-secondary"
          style={{
            textDecoration: 'none',
            padding: '0.6rem 1.5rem',
            fontSize: '0.95rem',
            display: 'inline-block'
          }}
        >
          Contact Us
        </a>
      </nav>
      
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        width: '100%',
        padding: '20px 0'
      }}>
        <Link href="/">
          <img
            src="/LOGO_SOMMELIER_FOND_BLANC_COULEURS.png"
            alt="Le Sommelier du Chocolat"
            style={{
              height: '180px', // Slightly smaller for better balance
              width: 'auto',
              display: 'block',
              margin: '0',
              cursor: 'pointer',
              transition: 'transform 0.3s ease'
            }}
            onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.02)'}
            onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}
          />
        </Link>
      </div>
    </header>
  )
}

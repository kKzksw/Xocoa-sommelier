import Header from '../components/UI/Header'
import SEOHead from '../components/SEO/SEOHead'

export default function About() {
  return (
    <>
      <SEOHead title="About Us - XOCOA" />
      <div className="min-h-screen" style={{ background: '#EBEAE4' }}>
        <Header />
        <main className="w-full px-8 py-12">
          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-3xl shadow-sm overflow-hidden" style={{
              border: '1px solid rgba(45, 139, 127, 0.1)',
              boxShadow: '0 10px 30px rgba(0,0,0,0.05)'
            }}>
              {/* Hero Section */}
              <div style={{
                background: 'var(--color-primary)',
                padding: '5rem 2rem',
                textAlign: 'center',
                color: 'white'
              }}>
                <h1 style={{ 
                  fontFamily: 'var(--font-body)', 
                  fontSize: '3.5rem',
                  fontWeight: '700',
                  marginBottom: '1rem'
                }}>
                  Netflix of Premium Chocolate
                </h1>
                <p style={{
                  fontSize: '1.4rem',
                  opacity: '0.9',
                  maxWidth: '700px',
                  margin: '0 auto',
                  fontWeight: '300',
                  lineHeight: '1.4'
                }}>
                  XOCOA is building an AI-powered recommendation platform for premium artisanal chocolate, connecting 500+ African artisan chocolatiers to global markets.
                </p>
              </div>

              {/* Text Content */}
              <div style={{ padding: '4rem' }}>
                <div style={{
                  fontFamily: 'var(--font-body)',
                  color: 'var(--color-text-primary)',
                  fontSize: '1.15rem',
                  lineHeight: '1.8'
                }}>
                  
                  {/* Market & Strategy Section */}
                  <div style={{ marginBottom: '4rem' }}>
                    <h2 style={{ color: 'var(--color-primary)', fontSize: '2rem', marginBottom: '1.5rem', fontWeight: '700' }}>
                      Why Now?
                    </h2>
                    <p style={{ marginBottom: '1.5rem' }}>
                      Cacao prices have recently doubled to <strong>€12,000/tonne</strong>. As a result, industrial producers are cutting corners, while the artisanal premium chocolate segment is exploding (<strong>+7-12% CAGR</strong>). 
                    </p>
                    <p style={{ marginBottom: '1.5rem' }}>
                      Currently, <strong>zero competitors</strong> possess AI-powered recommendations tailored specifically for this high-growth segment. XOCOA fills this vacuum, providing the first intelligent discovery layer for the "New Cocoa Era."
                    </p>
                    <p style={{ 
                      padding: '1.5rem', 
                      background: 'rgba(45, 139, 127, 0.05)', 
                      borderRadius: '1rem',
                      borderLeft: '4px solid var(--color-primary)',
                      fontStyle: 'italic'
                    }}>
                      We are at the seed stage, currently engaging with investors to create our first leverage and scale the platform. Our AI engine is live at <strong>xocoa-sommelier.com</strong>.
                    </p>
                  </div>

                  {/* Founders Section */}
                  <div style={{ marginBottom: '4rem' }}>
                    <h2 style={{ color: 'var(--color-primary)', fontSize: '2rem', marginBottom: '2rem', fontWeight: '700' }}>
                      Experienced Founders
                    </h2>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                      <div style={{ background: 'var(--color-bg-main)', padding: '2rem', borderRadius: '1.5rem' }}>
                        <h3 style={{ color: 'var(--color-secondary)', fontSize: '1.4rem', marginBottom: '0.5rem' }}>Ary</h3>
                        <p style={{ fontSize: '0.9rem', color: 'var(--color-primary)', fontWeight: '700', marginBottom: '1rem', textTransform: 'uppercase' }}>CEO</p>
                        <p style={{ fontSize: '1rem', lineHeight: '1.5' }}>
                          10+ years in B2B luxury (hotels, Michelin restaurants) with a formidable commercial network and market expertise.
                        </p>
                      </div>
                      <div style={{ background: 'var(--color-bg-main)', padding: '2rem', borderRadius: '1.5rem' }}>
                        <h3 style={{ color: 'var(--color-secondary)', fontSize: '1.4rem', marginBottom: '0.5rem' }}>Julien</h3>
                        <p style={{ fontSize: '0.9rem', color: 'var(--color-primary)', fontWeight: '700', marginBottom: '1rem', textTransform: 'uppercase' }}>CTO / COO</p>
                        <p style={{ fontSize: '1rem', lineHeight: '1.5' }}>
                          Former operations director in Côte d'Ivoire cocoa trading with 4 years dedicated to AI engine R&D.
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Developers Section */}
                  <div>
                    <h2 style={{ color: 'var(--color-primary)', fontSize: '2rem', marginBottom: '2rem', fontWeight: '700' }}>
                      Development Team
                    </h2>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                      <div style={{ border: '1px solid #eee', padding: '1.5rem', borderRadius: '1rem' }}>
                        <h3 style={{ fontSize: '1.2rem', marginBottom: '0.25rem' }}>Hrishikesh Alikatte</h3>
                        <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginBottom: '0.75rem' }}>Data Scientist / AI Engineer</p>
                        <p style={{ fontSize: '0.95rem', color: '#666' }}>BSc Data Science at Emlyon Business School</p>
                      </div>
                      <div style={{ border: '1px solid #eee', padding: '1.5rem', borderRadius: '1rem' }}>
                        <h3 style={{ fontSize: '1.2rem', marginBottom: '0.25rem' }}>Cheng Leyan</h3>
                        <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginBottom: '0.75rem' }}>Data Scientist / AI Engineer</p>
                        <p style={{ fontSize: '0.95rem', color: '#666' }}>BSc Data Science at Emlyon Business School</p>
                      </div>
                    </div>
                  </div>

                  <div style={{ 
                    marginTop: '5rem', 
                    textAlign: 'center',
                    padding: '3rem',
                    background: 'var(--color-secondary)',
                    borderRadius: '2rem',
                    color: 'white'
                  }}>
                    <p style={{ 
                      fontSize: '1.2rem',
                      fontWeight: '300',
                      marginBottom: '2rem'
                    }}>
                      Interested in joining our journey at the seed stage?
                    </p>
                    <a href="mailto:hello@xocoa.co" className="btn-secondary" style={{ 
                      textDecoration: 'none',
                      background: 'white',
                      color: 'var(--color-secondary)',
                      padding: '1rem 2.5rem'
                    }}>
                      Contact the Founders
                    </a>
                  </div>
                </div>
              </div>
            </div>
            
            <footer style={{
              marginTop: '3rem',
              textAlign: 'center',
              color: 'var(--color-text-secondary)',
              fontSize: '0.9rem',
              paddingBottom: '3rem'
            }}>
              &copy; {new Date().getFullYear()} XOCOA. All rights reserved.
            </footer>
          </div>
        </main>
      </div>
    </>
  )
}

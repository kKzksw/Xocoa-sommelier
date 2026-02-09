import ChatInterface from '../components/Chat/ChatInterface'
import Header from '../components/UI/Header'
import SEOHead from '../components/SEO/SEOHead'

export default function Home() {
  return (
    <>
      <SEOHead />

      <div className="min-h-screen" style={{ background: '#EBEAE4' }}>
        <Header />
        <main className="w-full px-16 py-8">
          <div className="max-w-7xl mx-auto">

            <ChatInterface />
          </div>
        </main>
      </div>
    </>
  )
}
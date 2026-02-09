import PremiumChocolateCard from './PremiumChocolateCard'

export default function ChocolateRecommendations({ recommendations }) {
  if (!recommendations || recommendations.length === 0) {
    return null
  }

  return (
    <div className="fade-in" style={{ padding: '0 1.5rem' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div className="recommendations-header" style={{
          textAlign: 'center',
          margin: 'var(--spacing-lg) 0 var(--spacing-md)',
          position: 'relative'
        }}>
          <h3 className="recommendations-title" style={{
            fontFamily: 'var(--font-heading)',
            fontSize: 'var(--text-2xl)',
            fontWeight: '700',
            color: 'var(--color-primary)'
          }}>
            My Recommendations for You
          </h3>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 max-h-[60vh] overflow-y-auto custom-scrollbar">
          {recommendations.map((chocolate) => (
            <PremiumChocolateCard key={chocolate.id} chocolate={chocolate} />
          ))}
        </div>

        {recommendations.length > 3 && (
          <div className="text-center mt-4">
            <p className="text-sm text-muted">
              {recommendations.length} chocolates match your preferences
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
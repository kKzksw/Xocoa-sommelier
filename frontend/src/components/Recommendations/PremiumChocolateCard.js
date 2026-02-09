import { useState } from 'react'

export default function PremiumChocolateCard({ chocolate }) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="chocolate-card-container" style={{
      marginBottom: '0',
      padding: '0',
      background: 'var(--color-bg-card)',
      border: '1px solid var(--color-primary)',
      borderRadius: '8px',
      boxShadow: '0 2px 6px rgba(45, 139, 127, 0.1)',
      transition: 'all 0.3s ease',
      overflow: 'hidden'
    }}>

      {/* Header Principal - Clickable */}
      <div
        onClick={() => setIsOpen(!isOpen)}
        style={{
          marginBottom: '0',
          padding: '1rem',
          background: 'var(--color-btn-primary-bg)',
          borderBottom: isOpen ? '2px solid var(--color-primary)' : 'none',
          cursor: 'pointer',
          transition: 'all 0.3s ease',
          position: 'relative'
        }}
      >
        {/* Chevron Icon */}
        <div style={{
          position: 'absolute',
          top: '1rem',
          right: '1rem',
          transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
          transition: 'transform 0.3s ease',
          color: '#FFFFFF',
          fontSize: '1.2rem',
          lineHeight: '1'
        }}>
          ▼
        </div>

        <h3 className="chocolate-title" style={{
          fontFamily: 'var(--font-heading)',
          fontSize: '1.1rem',
          fontWeight: '700',
          color: '#FFFFFF',
          marginBottom: '0.5rem',
          lineHeight: '1.3',
          paddingRight: '2rem'
        }}>
          {chocolate.name}
        </h3>

        {chocolate.maker_website ? (
          <a
            href={chocolate.maker_website}
            target="_blank"
            rel="noopener noreferrer"
            className="chocolate-brand"
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: '0.75rem',
              fontWeight: '500',
              color: 'rgba(255, 255, 255, 0.8)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              marginBottom: '0.5rem',
              textDecoration: 'none',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.3rem',
              transition: 'all 0.2s ease'
            }}
          >
            {chocolate.brand}
            <svg
              style={{ width: '12px', height: '12px' }}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
        ) : (
          <p className="chocolate-brand" style={{
            fontFamily: 'var(--font-body)',
            fontSize: '0.75rem',
            fontWeight: '500',
            color: 'rgba(255, 255, 255, 0.7)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: '0.5rem'
          }}>
            {chocolate.brand}
          </p>
        )}

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span className="cacao-percentage" style={{
            display: 'inline-block',
            background: 'var(--color-primary)',
            color: '#FFFFFF',
            padding: '0.2rem 0.6rem',
            borderRadius: '16px',
            fontSize: '0.75rem',
            fontWeight: '600'
          }}>
            {chocolate.cocoa_percentage}% cocoa
          </span>

          {chocolate.rating && (
            <div className="rating" style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.25rem',
              color: '#FFD700',
              fontSize: '0.9rem'
            }}>
              <span>★</span>
              <span style={{ fontSize: '0.75rem', color: 'rgba(255, 255, 255, 0.7)' }}>
                {chocolate.rating}/5
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Card Body - Conditionally displayed */}
      {isOpen && (
        <div style={{
          animation: 'slideDown 0.3s ease-out'
        }}>
          {/* Section General Information */}
          <div className="section-container" style={{
            marginBottom: '0.5rem',
            padding: '0.75rem',
            paddingBottom: '0.5rem',
            borderBottom: '1px solid rgba(45, 139, 127, 0.15)'
          }}>
            <h4 className="section-title" style={{
              fontFamily: 'var(--font-heading)',
              fontSize: '0.95rem',
              fontWeight: '600',
              color: 'var(--color-primary)',
              marginBottom: '0.5rem',
              position: 'relative'
            }}>
              General Information
              <span style={{
                content: '',
                position: 'absolute',
                bottom: '-4px',
                left: '0',
                width: '30px',
                height: '2px',
                background: 'var(--color-primary)',
                display: 'block'
              }}></span>
            </h4>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '0.4rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: '500', color: '#666666' }}>
                  Origin
                </span>
                <span style={{ fontSize: '0.85rem', color: 'var(--color-text-primary)', fontWeight: '500' }}>
                  {chocolate.origin_region && chocolate.origin_country
                    ? `${chocolate.origin_region}, ${chocolate.origin_country}`
                    : chocolate.origin_country || chocolate.origin_region}
                </span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: '500', color: '#666666' }}>
                  Type
                </span>
                <span style={{ fontSize: '0.85rem', color: 'var(--color-text-primary)', fontWeight: '500', textTransform: 'capitalize' }}>
                  {chocolate.type}
                </span>
              </div>

              {chocolate.bean_variety && (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: '500', color: '#666666' }}>
                    Variety
                  </span>
                  <span style={{ fontSize: '0.85rem', color: 'var(--color-text-primary)', fontWeight: '500' }}>
                    {chocolate.bean_variety}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Section Flavor Profile */}
          {chocolate.flavor_notes_primary && (
            <div className="section-container" style={{
              marginBottom: '0.5rem',
              padding: '0.75rem',
              paddingBottom: '0.5rem',
              borderBottom: '1px solid rgba(45, 139, 127, 0.15)'
            }}>
              <h4 className="section-title" style={{
                fontFamily: 'var(--font-heading)',
                fontSize: '0.95rem',
                fontWeight: '600',
                color: 'var(--color-primary)',
                marginBottom: '0.5rem',
                position: 'relative'
              }}>
                Flavor Profile
                <span style={{
                  content: '',
                  position: 'absolute',
                  bottom: '-4px',
                  left: '0',
                  width: '40px',
                  height: '2px',
                  background: 'var(--color-primary)',
                  display: 'block'
                }}></span>
              </h4>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-xs)', marginTop: '0.5rem' }}>
                {chocolate.flavor_notes_primary.split(',').map((flavor, index) => (
                  <span key={index} className="flavor-tag" style={{
                    background: 'rgba(45, 139, 127, 0.1)',
                    border: '1px solid rgba(45, 139, 127, 0.3)',
                    color: 'var(--color-primary)',
                    padding: '0.25rem 0.75rem',
                    borderRadius: '16px',
                    fontSize: 'var(--text-sm)',
                    transition: 'all 0.2s ease'
                  }}>
                    {flavor.trim()}
                  </span>
                ))}
              </div>

              {chocolate.flavor_notes_secondary && (
                <div style={{ marginTop: 'var(--space-sm)' }}>
                  <span style={{
                    fontSize: 'var(--text-sm)',
                    fontWeight: '500',
                    color: '#666666',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em'
                  }}>
                    Secondary:
                  </span>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-xs)', marginTop: '0.25rem' }}>
                    {chocolate.flavor_notes_secondary.split(',').map((flavor, index) => (
                      <span key={index} className="flavor-tag" style={{
                        background: 'rgba(45, 139, 127, 0.08)',
                        border: '1px solid rgba(45, 139, 127, 0.25)',
                        color: 'var(--color-primary-dark)',
                        padding: '0.25rem 0.75rem',
                        borderRadius: '16px',
                        fontSize: 'var(--text-sm)',
                        transition: 'all 0.2s ease'
                      }}>
                        {flavor.trim()}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Section Texture */}
          {(chocolate.texture_mouthfeel || chocolate.texture_melt || chocolate.texture_snap) && (
            <div className="section-container" style={{
              marginBottom: '0.5rem',
              padding: '0.75rem',
              paddingBottom: '0.5rem',
              borderBottom: '1px solid rgba(45, 139, 127, 0.15)'
            }}>
              <h4 className="section-title" style={{
                fontFamily: 'var(--font-heading)',
                fontSize: '0.95rem',
                fontWeight: '600',
                color: 'var(--color-primary)',
                marginBottom: '0.5rem',
                position: 'relative'
              }}>
                Texture
                <span style={{
                  content: '',
                  position: 'absolute',
                  bottom: '-4px',
                  left: '0',
                  width: '40px',
                  height: '2px',
                  background: 'var(--color-primary)',
                  display: 'block'
                }}></span>
              </h4>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '0.75rem' }}>
                {chocolate.texture_mouthfeel && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: '500', color: '#666666' }}>
                      Mouthfeel
                    </span>
                    <span style={{ fontSize: '0.85rem', color: 'var(--color-text-primary)', fontWeight: '500', textTransform: 'capitalize' }}>
                      {chocolate.texture_mouthfeel}
                    </span>
                  </div>
                )}

                {chocolate.texture_melt && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: '500', color: '#666666' }}>
                      Melt
                    </span>
                    <span style={{ fontSize: '0.85rem', color: 'var(--color-text-primary)', fontWeight: '500', textTransform: 'capitalize' }}>
                      {chocolate.texture_melt}
                    </span>
                  </div>
                )}

                {chocolate.texture_snap && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: '500', color: '#666666' }}>
                      Snap
                    </span>
                    <span style={{ fontSize: '0.85rem', color: 'var(--color-text-primary)', fontWeight: '500', textTransform: 'capitalize' }}>
                      {chocolate.texture_snap}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Section Pairings */}
          {(chocolate.pairings_wine || chocolate.pairings_spirits || chocolate.pairings_cheese) && (
            <div className="section-container" style={{
              marginBottom: '0.5rem',
              padding: '0.75rem',
              paddingBottom: '0.5rem',
              borderBottom: '1px solid rgba(45, 139, 127, 0.15)'
            }}>
              <h4 className="section-title" style={{
                fontFamily: 'var(--font-heading)',
                fontSize: '0.95rem',
                fontWeight: '600',
                color: 'var(--color-primary)',
                marginBottom: '0.5rem',
                position: 'relative'
              }}>
                Recommended Pairings
                <span style={{
                  content: '',
                  position: 'absolute',
                  bottom: '-4px',
                  left: '0',
                  width: '40px',
                  height: '2px',
                  background: 'var(--color-primary)',
                  display: 'block'
                }}></span>
              </h4>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 'var(--space-xs)' }}>
                {chocolate.pairings_wine && (
                  <div>
                    <span style={{
                      fontSize: 'var(--text-sm)',
                      fontWeight: '500',
                      color: '#666666',
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em'
                    }}>
                      Wines:
                    </span>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-xs)', marginTop: '0.25rem' }}>
                      {chocolate.pairings_wine.split(',').map((wine, index) => (
                        <span key={index} className="pairing-tag" style={{
                          background: 'rgba(45, 139, 127, 0.1)',
                          border: '1px solid rgba(45, 139, 127, 0.3)',
                          color: 'var(--color-primary)',
                          padding: '0.25rem 0.75rem',
                          borderRadius: '16px',
                          fontSize: 'var(--text-sm)',
                          transition: 'all 0.2s ease'
                        }}>
                          {wine.trim()}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {chocolate.pairings_spirits && (
                  <div style={{ marginTop: 'var(--space-sm)' }}>
                    <span style={{
                      fontSize: 'var(--text-sm)',
                      fontWeight: '500',
                      color: '#666666',
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em'
                    }}>
                      Spirits:
                    </span>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-xs)', marginTop: '0.25rem' }}>
                      {chocolate.pairings_spirits.split(',').map((spirit, index) => (
                        <span key={index} className="pairing-tag" style={{
                          background: 'rgba(45, 139, 127, 0.1)',
                          border: '1px solid rgba(45, 139, 127, 0.3)',
                          color: 'var(--color-primary)',
                          padding: '0.25rem 0.75rem',
                          borderRadius: '16px',
                          fontSize: 'var(--text-sm)',
                          transition: 'all 0.2s ease'
                        }}>
                          {spirit.trim()}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Footer with Price */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '1.5rem',
            paddingTop: '1rem',
            marginTop: '0.5rem',
            borderTop: '1px solid rgba(45, 139, 127, 0.2)'
          }}>
            {chocolate.price_retail && (
              <span style={{
                fontFamily: 'var(--font-body)',
                fontSize: 'var(--text-xl)',
                fontWeight: '700',
                color: 'var(--color-primary)'
              }}>
                ${chocolate.price_retail}
              </span>
            )}

            <span style={{
              fontSize: 'var(--text-sm)',
              fontWeight: '500',
              color: '#666666',
              textTransform: 'capitalize',
              padding: '0.25rem 0.75rem',
              background: 'rgba(45, 139, 127, 0.1)',
              borderRadius: '20px'
            }}>
              {chocolate.production_craft_level || 'Premium'}
            </span>
          </div>

          {/* Tasting Notes */}
          {chocolate.tasting_notes && (
            <div style={{
              background: 'rgba(45, 139, 127, 0.08)',
              border: '1px solid rgba(45, 139, 127, 0.25)',
              borderRadius: '6px',
              padding: '0.75rem',
              margin: '0.75rem'
            }}>
              <h5 style={{
                fontSize: '0.95rem',
                fontWeight: '600',
                color: 'var(--color-primary)',
                marginBottom: '0.5rem'
              }}>
                Tasting Notes
              </h5>
              <p style={{
                fontSize: '0.85rem',
                color: 'var(--color-text-primary)',
                lineHeight: '1.5'
              }}>
                {chocolate.tasting_notes}
              </p>
            </div>
          )}

          {/* Expert Review */}
          {chocolate.expert_review && (
            <div style={{
              background: 'rgba(45, 139, 127, 0.1)',
              border: '1px solid rgba(45, 139, 127, 0.3)',
              borderRadius: '6px',
              padding: '0.75rem',
              margin: '0.75rem',
              marginTop: '0.5rem'
            }}>
              <h5 style={{
                fontSize: '0.95rem',
                fontWeight: '600',
                color: 'var(--color-primary)',
                marginBottom: '0.5rem'
              }}>
                Expert Review
              </h5>
              <p style={{
                fontSize: '0.85rem',
                color: 'var(--color-text-primary)',
                fontStyle: 'italic',
                lineHeight: '1.5'
              }}>
                "{chocolate.expert_review}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
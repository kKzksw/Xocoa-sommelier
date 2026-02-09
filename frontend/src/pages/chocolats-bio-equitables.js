import Head from 'next/head'
import Header from '../components/UI/Header'
import Link from 'next/link'

export default function ChocolatsBioEquitables() {
  return (
    <>
      <Head>
        <title>Chocolats Bio et Équitables | Guide Fair Trade & Organic 2025</title>
        <meta name="description" content="Découvrez les meilleurs chocolats bio et équitables. Guide complet des certifications Fair Trade, Organic, Rainforest Alliance. Chocolat éthique et durable." />
        <meta name="keywords" content="chocolat bio, chocolat équitable, fair trade chocolate, organic chocolate, chocolat éthique, commerce équitable chocolat" />

        {/* Open Graph */}
        <meta property="og:title" content="Chocolats Bio et Équitables | Guide Fair Trade & Organic" />
        <meta property="og:description" content="Découvrez les meilleurs chocolats bio et équitables. Guide des certifications et chocolatiers engagés." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://xocoasommelier.netlify.app/chocolats-bio-equitables" />

        {/* Schema.org JSON-LD */}
        <script type="application/ld+json" dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "Chocolats Bio et Équitables : Guide Complet 2025",
            "description": "Guide complet des chocolats biologiques et équitables, certifications Fair Trade, Organic et pratiques durables",
            "url": "https://xocoasommelier.netlify.app/chocolats-bio-equitables",
            "author": {
              "@type": "Organization",
              "name": "XOCOA Sommelier"
            }
          })
        }} />
      </Head>

      <div className="min-h-screen" style={{ background: '#F5F5F0' }}>
        <Header />

        <main className="w-full px-4 md:px-16 py-8">
          <div className="max-w-4xl mx-auto">

            {/* Breadcrumb */}
            <nav className="mb-8 text-sm" style={{ color: '#3D2817' }}>
              <Link href="/" style={{ color: '#2D8B7F' }}>Accueil</Link>
              <span className="mx-2">›</span>
              <span>Chocolats Bio et Équitables</span>
            </nav>

            {/* Hero */}
            <div style={{
              background: 'white',
              borderRadius: '8px',
              padding: '3rem',
              marginBottom: '2rem',
              boxShadow: '0 2px 8px rgba(45, 139, 127, 0.1)'
            }}>
              <h1 style={{
                fontFamily: 'Sulphur Point, sans-serif',
                fontSize: '2.5rem',
                fontWeight: '700',
                color: '#2D8B7F',
                marginBottom: '1rem'
              }}>
                Chocolats Bio et Équitables
              </h1>
              <p style={{
                fontSize: '1.25rem',
                color: '#3D2817',
                marginBottom: '2rem',
                lineHeight: '1.8'
              }}>
                Consommer du chocolat avec conscience : découvrez les meilleurs chocolats certifiés bio et équitables, pour un plaisir respectueux des producteurs et de l'environnement.
              </p>
            </div>

            {/* Content */}
            <article style={{
              background: 'white',
              borderRadius: '8px',
              padding: '3rem',
              marginBottom: '2rem',
              boxShadow: '0 2px 8px rgba(45, 139, 127, 0.1)'
            }}>

              <h2 style={{
                fontFamily: 'Sulphur Point, sans-serif',
                fontSize: '1.75rem',
                fontWeight: '600',
                color: '#3D2817',
                marginTop: '2rem',
                marginBottom: '1rem',
                borderLeft: '4px solid #2D8B7F',
                paddingLeft: '1rem'
              }}>
                Pourquoi Choisir Bio et Équitable ?
              </h2>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                L'industrie du cacao fait face à des défis majeurs : <strong>déforestation</strong>, <strong>exploitation</strong> des producteurs, <strong>travail des enfants</strong> et <strong>usage intensif de pesticides</strong>. Choisir du chocolat bio et équitable, c'est participer activement à la solution.
              </p>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                Les certifications garantissent :
              </p>

              <ul style={{
                lineHeight: '2',
                marginBottom: '1.5rem',
                marginLeft: '2rem',
                color: '#1A1A1A'
              }}>
                <li><strong>Rémunération juste</strong> des producteurs (prix minimum garanti)</li>
                <li><strong>Pratiques agricoles durables</strong> sans pesticides de synthèse</li>
                <li><strong>Protection de la biodiversité</strong> et des écosystèmes</li>
                <li><strong>Interdiction du travail des enfants</strong></li>
                <li><strong>Traçabilité complète</strong> de la fève à la tablette</li>
              </ul>

              <h2 style={{
                fontFamily: 'Sulphur Point, sans-serif',
                fontSize: '1.75rem',
                fontWeight: '600',
                color: '#3D2817',
                marginTop: '2.5rem',
                marginBottom: '1rem',
                borderLeft: '4px solid #2D8B7F',
                paddingLeft: '1rem'
              }}>
                Les Certifications Principales
              </h2>

              <div style={{ marginBottom: '2rem' }}>
                <h3 style={{
                  fontWeight: '600',
                  fontSize: '1.25rem',
                  color: '#2D8B7F',
                  marginBottom: '0.75rem',
                  marginTop: '1.5rem'
                }}>
                  🌿 Bio / Organic (AB, EU Organic)
                </h3>
                <p style={{ lineHeight: '1.8', marginBottom: '1rem', color: '#1A1A1A' }}>
                  Garantit l'absence de pesticides de synthèse, d'OGM et d'engrais chimiques. Le cacao est cultivé selon les principes de l'agriculture biologique, respectant les cycles naturels et la santé des sols.
                </p>

                <h3 style={{
                  fontWeight: '600',
                  fontSize: '1.25rem',
                  color: '#2D8B7F',
                  marginBottom: '0.75rem',
                  marginTop: '1.5rem'
                }}>
                  🤝 Fair Trade / Max Havelaar
                </h3>
                <p style={{ lineHeight: '1.8', marginBottom: '1rem', color: '#1A1A1A' }}>
                  Assure un <strong>prix minimum garanti</strong> aux producteurs, supérieur au cours mondial, plus une prime investie dans des projets communautaires (écoles, infrastructures, santé). Interdit le travail forcé et celui des enfants.
                </p>

                <h3 style={{
                  fontWeight: '600',
                  fontSize: '1.25rem',
                  color: '#2D8B7F',
                  marginBottom: '0.75rem',
                  marginTop: '1.5rem'
                }}>
                  🌳 Rainforest Alliance
                </h3>
                <p style={{ lineHeight: '1.8', marginBottom: '1rem', color: '#1A1A1A' }}>
                  Certification axée sur la <strong>protection des forêts</strong>, la biodiversité et l'amélioration des conditions de travail. Moins stricte sur le prix que Fair Trade mais très exigeante sur l'environnement.
                </p>

                <h3 style={{
                  fontWeight: '600',
                  fontSize: '1.25rem',
                  color: '#2D8B7F',
                  marginBottom: '0.75rem',
                  marginTop: '1.5rem'
                }}>
                  🏢 B-Corp
                </h3>
                <p style={{ lineHeight: '1.8', marginBottom: '1rem', color: '#1A1A1A' }}>
                  Certification d'entreprise évaluant l'<strong>impact social et environnemental global</strong>. Les entreprises B-Corp s'engagent à équilibrer profit et responsabilité sociétale.
                </p>

                <h3 style={{
                  fontWeight: '600',
                  fontSize: '1.25rem',
                  color: '#2D8B7F',
                  marginBottom: '0.75rem',
                  marginTop: '1.5rem'
                }}>
                  🤲 Direct Trade
                </h3>
                <p style={{ lineHeight: '1.8', marginBottom: '1rem', color: '#1A1A1A' }}>
                  Relation <strong>directe entre le chocolatier et le producteur</strong>, sans intermédiaires. Permet une rémunération encore supérieure et un contrôle qualité optimal, mais sans certification tierce partie.
                </p>
              </div>

              <h2 style={{
                fontFamily: 'Sulphur Point, sans-serif',
                fontSize: '1.75rem',
                fontWeight: '600',
                color: '#3D2817',
                marginTop: '2.5rem',
                marginBottom: '1rem',
                borderLeft: '4px solid #2D8B7F',
                paddingLeft: '1rem'
              }}>
                Marques et Chocolatiers Engagés
              </h2>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                De nombreux chocolatiers d'excellence sont engagés dans le bio et l'équitable :
              </p>

              <ul style={{
                lineHeight: '2',
                marginBottom: '1.5rem',
                marginLeft: '2rem',
                color: '#1A1A1A'
              }}>
                <li><strong>Alter Eco</strong> - 100% bio et Fair Trade, B-Corp certifié</li>
                <li><strong>Ethiquable</strong> - Coopérative française, commerce équitable pionnier</li>
                <li><strong>Tony's Chocolonely</strong> - Mission d'éradiquer l'esclavage du cacao</li>
                <li><strong>Divine Chocolate</strong> - Entreprise détenue par les producteurs eux-mêmes</li>
                <li><strong>Original Beans</strong> - Bio, Direct Trade, reforestation</li>
                <li><strong>Chocolats Halba</strong> - Fair Trade et programmes sociaux</li>
                <li><strong>Ombar</strong> - Raw, bio, vegan et équitable</li>
              </ul>

              <h2 style={{
                fontFamily: 'Sulphur Point, sans-serif',
                fontSize: '1.75rem',
                fontWeight: '600',
                color: '#3D2817',
                marginTop: '2.5rem',
                marginBottom: '1rem',
                borderLeft: '4px solid #2D8B7F',
                paddingLeft: '1rem'
              }}>
                Qualité Gustative
              </h2>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                <strong>Idée reçue</strong> : "Bio et équitable, c'est moins bon". <strong>Faux !</strong> Les chocolats certifiés sont souvent de <strong>qualité supérieure</strong> car :
              </p>

              <ul style={{
                lineHeight: '2',
                marginBottom: '1.5rem',
                marginLeft: '2rem',
                color: '#1A1A1A'
              }}>
                <li>Meilleure sélection des fèves (variétés fines privilégiées)</li>
                <li>Fermentation et séchage optimaux (temps et savoir-faire)</li>
                <li>Sols vivants produisent des arômes plus complexes</li>
                <li>Traçabilité permettant des single-origin d'exception</li>
                <li>Chocolatiers engagés investissent dans la qualité</li>
              </ul>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                Les chocolats bio et équitables raflent régulièrement des <strong>prix aux concours internationaux</strong> (International Chocolate Awards, Academy of Chocolate).
              </p>

              <h2 style={{
                fontFamily: 'Sulphur Point, sans-serif',
                fontSize: '1.75rem',
                fontWeight: '600',
                color: '#3D2817',
                marginTop: '2.5rem',
                marginBottom: '1rem',
                borderLeft: '4px solid #2D8B7F',
                paddingLeft: '1rem'
              }}>
                Comment Choisir ?
              </h2>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                <strong>Conseils pour s'y retrouver</strong> :
              </p>

              <ul style={{
                lineHeight: '2',
                marginBottom: '1.5rem',
                marginLeft: '2rem',
                color: '#1A1A1A'
              }}>
                <li><strong>Multi-certifié</strong> : Recherchez "Bio + Fair Trade" pour un engagement maximal</li>
                <li><strong>Origine unique</strong> : Privilégiez les single-origin pour la traçabilité</li>
                <li><strong>Bean-to-bar</strong> : Chocolatiers contrôlant toute la chaîne</li>
                <li><strong>Transparence</strong> : Marques communiquant clairement sur leurs pratiques</li>
                <li><strong>Prix juste</strong> : Un bon chocolat éthique coûte 4-8€/100g (tablette artisanale)</li>
              </ul>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                <strong>Attention aux fausses promesses</strong> : méfiez-vous des mentions vagues type "cacao responsable" sans certification tierce. Les vrais engagements sont vérifiables via des labels officiels.
              </p>

              <h2 style={{
                fontFamily: 'Sulphur Point, sans-serif',
                fontSize: '1.75rem',
                fontWeight: '600',
                color: '#3D2817',
                marginTop: '2.5rem',
                marginBottom: '1rem',
                borderLeft: '4px solid #2D8B7F',
                paddingLeft: '1rem'
              }}>
                Impact Environnemental
              </h2>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                L'agriculture biologique du cacao permet :
              </p>

              <ul style={{
                lineHeight: '2',
                marginBottom: '1.5rem',
                marginLeft: '2rem',
                color: '#1A1A1A'
              }}>
                <li><strong>Réduction de 30%</strong> des émissions de CO2 vs conventionnel</li>
                <li><strong>Préservation de la biodiversité</strong> (agroforesterie)</li>
                <li><strong>Protection des nappes phréatiques</strong> (zéro pesticides)</li>
                <li><strong>Santé des sols</strong> améliorée (compost, rotation des cultures)</li>
                <li><strong>Résilience climatique</strong> accrue des plantations</li>
              </ul>

            </article>

            {/* CTA */}
            <div style={{
              background: '#2D8B7F',
              color: 'white',
              borderRadius: '8px',
              padding: '3rem',
              textAlign: 'center',
              marginBottom: '3rem'
            }}>
              <h2 style={{
                fontFamily: 'Sulphur Point, sans-serif',
                fontSize: '2rem',
                fontWeight: '700',
                marginBottom: '1rem'
              }}>
                Trouvez Votre Chocolat Bio et Équitable
              </h2>
              <p style={{
                fontSize: '1.125rem',
                marginBottom: '2rem',
                opacity: 0.95
              }}>
                Notre Sommelier IA sélectionne pour vous les meilleurs chocolats certifiés selon vos goûts.
              </p>
              <Link href="/">
                <button style={{
                  background: '#1A1A1A',
                  color: 'white',
                  padding: '1rem 2.5rem',
                  borderRadius: '24px',
                  border: 'none',
                  fontSize: '1.125rem',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'transform 0.2s',
                  fontFamily: 'Sulphur Point, sans-serif'
                }}
                onMouseEnter={(e) => e.target.style.transform = 'translateY(-2px)'}
                onMouseLeave={(e) => e.target.style.transform = 'translateY(0)'}
                >
                  Consulter le Sommelier
                </button>
              </Link>
            </div>

          </div>
        </main>
      </div>
    </>
  )
}

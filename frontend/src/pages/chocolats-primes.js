import Head from 'next/head'
import Header from '../components/UI/Header'
import Link from 'next/link'

export default function ChocolatsPrimes() {
  return (
    <>
      <Head>
        <title>Chocolats Primés | Meilleurs Chocolats du Monde - Awards 2025</title>
        <meta name="description" content="Découvrez les chocolats primés aux plus prestigieux concours : International Chocolate Awards, Academy of Chocolate, Good Food Awards. Guide des meilleurs chocolats du monde." />
        <meta name="keywords" content="chocolat primé, award winning chocolate, meilleur chocolat du monde, international chocolate awards, academy of chocolate, chocolat médaillé" />

        {/* Open Graph */}
        <meta property="og:title" content="Chocolats Primés | Meilleurs Chocolats du Monde" />
        <meta property="og:description" content="Découvrez les chocolats primés aux prestigieux concours internationaux." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://xocoasommelier.netlify.app/chocolats-primes" />

        {/* Schema.org JSON-LD */}
        <script type="application/ld+json" dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "Chocolats Primés : Les Meilleurs du Monde",
            "description": "Guide des chocolats primés aux concours internationaux : International Chocolate Awards, Academy of Chocolate",
            "url": "https://xocoasommelier.netlify.app/chocolats-primes"
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
              <span>Chocolats Primés</span>
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
                Chocolats Primés 🏆
              </h1>
              <p style={{
                fontSize: '1.25rem',
                color: '#3D2817',
                marginBottom: '2rem',
                lineHeight: '1.8'
              }}>
                Les meilleurs chocolats du monde reconnus par les concours les plus prestigieux. Excellence, innovation et savoir-faire récompensés.
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
                Les Concours de Référence
              </h2>

              <div style={{ marginBottom: '2rem' }}>
                <h3 style={{
                  fontWeight: '600',
                  fontSize: '1.25rem',
                  color: '#2D8B7F',
                  marginBottom: '0.75rem',
                  marginTop: '1.5rem'
                }}>
                  🌍 International Chocolate Awards (ICA)
                </h3>
                <p style={{ lineHeight: '1.8', marginBottom: '1rem', color: '#1A1A1A' }}>
                  Le <strong>"Oscar du chocolat"</strong>. Fondé en 2012, l'ICA est le plus prestigieux concours mondial. Compétition en 3 phases : régionales, continentales, puis finale mondiale. Jury d'experts internationaux (chocolatiers, sommeliers, journalistes). Plus de <strong>1500 chocolats</strong> évalués chaque année.
                </p>

                <h3 style={{
                  fontWeight: '600',
                  fontSize: '1.25rem',
                  color: '#2D8B7F',
                  marginBottom: '0.75rem',
                  marginTop: '1.5rem'
                }}>
                  🎓 Academy of Chocolate Awards
                </h3>
                <p style={{ lineHeight: '1.8', marginBottom: '1rem', color: '#1A1A1A' }}>
                  Basé au Royaume-Uni depuis 2005. Réputé pour sa <strong>rigueur d'évaluation</strong>. 3 niveaux : Bronze, Silver, Gold. Catégories multiples : bean-to-bar, pralinés, ganaches, inclusions. Jugement à l'aveugle par des professionnels chevronnés.
                </p>

                <h3 style={{
                  fontWeight: '600',
                  fontSize: '1.25rem',
                  color: '#2D8B7F',
                  marginBottom: '0.75rem',
                  marginTop: '1.5rem'
                }}>
                  🥇 Great Taste Awards
                </h3>
                <p style={{ lineHeight: '1.8', marginBottom: '1rem', color: '#1A1A1A' }}>
                  Organisé par la Guild of Fine Food (UK). Plus de <strong>14 000 produits</strong> évalués annuellement. Étoiles : 1, 2 ou 3 étoiles (exceptionnelle). Récompense la qualité gustative pure.
                </p>

                <h3 style={{
                  fontWeight: '600',
                  fontSize: '1.25rem',
                  color: '#2D8B7F',
                  marginBottom: '0.75rem',
                  marginTop: '1.5rem'
                }}>
                  🇺🇸 Good Food Awards (USA)
                </h3>
                <p style={{ lineHeight: '1.8', marginBottom: '1rem', color: '#1A1A1A' }}>
                  Focus sur les chocolatiers <strong>artisanaux américains</strong> engagés. Critères : goût + pratiques durables + approvisionnement éthique. Finalistes présentés à San Francisco chaque année.
                </p>

                <h3 style={{
                  fontWeight: '600',
                  fontSize: '1.25rem',
                  color: '#2D8B7F',
                  marginBottom: '0.75rem',
                  marginTop: '1.5rem'
                }}>
                  🇫🇷 Salon du Chocolat - Tablette d'Or
                </h3>
                <p style={{ lineHeight: '1.8', marginBottom: '1rem', color: '#1A1A1A' }}>
                  Le plus grand événement chocolat au monde (Paris). Concours annuel avec catégories variées. Récompense l'innovation et l'excellence française et internationale.
                </p>

                <h3 style={{
                  fontWeight: '600',
                  fontSize: '1.25rem',
                  color: '#2D8B7F',
                  marginBottom: '0.75rem',
                  marginTop: '1.5rem'
                }}>
                  🏅 European Bean-to-Bar Competition
                </h3>
                <p style={{ lineHeight: '1.8', marginBottom: '1rem', color: '#1A1A1A' }}>
                  Spécifique aux chocolatiers bean-to-bar européens. Évaluation technique : torréfaction, conchage, texture, arômes. Niveau d'exigence très élevé.
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
                Critères d'Évaluation
              </h2>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                Les jurys évaluent selon des critères stricts :
              </p>

              <ul style={{
                lineHeight: '2',
                marginBottom: '1.5rem',
                marginLeft: '2rem',
                color: '#1A1A1A'
              }}>
                <li><strong>Apparence</strong> : Brillance, uniformité, absence de défauts</li>
                <li><strong>Snap</strong> : Cassant net (tempérage réussi)</li>
                <li><strong>Arômes</strong> : Complexité, intensité, équilibre</li>
                <li><strong>Texture</strong> : Fonte en bouche, onctuosité</li>
                <li><strong>Saveurs</strong> : Profondeur, longueur, persistance</li>
                <li><strong>Innovation</strong> : Créativité, originalité</li>
                <li><strong>Technique</strong> : Maîtrise des processus de fabrication</li>
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
                Chocolatiers Mult-Primés
              </h2>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                Certains chocolatiers accumulent les récompenses année après année :
              </p>

              <ul style={{
                lineHeight: '2',
                marginBottom: '1.5rem',
                marginLeft: '2rem',
                color: '#1A1A1A'
              }}>
                <li><strong>Friis-Holm</strong> (Danemark) - 50+ médailles ICA, élu meilleur au monde</li>
                <li><strong>Pacari</strong> (Équateur) - Plus de 200 awards, champion sud-américain</li>
                <li><strong>Amedei</strong> (Italie) - Légende italienne, Chuao et Porcelana mythiques</li>
                <li><strong>Domori</strong> (Italie) - Pionnier bean-to-bar, collections rares</li>
                <li><strong>Pralus</strong> (France) - Excellence française multi-primée</li>
                <li><strong>Pump Street Bakery</strong> (UK) - Gold Academy of Chocolate multiple</li>
                <li><strong>Manoa</strong> (Hawaii) - Bean-to-bar américain primé ICA</li>
                <li><strong>Bonnat</strong> (France) - Tradition d'excellence depuis 1884</li>
                <li><strong>Dick Taylor</strong> (USA) - Good Food Awards répétés</li>
                <li><strong>Original Beans</strong> (Suisse/Pays-Bas) - Awards sustainability + goût</li>
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
                Pourquoi les Awards Comptent ?
              </h2>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                Les récompenses ne sont pas que du marketing :
              </p>

              <ul style={{
                lineHeight: '2',
                marginBottom: '1.5rem',
                marginLeft: '2rem',
                color: '#1A1A1A'
              }}>
                <li><strong>Garantie qualité</strong> : Évaluation objective par des experts</li>
                <li><strong>Repère fiable</strong> : Aide au choix parmi des milliers de références</li>
                <li><strong>Reconnaissance artisans</strong> : Visibilité pour petits producteurs</li>
                <li><strong>Innovation encouragée</strong> : Récompense la créativité</li>
                <li><strong>Standards élevés</strong> : Pousse l'industrie vers l'excellence</li>
                <li><strong>Transparence</strong> : Jugements documentés et tracés</li>
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
                Comment Lire les Médailles ?
              </h2>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                Sur les emballages, vous verrez :
              </p>

              <ul style={{
                lineHeight: '2',
                marginBottom: '1.5rem',
                marginLeft: '2rem',
                color: '#1A1A1A'
              }}>
                <li><strong>Gold / Or</strong> : Excellence absolue (rarement attribué)</li>
                <li><strong>Silver / Argent</strong> : Très haute qualité</li>
                <li><strong>Bronze</strong> : Bonne qualité reconnue</li>
                <li><strong>Winner / Laureate</strong> : Vainqueur de catégorie</li>
                <li><strong>3 étoiles</strong> (Great Taste) : Exceptionnelle</li>
                <li><strong>Regional Winner</strong> : Meilleur de sa région (ICA)</li>
                <li><strong>World Final</strong> : Sélectionné pour la finale mondiale</li>
              </ul>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                <strong>Astuce</strong> : Vérifiez l'année de l'award (la fraîcheur compte !) et le nom précis du concours (certains sont plus prestigieux).
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
                Les Tendances Awards 2025
              </h2>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                Les concours reflètent les évolutions du marché :
              </p>

              <ul style={{
                lineHeight: '2',
                marginBottom: '1.5rem',
                marginLeft: '2rem',
                color: '#1A1A1A'
              }}>
                <li><strong>Sustainability awards</strong> : Nouvelles catégories éco-responsables</li>
                <li><strong>Bean-to-bar en hausse</strong> : Artisans raflent les médailles vs industriels</li>
                <li><strong>Single-origin</strong> : Terroirs uniques davantage récompensés</li>
                <li><strong>Inclusions insolites</strong> : Créativité avec ingrédients locaux</li>
                <li><strong>Cacaos rares</strong> : Nacional, Criollo, Porcelana très valorisés</li>
                <li><strong>Direct Trade</strong> : Critère éthique de plus en plus important</li>
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
                Acheter des Chocolats Primés
              </h2>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                <strong>Où trouver ces pépites ?</strong>
              </p>

              <ul style={{
                lineHeight: '2',
                marginBottom: '1.5rem',
                marginLeft: '2rem',
                color: '#1A1A1A'
              }}>
                <li><strong>Boutiques spécialisées</strong> : Chocolatiers, épiceries fines</li>
                <li><strong>En ligne</strong> : Sites des chocolatiers, marketplaces chocolat</li>
                <li><strong>Salons</strong> : Salon du Chocolat, foires gastronomiques</li>
                <li><strong>Épiceries bio</strong> : Sélections de chocolats primés équitables</li>
                <li><strong>Cave à chocolats</strong> : Concept stores dédiés (grandes villes)</li>
              </ul>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                <strong>Prix</strong> : Comptez 6-12€ pour une tablette primée de 100g (selon rareté et awards).
              </p>

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
                Découvrez Nos Chocolats Primés
              </h2>
              <p style={{
                fontSize: '1.125rem',
                marginBottom: '2rem',
                opacity: 0.95
              }}>
                Notre base compte 984 chocolats primés aux concours internationaux. Trouvez le vôtre !
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

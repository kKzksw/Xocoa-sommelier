import Head from 'next/head'
import Header from '../components/UI/Header'
import Link from 'next/link'

export default function BeanToBar() {
  return (
    <>
      <Head>
        <title>Chocolat Bean-to-Bar | Guide Complet Artisan Chocolatier 2025</title>
        <meta name="description" content="Découvrez le mouvement Bean-to-Bar : chocolatiers artisanaux contrôlant toute la chaîne. Guide complet des meilleurs craftsmen et leurs méthodes." />
        <meta name="keywords" content="bean to bar, chocolat artisanal, craft chocolate, chocolatier artisan, tree to bar, single origin chocolate" />

        {/* Open Graph */}
        <meta property="og:title" content="Chocolat Bean-to-Bar | Guide Artisan Chocolatier" />
        <meta property="og:description" content="Découvrez le mouvement Bean-to-Bar et les meilleurs chocolatiers artisanaux." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://xocoasommelier.netlify.app/bean-to-bar" />

        {/* Schema.org JSON-LD */}
        <script type="application/ld+json" dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "Chocolat Bean-to-Bar : Le Mouvement Artisanal",
            "description": "Guide complet du chocolat bean-to-bar, chocolatiers artisanaux et méthodes de fabrication traditionnelles",
            "url": "https://xocoasommelier.netlify.app/bean-to-bar"
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
              <span>Bean-to-Bar</span>
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
                Chocolat Bean-to-Bar
              </h1>
              <p style={{
                fontSize: '1.25rem',
                color: '#3D2817',
                marginBottom: '2rem',
                lineHeight: '1.8'
              }}>
                Le mouvement artisanal qui révolutionne le monde du chocolat : de la fève à la tablette, découvrez la passion des chocolatiers qui maîtrisent chaque étape.
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
                Qu'est-ce que le Bean-to-Bar ?
              </h2>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                <strong>Bean-to-Bar</strong> (littéralement "de la fève à la tablette") désigne des chocolatiers qui <strong>contrôlent toute la chaîne de fabrication</strong>, depuis l'achat des fèves de cacao auprès des producteurs jusqu'à la création de la tablette finale.
              </p>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                Contrairement aux chocolatiers traditionnels qui achètent du chocolat de couverture déjà fabriqué, les artisans bean-to-bar :
              </p>

              <ul style={{
                lineHeight: '2',
                marginBottom: '1.5rem',
                marginLeft: '2rem',
                color: '#1A1A1A'
              }}>
                <li>Sélectionnent directement les <strong>fèves brutes</strong></li>
                <li>Contrôlent la <strong>torréfaction</strong> (profils de température uniques)</li>
                <li>Maîtrisent le <strong>broyage et le conchage</strong></li>
                <li>Créent leurs propres <strong>recettes</strong> (pourcentages, sucres, inclusions)</li>
                <li>Assurent la <strong>traçabilité complète</strong></li>
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
                Les Étapes de Fabrication
              </h2>

              <div style={{ marginBottom: '2rem' }}>
                <h3 style={{
                  fontWeight: '600',
                  fontSize: '1.25rem',
                  color: '#2D8B7F',
                  marginBottom: '0.75rem',
                  marginTop: '1.5rem'
                }}>
                  1. Sélection des Fèves
                </h3>
                <p style={{ lineHeight: '1.8', marginBottom: '1rem', color: '#1A1A1A' }}>
                  Relation directe avec les producteurs (<strong>Direct Trade</strong>). Sélection rigoureuse des <strong>single-origin</strong> ou <strong>blends</strong> selon le profil aromatique recherché.
                </p>

                <h3 style={{
                  fontWeight: '600',
                  fontSize: '1.25rem',
                  color: '#2D8B7F',
                  marginBottom: '0.75rem',
                  marginTop: '1.5rem'
                }}>
                  2. Tri et Nettoyage
                </h3>
                <p style={{ lineHeight: '1.8', marginBottom: '1rem', color: '#1A1A1A' }}>
                  Élimination des fèves défectueuses, corps étrangers et impuretés. Étape cruciale pour la qualité finale.
                </p>

                <h3 style={{
                  fontWeight: '600',
                  fontSize: '1.25rem',
                  color: '#2D8B7F',
                  marginBottom: '0.75rem',
                  marginTop: '1.5rem'
                }}>
                  3. Torréfaction
                </h3>
                <p style={{ lineHeight: '1.8', marginBottom: '1rem', color: '#1A1A1A' }}>
                  <strong>Étape clé</strong> révélant les arômes. Chaque artisan développe ses propres profils : température (120-150°C), durée (15-45 min), courbe de chauffe. La torréfaction influence 80% du profil aromatique final.
                </p>

                <h3 style={{
                  fontWeight: '600',
                  fontSize: '1.25rem',
                  color: '#2D8B7F',
                  marginBottom: '0.75rem',
                  marginTop: '1.5rem'
                }}>
                  4. Concassage et Vannage
                </h3>
                <p style={{ lineHeight: '1.8', marginBottom: '1rem', color: '#1A1A1A' }}>
                  Séparation de la <strong>coque</strong> (inutile) et des <strong>grués de cacao</strong> (cœur comestible). Les grués contiennent 50-55% de beurre de cacao.
                </p>

                <h3 style={{
                  fontWeight: '600',
                  fontSize: '1.25rem',
                  color: '#2D8B7F',
                  marginBottom: '0.75rem',
                  marginTop: '1.5rem'
                }}>
                  5. Broyage (Refining)
                </h3>
                <p style={{ lineHeight: '1.8', marginBottom: '1rem', color: '#1A1A1A' }}>
                  Transformation des grués en <strong>liqueur de cacao</strong> (pâte liquide). Broyage fin jusqu'à obtenir des particules de 18-25 microns pour une texture soyeuse.
                </p>

                <h3 style={{
                  fontWeight: '600',
                  fontSize: '1.25rem',
                  color: '#2D8B7F',
                  marginBottom: '0.75rem',
                  marginTop: '1.5rem'
                }}>
                  6. Conchage
                </h3>
                <p style={{ lineHeight: '1.8', marginBottom: '1rem', color: '#1A1A1A' }}>
                  Brassage prolongé (12-72h) à température contrôlée. Développe la <strong>rondeur</strong>, élimine l'acidité indésirable et homogénéise la texture. Secret de fabrication de chaque artisan.
                </p>

                <h3 style={{
                  fontWeight: '600',
                  fontSize: '1.25rem',
                  color: '#2D8B7F',
                  marginBottom: '0.75rem',
                  marginTop: '1.5rem'
                }}>
                  7. Tempérage
                </h3>
                <p style={{ lineHeight: '1.8', marginBottom: '1rem', color: '#1A1A1A' }}>
                  Cristallisation contrôlée du beurre de cacao pour obtenir le <strong>brillant</strong>, le <strong>snap</strong> (cassant) et éviter le blanchiment. Technique délicate nécessitant précision.
                </p>

                <h3 style={{
                  fontWeight: '600',
                  fontSize: '1.25rem',
                  color: '#2D8B7F',
                  marginBottom: '0.75rem',
                  marginTop: '1.5rem'
                }}>
                  8. Moulage et Démoulage
                </h3>
                <p style={{ lineHeight: '1.8', marginBottom: '1rem', color: '#1A1A1A' }}>
                  Coulée dans des moules, refroidissement puis démoulage manuel. Emballage artisanal soigné.
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
                Pourquoi Choisir Bean-to-Bar ?
              </h2>

              <ul style={{
                lineHeight: '2',
                marginBottom: '1.5rem',
                marginLeft: '2rem',
                color: '#1A1A1A'
              }}>
                <li><strong>Qualité supérieure</strong> : Contrôle total = excellence</li>
                <li><strong>Traçabilité</strong> : Origine exacte des fèves connue</li>
                <li><strong>Profils uniques</strong> : Signatures aromatiques distinctives</li>
                <li><strong>Éthique</strong> : Relation directe = rémunération juste des producteurs</li>
                <li><strong>Transparence</strong> : Ingrédients simples et clairs (souvent 2-3 ingrédients seulement)</li>
                <li><strong>Artisanat</strong> : Savoir-faire et passion vs industrie de masse</li>
                <li><strong>Innovation</strong> : Expérimentation et créativité</li>
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
                Chocolatiers Bean-to-Bar Incontournables
              </h2>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                <strong>France</strong> :
              </p>
              <ul style={{
                lineHeight: '2',
                marginBottom: '1.5rem',
                marginLeft: '2rem',
                color: '#1A1A1A'
              }}>
                <li>Pralus - Pionnier français du bean-to-bar</li>
                <li>Bonnat - Un des plus anciens (1884)</li>
                <li>Castelanne - Excellence bordelaise</li>
                <li>À Morin - Artisan lyonnais primé</li>
                <li>Thibaut - Tours, focus sur les terroirs</li>
              </ul>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                <strong>International</strong> :
              </p>
              <ul style={{
                lineHeight: '2',
                marginBottom: '1.5rem',
                marginLeft: '2rem',
                color: '#1A1A1A'
              }}>
                <li>Friis-Holm (Danemark) - Régulièrement élu meilleur au monde</li>
                <li>Amedei (Italie) - Légende toscane</li>
                <li>Domori (Italie) - Spécialiste des Criollos rares</li>
                <li>Akesson's (Madagascar) - Tree-to-bar authentique</li>
                <li>Pump Street Bakery (UK) - Inventifs et primés</li>
                <li>Ritual (USA) - Pionniers californiens</li>
                <li>Dick Taylor (USA) - Approche artisanale pure</li>
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
                Bean-to-Bar vs Tree-to-Bar
              </h2>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                Le <strong>Tree-to-Bar</strong> va encore plus loin : le chocolatier <strong>possède ses propres plantations</strong>. Il contrôle :
              </p>

              <ul style={{
                lineHeight: '2',
                marginBottom: '1.5rem',
                marginLeft: '2rem',
                color: '#1A1A1A'
              }}>
                <li>La culture du cacao (variétés, agroforesterie)</li>
                <li>La récolte et la fermentation</li>
                <li>Le séchage des fèves</li>
                <li>...puis toutes les étapes bean-to-bar</li>
              </ul>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                <strong>Exemples</strong> : Akesson's (Madagascar), Original Beans (Équateur), Claudio Corallo (São Tomé). Démarche ultime mais très rare.
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
                Comment Reconnaître un Vrai Bean-to-Bar ?
              </h2>

              <ul style={{
                lineHeight: '2',
                marginBottom: '1.5rem',
                marginLeft: '2rem',
                color: '#1A1A1A'
              }}>
                <li><strong>Origine précise</strong> : Pays, région, souvent plantation</li>
                <li><strong>Liste d'ingrédients courte</strong> : Cacao, sucre (parfois beurre de cacao ajouté)</li>
                <li><strong>Pourcentage de cacao</strong> indiqué</li>
                <li><strong>Absence d'additifs</strong> : Pas de lécithine, arômes, conservateurs</li>
                <li><strong>Prix reflétant la qualité</strong> : 5-10€/100g en moyenne</li>
                <li><strong>Communication transparente</strong> : Histoire des fèves, méthode de fabrication</li>
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
                Découvrez les Meilleurs Bean-to-Bar
              </h2>
              <p style={{
                fontSize: '1.125rem',
                marginBottom: '2rem',
                opacity: 0.95
              }}>
                Notre Sommelier IA vous guide vers les chocolats artisanaux qui correspondent à vos goûts.
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

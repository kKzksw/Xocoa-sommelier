import Head from 'next/head'
import Header from '../components/UI/Header'
import Link from 'next/link'

export default function ChocolatsMadagascar() {
  return (
    <>
      <Head>
        <title>Chocolats de Madagascar | Les Meilleurs Chocolats Malgaches Premium</title>
        <meta name="description" content="Découvrez les meilleurs chocolats de Madagascar. Terroir unique de Sambirano, saveurs fruitées et acidulées. Guide complet des chocolatiers artisanaux malgaches." />
        <meta name="keywords" content="chocolat Madagascar, chocolat Sambirano, chocolat malgache, cacao Madagascar, chocolat artisanal Madagascar, bean to bar Madagascar" />

        {/* Open Graph */}
        <meta property="og:title" content="Chocolats de Madagascar | Les Meilleurs Chocolats Malgaches Premium" />
        <meta property="og:description" content="Découvrez les meilleurs chocolats de Madagascar. Terroir unique de Sambirano, saveurs fruitées et acidulées." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://xocoasommelier.netlify.app/chocolats-madagascar" />

        {/* Schema.org JSON-LD */}
        <script type="application/ld+json" dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": "Chocolats de Madagascar",
            "description": "Guide complet des meilleurs chocolats de Madagascar, terroir de Sambirano et saveurs fruitées uniques",
            "url": "https://xocoasommelier.netlify.app/chocolats-madagascar",
            "inLanguage": "fr-FR",
            "about": {
              "@type": "Product",
              "name": "Chocolat de Madagascar",
              "category": "Chocolat Premium"
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
              <span>Chocolats de Madagascar</span>
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
                Chocolats de Madagascar
              </h1>
              <p style={{
                fontSize: '1.25rem',
                color: '#3D2817',
                marginBottom: '2rem',
                lineHeight: '1.8'
              }}>
                Découvrez l'excellence du cacao malgache, un terroir d'exception reconnu mondialement pour ses saveurs fruitées et acidulées uniques.
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
                Un Terroir d'Exception
              </h2>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                <strong>Madagascar</strong> produit certains des cacaos les plus recherchés au monde. Avec ses plantations concentrées dans la <strong>vallée de Sambirano</strong> au nord-ouest de l'île, le terroir malgache offre des conditions idéales : climat tropical, sols volcaniques riches et savoir-faire ancestral.
              </p>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                Les fèves de cacao de Madagascar sont principalement de variété <strong>Trinitario</strong>, un hybride alliant la finesse du Criollo et la robustesse du Forastero. Cette génétique unique, combinée au terroir exceptionnel, produit des chocolats aux profils aromatiques incomparables.
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
                Profil Aromatique Unique
              </h2>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                Les chocolats de Madagascar se distinguent par leur <strong>acidité marquée</strong> et leurs <strong>notes fruitées intenses</strong>. On y retrouve fréquemment :
              </p>

              <ul style={{
                lineHeight: '2',
                marginBottom: '1.5rem',
                marginLeft: '2rem',
                color: '#1A1A1A'
              }}>
                <li><strong>Fruits rouges</strong> : framboise, fraise, cerise</li>
                <li><strong>Agrumes</strong> : citron, pamplemousse, orange</li>
                <li><strong>Fruits tropicaux</strong> : passion, litchi, mangue</li>
                <li><strong>Notes lactiques</strong> : yaourt, crème fraîche</li>
                <li><strong>Nuances florales</strong> : jasmin, fleur d'oranger</li>
              </ul>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                Cette palette aromatique exceptionnelle fait du chocolat malgache un favori des sommeliers et amateurs éclairés.
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
                Chocolatiers de Référence
              </h2>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                De nombreux chocolatiers artisanaux travaillent le cacao de Madagascar, parmi les plus reconnus :
              </p>

              <ul style={{
                lineHeight: '2',
                marginBottom: '1.5rem',
                marginLeft: '2rem',
                color: '#1A1A1A'
              }}>
                <li><strong>Åkesson's</strong> - Producteur et chocolatier bean-to-bar sur place</li>
                <li><strong>Madécasse</strong> - Premier chocolatier bean-to-bar 100% malgache</li>
                <li><strong>Pralus</strong> - Collection plantation Madagascar Sambirano</li>
                <li><strong>Valrhona</strong> - Grand cru Manjari 64%</li>
                <li><strong>Bonnat</strong> - Madagascar Sambirano 75%</li>
                <li><strong>Chocolat Madagascar (Robert)</strong> - Artisan local multi-primé</li>
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
                Conseils de Dégustation
              </h2>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                Pour apprécier pleinement un chocolat de Madagascar :
              </p>

              <ul style={{
                lineHeight: '2',
                marginBottom: '1.5rem',
                marginLeft: '2rem',
                color: '#1A1A1A'
              }}>
                <li>Privilégiez une <strong>température de 18-20°C</strong></li>
                <li>Laissez fondre lentement en bouche pour révéler l'acidité</li>
                <li>Accordez avec des <strong>vins blancs secs</strong> ou des <strong>champagnes brut</strong></li>
                <li>Mariez avec des <strong>fruits rouges frais</strong> ou des <strong>fromages de chèvre</strong></li>
                <li>Les pourcentages 65-75% révèlent le meilleur du terroir</li>
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
                Impact Social et Environnemental
              </h2>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                Madagascar développe activement le <strong>commerce équitable</strong> et l'<strong>agriculture biologique</strong>. De nombreux producteurs sont certifiés <strong>Fair Trade, Organic et Rainforest Alliance</strong>, garantissant des pratiques durables et une rémunération juste des producteurs.
              </p>

              <p style={{ lineHeight: '1.8', marginBottom: '1.5rem', color: '#1A1A1A' }}>
                La filière bean-to-bar malgache, en plein essor, permet de créer de la valeur ajoutée sur place, bénéficiant directement aux communautés locales.
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
                Trouvez Votre Chocolat Malgache Idéal
              </h2>
              <p style={{
                fontSize: '1.125rem',
                marginBottom: '2rem',
                opacity: 0.95
              }}>
                Notre Sommelier IA vous recommande les meilleurs chocolats de Madagascar selon vos préférences.
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

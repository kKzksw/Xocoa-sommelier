import Head from 'next/head'

const SEO_DATA = {
  title: 'XOCOA - AI Chocolate Sommelier | 2000+ Premium Chocolates',
  description: 'Discover your ideal chocolate among 2000+ premium references. AI-powered personalized recommendations. Bean-to-bar, single origin, grand crus from Madagascar, Ecuador, Venezuela.',
  keywords: 'premium chocolate, bean to bar, artisan chocolate, chocolate sommelier, grand crus, single origin, Madagascar chocolate, Ecuador chocolate, ICA awards, dark chocolate',
  ogTitle: 'XOCOA - Your Personal Chocolate Sommelier',
  ogDescription: '2000+ premium chocolates analyzed. Artificial intelligence to find your perfect chocolate in a few clicks.',
  url: 'https://xocoa.co',
  locale: 'en_US'
}

export default function SEOHead({
  title: customTitle,
  description: customDescription,
  ogImage = 'https://xocoa.co/og-image.jpg'
}) {
  const title = customTitle || SEO_DATA.title
  const description = customDescription || SEO_DATA.description

  return (
    <Head>
      {/* Primary Meta Tags */}
      <title>{title}</title>
      <meta name="title" content={title} />
      <meta name="description" content={description} />
      <meta name="keywords" content={SEO_DATA.keywords} />

      {/* Viewport & Mobile */}
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <meta name="theme-color" content="#1a1a1a" />

      {/* Language & Locale */}
      <meta httpEquiv="content-language" content="en" />
      <link rel="canonical" href={SEO_DATA.url} />

      {/* Open Graph / Facebook */}
      <meta property="og:type" content="website" />
      <meta property="og:url" content={SEO_DATA.url} />
      <meta property="og:title" content={customTitle || SEO_DATA.ogTitle} />
      <meta property="og:description" content={description} />
      <meta property="og:image" content={ogImage} />
      <meta property="og:locale" content={SEO_DATA.locale} />
      <meta property="og:site_name" content="XOCOA" />

      {/* Twitter */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:url" content={SEO_DATA.url} />
      <meta name="twitter:title" content={customTitle || SEO_DATA.ogTitle} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={ogImage} />

      {/* Favicon */}
      <link rel="icon" href="/Xocoa-icon.ico" />

      {/* Schema.org JSON-LD */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'WebApplication',
            name: 'XOCOA',
            description: description,
            url: SEO_DATA.url,
            applicationCategory: 'FoodApplication',
            offers: {
              '@type': 'Offer',
              price: '0',
              priceCurrency: 'USD'
            },
            provider: {
              '@type': 'Organization',
              name: 'XOCOA',
              url: SEO_DATA.url
            }
          })
        }}
      />
    </Head>
  )
}
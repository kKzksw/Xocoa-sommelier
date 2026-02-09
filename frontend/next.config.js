/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false, // Désactiver pour faster dev
  // Conditionally set output for production builds
  output: 'standalone',
  trailingSlash: true,
  images: {
    // Optimize images only in production for smaller payloads
    unoptimized: process.env.NODE_ENV === 'development',
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'xocoa-sommelier.com',
      },
    ],
    formats: ['image/avif', 'image/webp'],
  },
  env: {
    OPENAI_API_KEY: process.env.OPENAI_API_KEY,
  },
  // Optimisations pour développement plus rapide
  experimental: {
    optimizeCss: false,
    optimizePackageImports: ['date-fns'],
  },
  webpack: (config, { dev, isServer }) => {
    if (dev) {
      // Désactiver le cache en dev pour éviter les problèmes
      config.cache = false
    }
    return config
  },
}

module.exports = nextConfig

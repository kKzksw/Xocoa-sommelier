/**
 * Data Obfuscation Utilities
 * Protège les données sensibles contre le scraping en ajoutant des variations légères
 */

/**
 * Génère une variation aléatoire basée sur l'IP pour maintenir la cohérence par session
 * @param {string} ip - Adresse IP du client
 * @param {string} seed - Seed pour la variation (ex: chocolate id)
 * @returns {number} - Nombre entre -1 et 1
 */
function getSessionVariation(ip, seed) {
  // Simple hash function basée sur IP + seed
  const str = `${ip}-${seed}`
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i)
    hash = hash & hash
  }
  // Normalize to -1 to 1
  return (hash % 100) / 100
}

/**
 * Obfusque le prix en ajoutant une variation légère basée sur l'IP
 * @param {number} originalPrice - Prix original
 * @param {string} chocolateId - ID du chocolat pour le seed
 * @param {string} clientIp - IP du client
 * @returns {number} - Prix avec variation légère (-2% à +2%)
 */
export function obfuscatePrice(originalPrice, chocolateId, clientIp = 'default') {
  if (!originalPrice || isNaN(originalPrice)) return originalPrice

  const variation = getSessionVariation(clientIp, chocolateId)
  // Variation de ±2%
  const variationPercent = variation * 0.02
  const obfuscatedPrice = originalPrice * (1 + variationPercent)

  // Arrondir à 2 décimales
  return Math.round(obfuscatedPrice * 100) / 100
}

/**
 * Obfusque l'avis expert en ajoutant/modifiant des mots subtils
 * @param {string} originalReview - Avis original
 * @param {string} chocolateId - ID du chocolat
 * @param {string} clientIp - IP du client
 * @returns {string} - Avis légèrement modifié
 */
export function obfuscateExpertReview(originalReview, chocolateId, clientIp = 'default') {
  if (!originalReview || originalReview.length === 0) return originalReview

  const variation = getSessionVariation(clientIp, chocolateId)

  // Synonymes pour variation légère
  const synonyms = {
    'excellent': ['remarquable', 'exceptionnel', 'excellent', 'superbe'],
    'good': ['bon', 'agréable', 'plaisant', 'satisfaisant'],
    'intense': ['intense', 'puissant', 'prononcé', 'marqué'],
    'smooth': ['lisse', 'velouté', 'onctueux', 'soyeux'],
    'creamy': ['crémeux', 'onctueux', 'velouté', 'moelleux']
  }

  let modifiedReview = originalReview

  // Sélectionne des synonymes basés sur la variation IP
  Object.keys(synonyms).forEach(word => {
    if (modifiedReview.toLowerCase().includes(word)) {
      const synonymList = synonyms[word]
      const index = Math.abs(Math.floor(variation * synonymList.length))
      const synonym = synonymList[index % synonymList.length]

      // Remplace seulement une occurrence pour rester subtil
      modifiedReview = modifiedReview.replace(
        new RegExp(word, 'i'),
        synonym
      )
    }
  })

  return modifiedReview
}

/**
 * Obfusque les notes de dégustation de manière similaire
 * @param {string} originalNotes - Notes originales
 * @param {string} chocolateId - ID du chocolat
 * @param {string} clientIp - IP du client
 * @returns {string} - Notes légèrement modifiées
 */
export function obfuscateTastingNotes(originalNotes, chocolateId, clientIp = 'default') {
  if (!originalNotes || originalNotes.length === 0) return originalNotes

  const variation = getSessionVariation(clientIp, chocolateId)

  // Synonymes de saveurs
  const flavorSynonyms = {
    'fruity': ['fruité', 'aux notes de fruits', 'fruitées', 'avec des arômes fruités'],
    'nutty': ['noisette', 'aux notes de noix', 'avec des arômes de fruits secs'],
    'floral': ['floral', 'aux notes florales', 'fleuri', 'avec des arômes floraux'],
    'spicy': ['épicé', 'aux notes épicées', 'avec des épices', 'relevé']
  }

  let modifiedNotes = originalNotes

  Object.keys(flavorSynonyms).forEach(flavor => {
    if (modifiedNotes.toLowerCase().includes(flavor)) {
      const synonymList = flavorSynonyms[flavor]
      const index = Math.abs(Math.floor(variation * synonymList.length))
      const synonym = synonymList[index % synonymList.length]

      modifiedNotes = modifiedNotes.replace(
        new RegExp(flavor, 'i'),
        synonym
      )
    }
  })

  return modifiedNotes
}

/**
 * Applique l'obfuscation complète à un chocolat
 * @param {object} chocolate - Objet chocolat
 * @param {string} clientIp - IP du client
 * @returns {object} - Chocolat obfusqué
 */
export function obfuscateChocolate(chocolate, clientIp = 'default') {
  if (!chocolate) return chocolate

  return {
    ...chocolate,
    price_retail: obfuscatePrice(chocolate.price_retail, chocolate.id, clientIp),
    expert_review: obfuscateExpertReview(chocolate.expert_review, chocolate.id, clientIp),
    tasting_notes: obfuscateTastingNotes(chocolate.tasting_notes, chocolate.id, clientIp)
  }
}

/**
 * Applique l'obfuscation à un array de chocolats
 * @param {array} chocolates - Array de chocolats
 * @param {string} clientIp - IP du client
 * @returns {array} - Chocolats obfusqués
 */
export function obfuscateChocolates(chocolates, clientIp = 'default') {
  if (!Array.isArray(chocolates)) return chocolates

  return chocolates.map(chocolate => obfuscateChocolate(chocolate, clientIp))
}

/**
 * Data Obfuscation Utilities (CommonJS version for Netlify)
 * Protège les données sensibles contre le scraping
 */

function getSessionVariation(ip, seed) {
  const str = `${ip}-${seed}`
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i)
    hash = hash & hash
  }
  return (hash % 100) / 100
}

function obfuscatePrice(originalPrice, chocolateId, clientIp = 'default') {
  if (!originalPrice || isNaN(originalPrice)) return originalPrice

  const variation = getSessionVariation(clientIp, chocolateId)
  const variationPercent = variation * 0.02
  const obfuscatedPrice = originalPrice * (1 + variationPercent)

  return Math.round(obfuscatedPrice * 100) / 100
}

function obfuscateExpertReview(originalReview, chocolateId, clientIp = 'default') {
  if (!originalReview || originalReview.length === 0) return originalReview

  const variation = getSessionVariation(clientIp, chocolateId)

  const synonyms = {
    'excellent': ['remarquable', 'exceptionnel', 'excellent', 'superbe'],
    'good': ['bon', 'agréable', 'plaisant', 'satisfaisant'],
    'intense': ['intense', 'puissant', 'prononcé', 'marqué'],
    'smooth': ['lisse', 'velouté', 'onctueux', 'soyeux'],
    'creamy': ['crémeux', 'onctueux', 'velouté', 'moelleux']
  }

  let modifiedReview = originalReview

  Object.keys(synonyms).forEach(word => {
    if (modifiedReview.toLowerCase().includes(word)) {
      const synonymList = synonyms[word]
      const index = Math.abs(Math.floor(variation * synonymList.length))
      const synonym = synonymList[index % synonymList.length]
      modifiedReview = modifiedReview.replace(new RegExp(word, 'i'), synonym)
    }
  })

  return modifiedReview
}

function obfuscateTastingNotes(originalNotes, chocolateId, clientIp = 'default') {
  if (!originalNotes || originalNotes.length === 0) return originalNotes

  const variation = getSessionVariation(clientIp, chocolateId)

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
      modifiedNotes = modifiedNotes.replace(new RegExp(flavor, 'i'), synonym)
    }
  })

  return modifiedNotes
}

function obfuscateChocolate(chocolate, clientIp = 'default') {
  if (!chocolate) return chocolate

  return {
    ...chocolate,
    price_retail: obfuscatePrice(chocolate.price_retail, chocolate.id, clientIp),
    expert_review: obfuscateExpertReview(chocolate.expert_review, chocolate.id, clientIp),
    tasting_notes: obfuscateTastingNotes(chocolate.tasting_notes, chocolate.id, clientIp)
  }
}

function obfuscateChocolates(chocolates, clientIp = 'default') {
  if (!Array.isArray(chocolates)) return chocolates
  return chocolates.map(chocolate => obfuscateChocolate(chocolate, clientIp))
}

module.exports = {
  obfuscatePrice,
  obfuscateExpertReview,
  obfuscateTastingNotes,
  obfuscateChocolate,
  obfuscateChocolates
}

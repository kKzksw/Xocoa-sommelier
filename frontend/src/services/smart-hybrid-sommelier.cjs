const OpenAI = require('openai')
const fs = require('fs')
const path = require('path')

class SmartHybridSommelier {
  constructor(skipDataLoading = false) {
    this.chocolates = []
    this.filters = {}
    if (!skipDataLoading) {
      this.loadData()
    }

    if (process.env.OPEN_AI_KEY) {
      this.openai = new OpenAI({
        apiKey: process.env.OPEN_AI_KEY
      })
      this.useOpenAI = true
    } else {
      this.useOpenAI = false
      throw new Error('❌ OpenAI API key required for Smart Hybrid Sommelier')
    }
  }

  loadData(language = 'en') {
    try {
      // Determine which chocolate file to load based on language
      const chocolateFile = `chocolates_${language}.json`

      // Try data/ first (for local dev), then public/ (for Netlify)
      let chocolatesPath = path.join(process.cwd(), 'data', chocolateFile)
      let filtersPath = path.join(process.cwd(), 'data', 'filters.json')

      if (!fs.existsSync(chocolatesPath)) {
        chocolatesPath = path.join(process.cwd(), 'public', chocolateFile)
        filtersPath = path.join(process.cwd(), 'public', 'filters.json')
      }

      this.chocolates = JSON.parse(fs.readFileSync(chocolatesPath, 'utf8'))
      this.filters = JSON.parse(fs.readFileSync(filtersPath, 'utf8'))

      console.log(`✅ Loaded ${this.chocolates.length} chocolates (${language}) for Smart Hybrid Sommelier`)
    } catch (error) {
      console.error(`❌ Error loading chocolate data for language ${language}:`, error)
      throw error
    }
  }

  // Helper to extract filter values ACCORDING TO CURRENT LANGUAGE
  getFilterKeys(filterName) {
    const filter = this.filters[filterName]
    if (!filter) return []
    // If it's an array, return as is
    if (Array.isArray(filter)) return filter
    // If it's an object (multilingual), return values for current language
    if (typeof filter === 'object') {
      const lang = this.currentLanguage || 'en'

      if (lang === 'en') {
        // EN: return English keys from filters.json (mushroom, gift, creamy, Belgium)
        return Object.keys(filter)
      } else if (lang === 'fr') {
        // FR: return .fr values from filters.json (champignon, cadeau, crémeux, Belgique)
        return Object.entries(filter).map(([key, translations]) => {
          return translations?.fr || key
        }).filter(Boolean)
      } else if (lang === 'es') {
        // ES: return .es values from filters.json (hongo, regalo, cremoso, Bélgica)
        return Object.entries(filter).map(([key, translations]) => {
          return translations?.es || key
        }).filter(Boolean)
      }
    }
    return []
  }

  // Resolve synonyms in the CURRENT LANGUAGE
  // FR: "bio" → "Biologique" (FR value), EN: "organic" → "Organic" (EN key), ES: "bio" → "Orgánico" (ES value)
  resolveSynonym(filterName, userValue, language = 'fr') {
    const filter = this.filters[filterName]
    if (!filter || typeof filter !== 'object') return userValue

    const userValueLower = userValue.toLowerCase().trim()

    // Search through all filter entries
    for (const [canonicalKey, translations] of Object.entries(filter)) {
      if (typeof translations !== 'object') continue

      // Check if synonyms exist for this language
      if (translations.synonyms && translations.synonyms[language]) {
        const synonyms = translations.synonyms[language]
        // Check if user value matches any synonym
        if (synonyms.some(syn => syn.toLowerCase() === userValueLower)) {
          // Return value in current language
          if (language === 'en') {
            return canonicalKey // EN: return English key
          } else if (language === 'fr') {
            return translations.fr || canonicalKey // FR: return French value
          } else if (language === 'es') {
            return translations.es || canonicalKey // ES: return Spanish value
          }
        }
      }

      // Also check if it matches the translated value itself
      if (translations[language] && translations[language].toLowerCase() === userValueLower) {
        // Already matches, return it as-is
        if (language === 'en') {
          return canonicalKey
        } else if (language === 'fr') {
          return translations.fr || canonicalKey
        } else if (language === 'es') {
          return translations.es || canonicalKey
        }
      }

      // Check if it matches the canonical key itself (EN case)
      if (language === 'en' && canonicalKey.toLowerCase() === userValueLower) {
        return canonicalKey
      }
    }

    // No match found, return original value
    return userValue
  }

  async processUserMessage({ message, currentPreferences, conversationHistory, language = 'fr' }) {
    try {
      // Store language for synonym resolution
      this.currentLanguage = language

      // DEBUG: Log the language being used
      console.log(`🌍 [LANGUAGE] Processing message in: ${language}`)

      // IMPORTANT: Reload data with correct language if language changed
      if (!this.chocolates.length || this.loadedLanguage !== language) {
        this.loadData(language)
        this.loadedLanguage = language
      }

      // ÉTAPE 1: OpenAI analyse et extrait les critères
      const extractedCriteria = await this.extractCriteriaWithAI(message, currentPreferences, conversationHistory)

      // ÉTAPE 2: Code local fait le filtrage rapide
      const filteredChocolates = this.filterChocolates(extractedCriteria)
      const count = filteredChocolates.length

      // ÉTAPE 3: OpenAI décide de la suite selon le workflow
      return await this.makeDecisionWithAI(message, extractedCriteria, filteredChocolates, count, conversationHistory)

    } catch (error) {
      console.error('Smart Hybrid processing error:', error)
      throw new Error(`Processing failed: ${error.message}`)
    }
  }

  // ÉTAPE 1: OpenAI extrait les critères avec validation stricte
  async extractCriteriaWithAI(message, currentPreferences, conversationHistory) {
    // Build language-specific instruction
    const lang = this.currentLanguage || 'fr'
    let languageInstruction = ''

    if (lang === 'fr') {
      languageInstruction = `🇫🇷 UTILISATEUR FRANCOPHONE: Il parle FRANÇAIS
- Les valeurs de filtres ci-dessous sont en FRANÇAIS
- Tu dois retourner les valeurs EXACTEMENT comme elles apparaissent dans les listes
- NE traduis PAS vers l'anglais!`
    } else if (lang === 'en') {
      languageInstruction = `🇬🇧 ENGLISH USER: They speak ENGLISH
- The filter values below are in ENGLISH
- You must return values EXACTLY as they appear in the lists
- Do NOT translate!`
    } else if (lang === 'es') {
      languageInstruction = `🇪🇸 USUARIO HISPANOHABLANTE: Habla ESPAÑOL
- Los valores de filtros abajo están en ESPAÑOL
- Debes devolver los valores EXACTAMENTE como aparecen en las listas
- ¡NO traduzcas!`
    }

    const completion = await this.openai.chat.completions.create({
      model: 'gpt-4o',
      messages: [
        {
          role: 'system',
          content: `Tu es un expert sommelier qui comprend les demandes chocolat naturellement.

${languageInstruction}

MISSION: Comprends le message utilisateur et extrais les critères de recherche intelligemment.

DONNÉES DISPONIBLES (dynamiques depuis filters.json):

ORIGINES & FABRICATION:
- Pays d'origine fèves: ${this.getFilterKeys('origin_countrys').join(', ')}
- Régions d'origine: ${this.getFilterKeys('origin_regions').slice(0, 30).join(', ')}... (${this.getFilterKeys('origin_regions').length} total)
- Pays fabricants: ${this.getFilterKeys('maker_countrys').join(', ')}
- Variétés de fèves: ${this.getFilterKeys('bean_varietys').join(', ')}

FORMATS & TYPES:
- Types: ${this.getFilterKeys('types').join(', ')}
- Niveaux craft: ${this.getFilterKeys('production_craft_levels').join(', ')}

TEXTURE & FINITION:
- Textures: ${this.getFilterKeys('texture_mouthfeels').join(', ')}
- Longueur finish: ${this.getFilterKeys('finish_lengths').join(', ')}
- Caractère finish: ${this.getFilterKeys('finish_characters').join(', ')}

SAVEURS (${this.getFilterKeys('flavors').length} disponibles):
${this.getFilterKeys('flavors').slice(0, 50).join(', ')}...

ACCORDS:
- Vins: ${this.getFilterKeys('pairings_wine').join(', ')}
- Spiritueux: ${this.getFilterKeys('pairings_spirits').join(', ')}
- Cafés: ${this.getFilterKeys('pairings_coffee').join(', ')}
- Thés: ${this.getFilterKeys('pairings_tea').join(', ')}
- Fromages: ${this.getFilterKeys('pairings_cheese').join(', ')}
- Fruits: ${this.getFilterKeys('pairings_fruits').join(', ')}
- Noix: ${this.getFilterKeys('pairings_nuts').join(', ')}

CERTIFICATIONS & DIETARY:
- Certifications: ${this.getFilterKeys('sustainability_certificationss').join(', ')}
- Régimes: ${this.getFilterKeys('dietarys').join(', ')}

AWARDS:
${this.getFilterKeys('awardss').join(', ')}

OCCASIONS:
${this.getFilterKeys('serving_occasions').join(', ')}

🎯 CONTEXTE MARQUES GRAND PUBLIC:
Si l'utilisateur mentionne **Nutella**, **Ferrero**, **Snickers**, **Kinder**, **Milka**, **Toblerone**:
→ Ce sont des chocolats industriels doux, onctueux, souvent avec noisettes/caramel
→ L'utilisateur cherche probablement des chocolats artisanaux avec profils similaires (douceur, onctuosité, noisettes)
→ Choisis intelligemment parmi les 485 saveurs et textures disponibles ci-dessus
→ **IMPORTANT**: Si tu trouves peu ou zéro résultats avec plusieurs critères, essaie avec SEULEMENT les saveurs (flavor_keywords)
→ Message suggéré: "Je comprends que vous aimez ces saveurs ! Je vais vous recommander des chocolats artisanaux avec de belles notes de noisette."

TON RÔLE:
- Pour TOUS les champs de filtres (occasions, textures, finish, saveurs, etc.): retourne la valeur EXACTEMENT comme elle apparaît dans la liste ci-dessus
- L'utilisateur peut utiliser des synonymes (c'est normal), tu cherches la correspondance dans les listes et retournes la valeur officielle
- Exception UNIQUEMENT pour pays/régions géographiques: utilise toujours le nom anglais standard (Peru, Ecuador, Madagascar, Belgium)
- Comprends "awards", "prix", "récompense", "premio" → utilise champ awards
- Comprends "années 2020", "year 2021", "año 2022" → utilise awards_year
- Comprends TOUTES demandes de prix/tri/classement (voir exemples ci-dessous)
- CONSERVE TOUJOURS les préférences actuelles et AJOUTE les nouvelles

RETOUR JSON:
{
  "criteria": {
    "origin_country": "pays_traduit_ou_null",
    "origin_region": "région_ou_null",
    "maker_country": "pays_traduit_ou_null",
    "cocoa_percentage_min": number_or_null,
    "cocoa_percentage_max": number_or_null,
    "flavor_keywords": ["valeurs_exactes_liste_saveurs"],
    "price_min": number_or_null,
    "price_max": number_or_null,
    "type": "type_ou_null",
    "bean_variety": "variété_ou_null",
    "texture": "texture_ou_null",
    "finish_length": "longueur_ou_null",
    "finish_character": "caractère_ou_null",
    "wine_pairing": "cépage_ou_null",
    "spirit_pairing": "spiritueux_ou_null",
    "coffee_pairing": "café_ou_null",
    "tea_pairing": "thé_ou_null",
    "cheese_pairing": "fromage_ou_null",
    "fruit_pairing": "fruit_ou_null",
    "nut_pairing": "noix_ou_null",
    "certification": "certification_ou_null",
    "dietary": "régime_ou_null",
    "craft_level": "niveau_craft_ou_null",
    "occasion": "occasion_ou_null",
    "awards": "award_recherché_ou_null",
    "awards_year": "année_award_ou_null"
  },
  "sort_by": "price_desc/price_asc/rating_desc/cocoa_desc/null",
  "limit": number_or_null,
  "unrecognized_terms": ["seulement_termes_vraiment_incompris"],
  "confidence": "high/medium/low"
}

EXEMPLES DE COMPRÉHENSION:
- "les 3 plus chers" → sort_by: "price_desc", limit: 3
- "plus de 18 euros" → price_min: 18
- "moins de 15€" → price_max: 15
- "les meilleurs" → sort_by: "rating_desc"
- "le plus intense en cacao" → sort_by: "cocoa_desc", limit: 1`
        },
        {
          role: 'user',
          content: `PRÉFÉRENCES ACTUELLES: ${JSON.stringify(currentPreferences)}
NOUVEAU MESSAGE: "${message}"`
        }
      ],
      temperature: 0.3,
      max_tokens: 300
    })

    // Parse et merge avec préférences actuelles
    let result
    try {
      const content = completion.choices[0].message.content
      const jsonMatch = content.match(/\{[\s\S]*\}/)
      result = jsonMatch ? JSON.parse(jsonMatch[0]) : { criteria: {}, confidence: "low" }
    } catch (e) {
      result = { criteria: {}, confidence: "low" }
    }

    // Merge avec préférences existantes
    const mergedCriteria = { ...currentPreferences, ...result.criteria }

    // 📊 User tracking log (kept for database valuation)
    console.log('📊 USER QUERY:', message)
    console.log('📊 EXTRACTED CRITERIA:', JSON.stringify(result.criteria, null, 2))

    return {
      ...result,
      criteria: mergedCriteria
    }
  }

  // ÉTAPE 2: Filtrage local rapide et précis avec accords
  filterChocolates(extractedCriteria) {
    const criteria = extractedCriteria.criteria
    let filtered = [...this.chocolates]

    // Filtrage par origine
    if (criteria.origin_country) {
      filtered = filtered.filter(c =>
        c.origin_country && c.origin_country.toLowerCase().includes(criteria.origin_country.toLowerCase())
      )
    }

    // Filtrage par chocolatier
    if (criteria.maker_country) {
      filtered = filtered.filter(c =>
        c.maker_country && c.maker_country.toLowerCase().includes(criteria.maker_country.toLowerCase())
      )
    }

    // Filtrage par pourcentage cacao
    if (criteria.cocoa_percentage_min) {
      filtered = filtered.filter(c =>
        c.cocoa_percentage && c.cocoa_percentage >= criteria.cocoa_percentage_min
      )
    }
    if (criteria.cocoa_percentage_max) {
      filtered = filtered.filter(c =>
        c.cocoa_percentage && c.cocoa_percentage <= criteria.cocoa_percentage_max
      )
    }

    // Filtrage par saveurs - Chercher dans TOUS les flavor_notes
    if (criteria.flavor_keywords && criteria.flavor_keywords.length > 0) {
      filtered = filtered.filter(c => {
        const allFlavors = [
          c.flavor_notes_primary || '',
          c.flavor_notes_secondary || '',
          c.flavor_notes_tertiary || '',
          c.flavor_notes_additional || '',
          c.finish_aftertaste || ''
        ].join(' ').toLowerCase()

        return criteria.flavor_keywords.some(keyword => {
          const keywordLower = keyword.toLowerCase()
          // Try exact match first
          if (allFlavors.includes(keywordLower)) return true
          // Try singular form (remove 's' at end) - handles Noisettes → noisette
          if (keywordLower.endsWith('s')) {
            const singular = keywordLower.slice(0, -1)
            if (allFlavors.includes(singular)) return true
          }
          // Try plural form (add 's') - handles noisette → noisettes
          const plural = keywordLower + 's'
          return allFlavors.includes(plural)
        })
      })
    }

    // Filtrage par région d'origine
    if (criteria.origin_region) {
      filtered = filtered.filter(c =>
        c.origin_region && c.origin_region.toLowerCase().includes(criteria.origin_region.toLowerCase())
      )
    }

    // Filtrage par texture
    if (criteria.texture) {
      filtered = filtered.filter(c =>
        c.texture_mouthfeel && c.texture_mouthfeel.toLowerCase().includes(criteria.texture.toLowerCase())
      )
    }

    // Filtrage par longueur de finish
    if (criteria.finish_length) {
      filtered = filtered.filter(c =>
        c.finish_length && c.finish_length.toLowerCase().includes(criteria.finish_length.toLowerCase())
      )
    }

    // Filtrage par caractère de finish
    if (criteria.finish_character) {
      filtered = filtered.filter(c =>
        c.finish_character && c.finish_character.toLowerCase().includes(criteria.finish_character.toLowerCase())
      )
    }

    // Filtrage par niveau craft
    if (criteria.craft_level) {
      filtered = filtered.filter(c =>
        c.production_craft_level && c.production_craft_level.toLowerCase().includes(criteria.craft_level.toLowerCase())
      )
    }

    // Filtrage par certification avec résolution de synonymes
    if (criteria.certification) {
      // Resolve synonym to canonical English value
      const canonicalCert = this.resolveSynonym('sustainability_certificationss', criteria.certification, this.currentLanguage || 'fr')

      filtered = filtered.filter(c => {
        if (!c.sustainability_certifications) return false
        const certLower = c.sustainability_certifications.toLowerCase()
        return certLower.includes(canonicalCert.toLowerCase())
      })
    }

    // Filtrage par régime alimentaire
    if (criteria.dietary) {
      filtered = filtered.filter(c =>
        c.dietary && c.dietary.toLowerCase().includes(criteria.dietary.toLowerCase())
      )
    }

    // Filtrage par occasion
    if (criteria.occasion) {
      filtered = filtered.filter(c =>
        c.serving_occasion && c.serving_occasion.toLowerCase().includes(criteria.occasion.toLowerCase())
      )
    }

    // ACCORDS - Filtrage par vins
    if (criteria.wine_pairing) {
      filtered = filtered.filter(c =>
        c.pairings_wine && c.pairings_wine.toLowerCase().includes(criteria.wine_pairing.toLowerCase())
      )
    }

    // Filtrage par spiritueux
    if (criteria.spirit_pairing) {
      filtered = filtered.filter(c =>
        c.pairings_spirits && c.pairings_spirits.toLowerCase().includes(criteria.spirit_pairing.toLowerCase())
      )
    }

    // Filtrage par café
    if (criteria.coffee_pairing) {
      filtered = filtered.filter(c =>
        c.pairings_coffee && c.pairings_coffee.toLowerCase().includes(criteria.coffee_pairing.toLowerCase())
      )
    }

    // Filtrage par thé
    if (criteria.tea_pairing) {
      filtered = filtered.filter(c =>
        c.pairings_tea && c.pairings_tea.toLowerCase().includes(criteria.tea_pairing.toLowerCase())
      )
    }

    // Filtrage par fromage
    if (criteria.cheese_pairing) {
      filtered = filtered.filter(c =>
        c.pairings_cheese && c.pairings_cheese.toLowerCase().includes(criteria.cheese_pairing.toLowerCase())
      )
    }

    // Filtrage par fruits
    if (criteria.fruit_pairing) {
      filtered = filtered.filter(c =>
        c.pairings_fruits && c.pairings_fruits.toLowerCase().includes(criteria.fruit_pairing.toLowerCase())
      )
    }

    // Filtrage par noix
    if (criteria.nut_pairing) {
      filtered = filtered.filter(c =>
        c.pairings_nuts && c.pairings_nuts.toLowerCase().includes(criteria.nut_pairing.toLowerCase())
      )
    }

    // Filtrage par prix
    if (criteria.price_max) {
      filtered = filtered.filter(c =>
        c.price_retail && parseFloat(c.price_retail) <= criteria.price_max
      )
    }

    // Filtrage par type
    if (criteria.type) {
      filtered = filtered.filter(c =>
        c.type && c.type.toLowerCase().includes(criteria.type.toLowerCase())
      )
    }

    // Filtrage par variété de fève
    if (criteria.bean_variety) {
      filtered = filtered.filter(c =>
        c.bean_variety && c.bean_variety.toLowerCase().includes(criteria.bean_variety.toLowerCase())
      )
    }

    // Filtrage par awards
    if (criteria.awards) {
      filtered = filtered.filter(c =>
        c.awards && c.awards.toLowerCase().includes(criteria.awards.toLowerCase())
      )
    }

    // Filtrage par année d'award
    if (criteria.awards_year) {
      filtered = filtered.filter(c =>
        c.awards_year && c.awards_year.includes(criteria.awards_year)
      )
    }

    // Filtrage par prix minimum
    if (criteria.price_min) {
      filtered = filtered.filter(c =>
        c.price_retail && parseFloat(c.price_retail) >= criteria.price_min
      )
    }

    // 📊 User tracking log (kept for database valuation)
    console.log('📊 FILTER RESULTS:', filtered.length, 'chocolates found')

    // Tri selon demande utilisateur
    const sortBy = extractedCriteria.sort_by
    if (sortBy === 'price_desc') {
      filtered.sort((a, b) => (parseFloat(b.price_retail) || 0) - (parseFloat(a.price_retail) || 0))
    } else if (sortBy === 'price_asc') {
      filtered.sort((a, b) => (parseFloat(a.price_retail) || 0) - (parseFloat(b.price_retail) || 0))
    } else if (sortBy === 'cocoa_desc') {
      filtered.sort((a, b) => (parseFloat(b.cocoa_percentage) || 0) - (parseFloat(a.cocoa_percentage) || 0))
    } else if (sortBy === 'rating_desc') {
      filtered.sort((a, b) => (parseFloat(b.rating) || 0) - (parseFloat(a.rating) || 0))
    } else {
      // Tri par défaut: rating décroissant
      filtered.sort((a, b) => (parseFloat(b.rating) || 0) - (parseFloat(a.rating) || 0))
    }

    // Limite de résultats si demandée
    if (extractedCriteria.limit && extractedCriteria.limit > 0) {
      filtered = filtered.slice(0, extractedCriteria.limit)
    }

    return filtered
  }

  // ÉTAPE 3: OpenAI décide de la suite selon le workflow
  async makeDecisionWithAI(originalMessage, extractedCriteria, filteredChocolates, count, conversationHistory) {
    // Analyser les options disponibles dans les chocolats filtrés
    const availableOptions = this.analyzeAvailableOptions(filteredChocolates)

    // Build language-specific instruction for response
    const lang = this.currentLanguage || 'fr'

    // DEBUG: Log which language prompt will be used
    console.log(`🌍 [GPT PROMPT] Using ${lang} system prompt for GPT-3.5`)

    // Build complete system prompt in user's language
    let systemPrompt = ''

    if (lang === 'en') {
      systemPrompt = `🇬🇧 RESPOND IN ENGLISH - All your responses must be in English with a warm and professional tone.

You are the XOCOA sommelier applying the INTELLIGENT WORKFLOW with strict validation.

${extractedCriteria.unrecognized_terms && extractedCriteria.unrecognized_terms.length > 0 ?
`UNRECOGNIZED TERMS: ${extractedCriteria.unrecognized_terms.join(', ')}
→ You MUST mention these terms and suggest available alternatives` : ''}

WORKFLOW:
- If unrecognized terms → Explain + suggest alternatives
- If 0 chocolates → Suggest relaxing a criterion
- If 1-6 chocolates → FINAL RECOMMENDATIONS
- If 7+ chocolates → ASK FOR ADDITIONAL CRITERION

VALIDATED CRITERIA: ${JSON.stringify(extractedCriteria.criteria)}
RESULTS: ${count} chocolates found

${count > 6 ? `AVAILABLE OPTIONS IN THE ${count} CHOCOLATES:
- Origins: ${availableOptions.origins.slice(0, 8).join(', ')}
- Prices: ${availableOptions.price_range}
- Percentages: ${availableOptions.cocoa_range}
- Types: ${availableOptions.types.slice(0, 5).join(', ')}
- Available flavors: ${availableOptions.available_flavors?.slice(0, 8).join(', ') || 'none'}
- Available wines: ${availableOptions.wine_pairings?.slice(0, 6).join(', ') || 'none'}
- Available spirits: ${availableOptions.spirit_pairings?.slice(0, 6).join(', ') || 'none'}` : ''}

ALTERNATIVES FOR UNRECOGNIZED TERMS:
- For wines: our VARIETALS are ${this.filters.wine_pairings?.slice(0, 10).join(', ')}
- For flavors: ${count > 6 ? `in these ${count} chocolates we have ${availableOptions.available_flavors?.slice(0, 6).join(', ') || 'none'}` : `our keywords are in English (apricot, cherry, vanilla...)`}
- For origins: ${this.filters.origin_countries?.slice(0, 10).join(', ')}

JSON RESPONSE:
{
  "message": "your conversational response in English",
  "preferences": ${JSON.stringify(extractedCriteria.criteria)},
  "recommendations": ${count <= 6 ? "array of chocolates" : "[]"},
  "debug_count": ${count}
}`
    } else if (lang === 'es') {
      systemPrompt = `🇪🇸 RESPONDER EN ESPAÑOL - Todas tus respuestas deben ser en español con un tono cálido y profesional.

Eres el sommelier de XOCOA que aplica el FLUJO DE TRABAJO INTELIGENTE con validación estricta.

${extractedCriteria.unrecognized_terms && extractedCriteria.unrecognized_terms.length > 0 ?
`TÉRMINOS NO RECONOCIDOS: ${extractedCriteria.unrecognized_terms.join(', ')}
→ DEBES mencionar estos términos y sugerir alternativas disponibles` : ''}

FLUJO DE TRABAJO:
- Si términos no reconocidos → Explicar + sugerir alternativas
- Si 0 chocolates → Sugerir relajar un criterio
- Si 1-6 chocolates → RECOMENDACIONES FINALES
- Si 7+ chocolates → PEDIR CRITERIO ADICIONAL

CRITERIOS VALIDADOS: ${JSON.stringify(extractedCriteria.criteria)}
RESULTADOS: ${count} chocolates encontrados

${count > 6 ? `OPCIONES DISPONIBLES EN LOS ${count} CHOCOLATES:
- Orígenes: ${availableOptions.origins.slice(0, 8).join(', ')}
- Precios: ${availableOptions.price_range}
- Porcentajes: ${availableOptions.cocoa_range}
- Tipos: ${availableOptions.types.slice(0, 5).join(', ')}
- Sabores disponibles: ${availableOptions.available_flavors?.slice(0, 8).join(', ') || 'ninguno'}
- Vinos disponibles: ${availableOptions.wine_pairings?.slice(0, 6).join(', ') || 'ninguno'}
- Espirituosos disponibles: ${availableOptions.spirit_pairings?.slice(0, 6).join(', ') || 'ninguno'}` : ''}

ALTERNATIVAS PARA TÉRMINOS NO RECONOCIDOS:
- Para vinos: nuestras VARIEDADES son ${this.filters.wine_pairings?.slice(0, 10).join(', ')}
- Para sabores: ${count > 6 ? `en estos ${count} chocolates tenemos ${availableOptions.available_flavors?.slice(0, 6).join(', ') || 'ninguno'}` : `nuestras palabras clave están en inglés (apricot, cherry, vanilla...)`}
- Para orígenes: ${this.filters.origin_countries?.slice(0, 10).join(', ')}

RESPUESTA JSON:
{
  "message": "tu respuesta conversacional en español",
  "preferences": ${JSON.stringify(extractedCriteria.criteria)},
  "recommendations": ${count <= 6 ? "array de chocolates" : "[]"},
  "debug_count": ${count}
}`
    } else { // 'fr'
      systemPrompt = `🇫🇷 RÉPONDRE EN FRANÇAIS - Toutes tes réponses doivent être en français avec un ton chaleureux et professionnel.

Tu es le sommelier XOCOA qui applique le WORKFLOW INTELLIGENT avec validation stricte.

${extractedCriteria.unrecognized_terms && extractedCriteria.unrecognized_terms.length > 0 ?
`TERMES NON RECONNUS: ${extractedCriteria.unrecognized_terms.join(', ')}
→ Tu DOIS mentionner ces termes et proposer les alternatives disponibles` : ''}

WORKFLOW:
- Si termes non reconnus → Expliquer + proposer alternatives
- Si 0 chocolats → Propose d'assouplir un critère
- Si 1-6 chocolats → RECOMMANDATIONS FINALES
- Si 7+ chocolats → DEMANDE UN CRITÈRE SUPPLÉMENTAIRE

CRITÈRES VALIDÉS: ${JSON.stringify(extractedCriteria.criteria)}
RÉSULTATS: ${count} chocolats trouvés

${count > 6 ? `OPTIONS DISPONIBLES DANS LES ${count} CHOCOLATS:
- Origines: ${availableOptions.origins.slice(0, 8).join(', ')}
- Prix: ${availableOptions.price_range}
- Pourcentages: ${availableOptions.cocoa_range}
- Types: ${availableOptions.types.slice(0, 5).join(', ')}
- Saveurs spécifiques disponibles: ${availableOptions.available_flavors?.slice(0, 8).join(', ') || 'aucune'}
- Cépages disponibles: ${availableOptions.wine_pairings?.slice(0, 6).join(', ') || 'aucun'}
- Spiritueux disponibles: ${availableOptions.spirit_pairings?.slice(0, 6).join(', ') || 'aucun'}` : ''}

ALTERNATIVES POUR TERMES NON RECONNUS:
- Pour les vins: nos CÉPAGES sont ${this.filters.wine_pairings?.slice(0, 10).join(', ')}
- Pour les saveurs: ${count > 6 ? `dans ces ${count} chocolats nous avons ${availableOptions.available_flavors?.slice(0, 6).join(', ') || 'aucune'}` : `nos mots-clés sont en anglais (apricot, cherry, vanilla...)`}
- Pour les origines: ${this.filters.origin_countries?.slice(0, 10).join(', ')}

RETOUR JSON:
{
  "message": "ta réponse conversationnelle en français",
  "preferences": ${JSON.stringify(extractedCriteria.criteria)},
  "recommendations": ${count <= 6 ? "array des chocolats" : "[]"},
  "debug_count": ${count}
}`
    }

    const completion = await this.openai.chat.completions.create({
      model: 'gpt-3.5-turbo',
      messages: [
        {
          role: 'system',
          content: systemPrompt
        },
        {
          role: 'user',
          content: lang === 'en'
            ? `MESSAGE: "${originalMessage}"
RESULTS: ${count} chocolates

${count <= 6 && count > 0 ? `CHOCOLATES FOUND:
${JSON.stringify(filteredChocolates.slice(0, 6), null, 2)}` : ''}`
            : lang === 'es'
            ? `MENSAJE: "${originalMessage}"
RESULTADOS: ${count} chocolates

${count <= 6 && count > 0 ? `CHOCOLATES ENCONTRADOS:
${JSON.stringify(filteredChocolates.slice(0, 6), null, 2)}` : ''}`
            : `MESSAGE: "${originalMessage}"
RÉSULTATS: ${count} chocolats

${count <= 6 && count > 0 ? `CHOCOLATS TROUVÉS:
${JSON.stringify(filteredChocolates.slice(0, 6), null, 2)}` : ''}`
        }
      ],
      temperature: 0.8,
      max_tokens: 400
    })

    // Parse response
    let result
    try {
      const content = completion.choices[0].message.content
      const jsonMatch = content.match(/\{[\s\S]*\}/)
      if (jsonMatch) {
        result = JSON.parse(jsonMatch[0])
      } else {
        result = {
          message: content,
          preferences: extractedCriteria.criteria,
          recommendations: count <= 6 ? filteredChocolates.slice(0, 6) : [],
          debug_count: count
        }
      }
    } catch (e) {
      result = {
        message: completion.choices[0].message.content,
        preferences: extractedCriteria.criteria,
        recommendations: count <= 6 ? filteredChocolates.slice(0, 6) : [],
        debug_count: count
      }
    }

    // S'assurer que les recommandations sont incluses si ≤6
    if (count <= 6 && count > 0 && (!result.recommendations || result.recommendations.length === 0)) {
      result.recommendations = filteredChocolates.slice(0, count)
    }

    // Recommendations are already in the correct language from the language-specific database
    // No need to translate anymore!

    return result
  }

  // Analyser les options disponibles dans un sous-ensemble
  analyzeAvailableOptions(chocolates) {
    const origins = [...new Set(chocolates.map(c => c.origin_country).filter(Boolean))].slice(0, 10)
    const types = [...new Set(chocolates.map(c => c.type).filter(Boolean))].slice(0, 5)
    const prices = chocolates.map(c => parseFloat(c.price_retail)).filter(p => p > 0)
    const cocoaPercentages = chocolates.map(c => c.cocoa_percentage).filter(Boolean)

    // Extraire les accords disponibles
    const wine_pairings = [...new Set(
      chocolates
        .map(c => c.pairings_wine?.split(', ') || [])
        .flat()
        .map(w => w?.trim())
        .filter(Boolean)
    )].slice(0, 8)

    const spirit_pairings = [...new Set(
      chocolates
        .map(c => c.pairings_spirits?.split(', ') || [])
        .flat()
        .map(s => s?.trim())
        .filter(Boolean)
    )].slice(0, 6)

    // Extraire les saveurs disponibles avec comptage
    const flavorCounts = {}
    chocolates.forEach(c => {
      const allFlavors = [
        c.flavor_notes_primary || '',
        c.flavor_notes_secondary || '',
        c.flavor_notes_tertiary || ''
      ].join(', ').split(',').map(f => f.trim().toLowerCase()).filter(Boolean)

      allFlavors.forEach(flavor => {
        if (flavor.length > 2) { // Ignorer les mots trop courts
          flavorCounts[flavor] = (flavorCounts[flavor] || 0) + 1
        }
      })
    })

    // Trier par fréquence et garder les plus populaires
    const available_flavors = Object.entries(flavorCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 12)
      .map(([flavor, count]) => `${flavor} (${count})`)

    return {
      origins,
      types,
      price_range: prices.length ? `${Math.min(...prices).toFixed(2)}€ - ${Math.max(...prices).toFixed(2)}€` : '',
      cocoa_range: cocoaPercentages.length ? `${Math.min(...cocoaPercentages)}% - ${Math.max(...cocoaPercentages)}%` : '',
      wine_pairings,
      spirit_pairings,
      available_flavors
    }
  }
}

module.exports = { SmartHybridSommelier }
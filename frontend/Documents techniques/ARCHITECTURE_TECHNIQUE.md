# XOCOA Sommelier - Documentation technique

## Vue d'ensemble

XOCOA Sommelier est une application web intelligente de recommandation de chocolats utilisant l'IA (OpenAI GPT-4o) pour offrir une expérience conversationnelle naturelle et personnalisée.

## Architecture générale

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                      │
├─────────────────────────────────────────────────────────────┤
│ • Interface conversationnelle multilingue (FR/EN/ES)      │
│ • Composants React optimisés                               │
│ • Gestion d'état des préférences utilisateur               │
│ • SEO multilingue + 4 pages statiques                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  API Layer (/api/chat.js)                  │
├─────────────────────────────────────────────────────────────┤
│ • Validation des requêtes                                  │
│ • Gestion des erreurs                                      │
│ • Logging Supabase (connection, search, blocked)          │
│ • Interface avec Smart Hybrid Sommelier                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Smart Hybrid Sommelier Engine                 │
├─────────────────────────────────────────────────────────────┤
│ • Extraction de critères via OpenAI GPT-4o                │
│ • Filtrage local optimisé (2129 chocolats)                │
│ • Workflow intelligent de recommandation                   │
│ • Traduction automatique FR via GPT-4o-mini               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Base de données                           │
├─────────────────────────────────────────────────────────────┤
│ • chocolates.json (2129 chocolats, 106 champs)            │
│ • filters.json (filtres et taxonomies)                    │
│ • Support complet des awards et certifications            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  Analytics (Supabase)                      │
├─────────────────────────────────────────────────────────────┤
│ • Stockage persistant des événements                       │
│ • Rapports hebdomadaires automatiques                      │
│ • Statistiques temps réel (connexions, recherches)        │
└─────────────────────────────────────────────────────────────┘
```

## Composants principaux

### 1. Smart Hybrid Sommelier (`src/services/smart-hybrid-sommelier.cjs`)

**Architecture hybride en 3 étapes :**

1. **Extraction de critères (OpenAI GPT-4o)** : Analyse le message utilisateur et extrait les critères de recherche
2. **Filtrage local (JavaScript)** : Applique les filtres sur la base de 2129 chocolats
3. **Décision intelligente (OpenAI GPT-3.5)** : Détermine la suite selon le workflow

**Workflow intelligent :**
- 0 chocolats → Propose d'assouplir un critère
- 1-6 chocolats → Recommandations finales (déjà dans la langue correcte)
- 7+ chocolats → Demande un critère supplémentaire

**Système multilingue sans traduction** :
- **FR** 🇫🇷: Charge `chocolates_fr.json` + utilise `.fr` de filters.json + synonymes français
- **EN** 🇬🇧: Charge `chocolates_en.json` + utilise clés EN de filters.json + synonymes anglais
- **ES** 🇪🇸: Charge `chocolates_es.json` + utilise `.es` de filters.json + synonymes espagnols
- **Pas d'intermédiaire** : Tout reste dans la langue sélectionnée du début à la fin

#### Critères de recherche supportés (35 critères)

Le système GPT-4o comprend et extrait **automatiquement** ces critères depuis filters.json :

**Origines & Fabrication :**
- `origin_country` : 23 pays (Madagascar, Ecuador, Peru, Ghana...)
- `origin_region` : 154 régions (Sambirano, Piura, Ambanja, Chuao...)
- `origin_continent` : 4 continents (Africa, Asia, South America, Americas)
- `maker_country` : 16 pays fabricants (France, Belgium, Switzerland, USA...)
- `bean_variety` : 6 variétés (Criollo, Trinitario, Nacional, Forastero...)

**Caractéristiques chocolat :**
- `cocoa_percentage` : Pourcentage de cacao (<40%, 40-50%, 50-70%, 70-85%, >85%)
- `type` : bar, bonbon, truffle, disc, tablet, square, couverture
- `texture_mouthfeel` : creamy, silky, velvety, smooth, buttery, waxy
- `texture_melt` : quick, slow, smooth, creamy (NOUVEAU)
- `finish_length` : short, medium, long, very long, persistent (NOUVEAU)
- `finish_character` : clean, complex, dry, evolving, lingering, sweet (NOUVEAU)
- `production_craft_level` : artisan, boutique, craft, premium, industrial (NOUVEAU)

**Saveurs :**
- `flavor_keywords` : 485+ saveurs (fruity, nutty, floral, spicy, earthy...)

**Prix & Tri :**
- `price_min` / `price_max` : Fourchette de prix en euros
- `sort_by` : price_desc, price_asc, rating_desc, cocoa_desc
- `limit` : Nombre de résultats (ex: "top 3", "les 5 meilleurs")

**Accords gastronomiques :**
- `wine_pairing` : Cabernet, Pinot Noir, Port, Champagne, Merlot...
- `spirit_pairing` : Whisky, Rum, Cognac, Bourbon, Armagnac...
- `coffee_pairing` : Espresso, Ethiopian, Colombian, Kona...
- `tea_pairing` : Earl Grey, Matcha, Oolong, Pu-erh, Darjeeling...
- `cheese_pairing` : Aged Cheddar, Brie, Blue Cheese, Manchego...
- `fruit_pairing` : Berries, Citrus, Stone Fruits, Tropical Fruits...
- `nut_pairing` : Almonds, Hazelnuts, Walnuts, Pecans, Pistachios...

**Éthique & Régimes :**
- `certification` : Organic, Fair Trade, Direct Trade, B-Corp, Rainforest Alliance...
- `dietary` : vegan, gluten-free, organic, keto-friendly (NOUVEAU)

**Production & Awards :**
- `production_method` : bean-to-bar, tree-to-bar (NOUVEAU)
- `has_awards` : Chocolats primés uniquement (NOUVEAU)
- `awards` : International Chocolate Awards, Academy of Chocolate, Good Food Award...
- `awards_year` : Année spécifique d'award

**Occasions :**
- `serving_occasion` : gift, tasting, celebration, pairing, meditation (NOUVEAU)

#### Compréhension multilingue et sélection intelligente des saveurs

**Sélection exacte des saveurs** (amélioration majeure) :
- GPT-4o **choisit directement** parmi les 485 saveurs disponibles au lieu de traduire
- Évite les erreurs de traduction (ex: "iode" trouve "brine" dans la liste, pas "iodine")
- Exemples de mappings automatiques :
  - "iode" (FR) → cherche et trouve "brine" dans la liste
  - "fumé" (FR) → trouve "smoke" ou "tobacco"
  - "vanille" (FR/ES) → trouve "vanilla"

**Traduction pays/régions et contextes** :
- 🇫🇷 "chocolat bio équitable" → certification: Fair Trade + Organic
- 🇬🇧 "creamy texture with berries" → texture: creamy + fruit_pairing: Berries
- 🇪🇸 "para regalar artesanal" → occasion: gift + craft_level: artisan

**Exemples de compréhension avancée :**
- "les 3 plus chers" → sort_by: "price_desc", limit: 3
- "plus de 18 euros" → price_min: 18
- "chocolat français pour cadeau avec notes d'iode" → maker_country: France, occasion: gift, flavor_keywords: ["brine"]
- "texture onctueuse avec du whisky" → texture: creamy, spirit_pairing: Whisky
- "Madagascar région Sambirano bio" → origin_country: Madagascar, origin_region: Sambirano, certification: Organic
- "pour offrir artisanal primé" → occasion: gift, craft_level: artisan, awards: non-null

### 2. Frontend React (`src/components/`)

**Structure des composants :**
```
src/components/
├── Chat/
│   ├── ChatInterface.js      # Interface principale de conversation
│   ├── ChatMessage.js        # Affichage des messages
│   └── FixedChatInput.js     # Input fixe en bas de page
├── Recommendations/
│   ├── PremiumChocolateCard.js      # Cartes de recommandation (avec tasting_notes + maker_website)
│   └── ChocolateRecommendations.js  # Grille de cartes
├── SEO/
│   └── SEOHead.js            # Métadonnées SEO multilingues (FR/EN/ES)
├── UI/
│   └── Header.js             # En-tête avec sélecteur de langue
└── LanguageSelector/
    └── LanguageSelector.js   # Commutateur FR/EN/ES (style épuré)
```

### 3. Base de données

**chocolates.json** (9.3MB, 106 champs par chocolat) :
- Données complètes importées depuis Excel
- 2129 chocolats avec métadonnées riches
- Support des awards, certifications, accords mets-vins

**Champs principaux :**
- Identification : `id`, `name`, `brand`, `maker_name`, `maker_website`
- Origine : `origin_country`, `origin_region`, `bean_variety`
- Caractéristiques : `cocoa_percentage`, `type`, `rating`
- Saveurs : `flavor_notes_primary/secondary/tertiary`
- Accords : `pairings_wine`, `pairings_spirits`, `pairings_cheese`
- Awards : `awards`, `awards_year`
- Dégustation : `tasting_notes`, `expert_review`

**Sites web des fabricants** :
- Champ `maker_website` dans les 3 bases de données (EN/FR/ES)
- **1414 chocolats sur 2129 (66.4%)** ont un lien fabricant cliquable
- Script `add-websites-to-translations.js` copie les URLs entre langues
- Affichage : Nom de marque cliquable avec icône de lien externe
- Permet à l'utilisateur d'accéder directement au site du fabricant depuis les recommandations

## Système Multilingue

### Architecture des bases de données par langue

XOCOA utilise des **bases de données pré-traduites** pour offrir une expérience optimale sans latence de traduction en temps réel.

```
data/
├── chocolates_en.json       # Base anglaise (originale - 9.3 MB)
├── chocolates_fr.json       # Base française (traduite - 9.5 MB)
├── chocolates_es.json       # Base espagnole (traduite - 9.4 MB)
└── filters.json             # Filtres multilingues

public/                      # Copies pour Netlify Functions
├── chocolates_en.json
├── chocolates_fr.json
└── chocolates_es.json
```

### Avantages du système pré-traduit

✅ **Performance** : Latence 0ms vs 2-3s (traduction temps réel)
✅ **Qualité** : Traductions professionnelles cohérentes via GPT-4o
✅ **Coût** : $0 par requête vs $0.002 (économie de ~100%)
✅ **Fiabilité** : Pas de dépendance aux APIs externes en temps réel
✅ **Évolutivité** : Simple d'ajouter de nouvelles langues

### Champs traduits

Les champs suivants sont traduits dans chaque langue :
- `tasting_notes` : Notes de dégustation professionnelles
- `expert_review` : Avis d'expert sommeliers
- `flavor_notes_primary` : Descriptions de saveurs primaires
- `flavor_notes_secondary` : Descriptions de saveurs secondaires

Les autres champs restent identiques (noms, marques, origines, prix, etc.)

### Fonctionnement

**1. Frontend → API**
```javascript
fetch('/api/chat', {
  body: JSON.stringify({
    message: "je cherche un chocolat...",
    language: "fr"  // Langue actuelle de l'interface
  })
})
```

**2. Smart Hybrid Sommelier**
```javascript
async processUserMessage({ message, currentPreferences, conversationHistory, language = 'fr' }) {
  // Store language for filtering and synonym resolution
  this.currentLanguage = language

  // IMPORTANT: Reload data with correct language if language changed
  if (!this.chocolates.length || this.loadedLanguage !== language) {
    this.loadData(language)  // Charge chocolates_fr.json / chocolates_en.json / chocolates_es.json
    this.loadedLanguage = language
  }

  // Extract criteria using GPT-4o with language-specific instructions
  const extractedCriteria = await this.extractCriteriaWithAI(message, currentPreferences, conversationHistory)

  // Filter chocolates locally (already in correct language)
  const filteredChocolates = this.filterChocolates(extractedCriteria)

  // Make decision with GPT-3.5
  return await this.makeDecisionWithAI(message, extractedCriteria, filteredChocolates, count, conversationHistory)
}
```

**3. Extraction de critères multilingue (GPT-4o)**
```javascript
// Instructions dynamiques selon la langue
if (lang === 'fr') {
  languageInstruction = `🇫🇷 UTILISATEUR FRANCOPHONE: Il parle FRANÇAIS
- Les valeurs de filtres ci-dessous sont en FRANÇAIS
- Tu dois retourner les valeurs EXACTEMENT comme elles apparaissent dans les listes
- NE traduis PAS vers l'anglais!`
}

// Valeurs de filtres générées dynamiquement
SAVEURS: ${this.getFilterKeys('flavors').slice(0, 50).join(', ')}...
// FR: champignon, iode, vanille, fumé...
// EN: mushroom, iodine, vanilla, smoke...
// ES: hongo, yodo, vainilla, humo...
```

**4. Résolution de synonymes**
```javascript
resolveSynonym('sustainability_certificationss', 'bio', 'fr')
// FR: "bio" → "Biologique"
// EN: "organic" → "Organic"
// ES: "bio" → "Orgánico"
```

**5. Réponse**
Les chocolats retournés sont déjà dans la langue demandée, aucune traduction nécessaire !

### Génération des traductions

#### Méthode 1 : Traduction traditionnelle (GPT-4o) - Français

**Script** : `scripts/complete-translations.js`

```bash
node scripts/complete-translations.js fr
```

**Processus** :
1. Charge `chocolates_en.json` (2129 chocolats)
2. Traduit par batches de 5 chocolats via GPT-4o
3. Génère `chocolates_fr.json`
4. **Durée** : ~72 minutes (1h12)
5. **Coût** : ~$6 USD
6. **Qualité** : Excellente - vocabulaire gastronomique professionnel

**Avantages** :
- Haute qualité pour langue principale (français)
- Nuances gastronomiques préservées
- Terminologie professionnelle précise

#### Méthode 2 : Traduction par dictionnaire (GPT-4o-mini) - Espagnol

**Script** : `scripts/translate-es-full.js`

```bash
node scripts/translate-es-full.js
```

**Processus innovant** :
1. **Extraction** : Analyse tous les 2129 chocolats et extrait 6707 termes uniques
2. **Traduction dictionnaire** : Traduit ces 6707 termes en espagnol via GPT-4o-mini
   - Batches de 150 termes
   - Durée : ~15 minutes
3. **Application** : Remplace chaque terme par sa traduction dans tous les chocolats
4. **Génération** : Produit `chocolates_es.json` complet
5. **Durée totale** : ~72 minutes (1h12)
6. **Coût** : ~$0.03 USD (**200x moins cher** que méthode traditionnelle!)
7. **Couverture** : 5783/6707 termes traduits (86%)

**Avantages** :
- **Économique** : Réduction de coût de 200x ($6 → $0.03)
- **Rapide** : Même durée mais beaucoup moins d'appels API
- **Cohérent** : Traductions uniformes pour termes récurrents
- **Scalable** : Idéal pour ajouter de nouvelles langues

**Comparaison des coûts** :
| Langue | Méthode | Durée | Coût | Qualité |
|--------|---------|-------|------|---------|
| Français | GPT-4o (batch 5) | 72 min | $6.00 | ⭐⭐⭐⭐⭐ |
| Espagnol | Dictionnaire GPT-4o-mini | 72 min | $0.03 | ⭐⭐⭐⭐ |

### Filtres multilingues (filters.json)

**Architecture unifiée** : Un seul fichier `filters.json` contient toutes les langues

**Structure** :
```json
{
  "flavors": {
    "fruity": {"fr": "fruité", "es": "afrutado"},
    "nutty": {"fr": "noisetté", "es": "a nuez"},
    "floral": {"fr": "floral", "es": "floral"}
  },
  "maker_countries": {
    "France": {"fr": "France", "es": "Francia"},
    "Belgium": {"fr": "Belgique", "es": "Bélgica"}
  }
}
```

**Avantages** :
- ✅ Un seul fichier source de vérité
- ✅ Pas de modification de code nécessaire
- ✅ Ajout de nouvelles langues facile
- ✅ Cohérence garantie entre langues
- ✅ Maintenance simplifiée

**Script de génération** : `scripts/create-multilingual-filters.js`

### Interface utilisateur multilingue

**Composants** :
- `LanguageContext` : Gestion globale de la langue (FR/EN/ES)
- `LanguageSelector` : Sélecteur de langue épuré (codes FR/EN/ES sans drapeaux)
- `translations.js` : Traductions complètes de l'interface pour chaque langue (35 questions dynamiques)

**Langues supportées** :
- 🇫🇷 **Français (FR)** - Langue par défaut
- 🇬🇧 **Anglais (EN)** - Base de données originale
- 🇪🇸 **Espagnol (ES)** - Traduit depuis l'anglais

**Détection automatique** :
1. Vérifie la préférence sauvegardée (localStorage)
2. Sinon, détecte la langue du navigateur
3. Par défaut : français

### Ajout d'une nouvelle langue

1. Modifier `scripts/translate-database.js` pour ajouter la langue
2. Exécuter le script de traduction
3. Copier `data/chocolates_XX.json` vers `public/`
4. Mettre à jour `netlify/functions/chat.js` pour charger la nouvelle base
5. Ajouter les traductions UI dans `src/translations/translations.js`
6. Ajouter la langue dans `src/contexts/LanguageContext.js` (LANGUAGES)

### Maintenance

Si la base anglaise change :
1. Mettre à jour `data/chocolates_en.json`
2. Relancer `node scripts/translate-database.js`
3. Copier vers `public/` : `cp data/chocolates_*.json public/`
4. Déployer

## Technologies utilisées

### Stack technique
- **Frontend** : Next.js 14, React 18, Tailwind CSS
- **Backend** : Next.js API Routes, Node.js
- **IA** : OpenAI GPT-4o (extraction critères + décisions conversationnelles)
- **Base de données** : JSON statique multilingue (EN/FR/ES)
- **Déploiement** : Netlify avec fonctions serverless

### Dépendances principales
```json
{
  "next": "14.2.32",
  "react": "^18",
  "openai": "^4.0.0",
  "tailwindcss": "^3.3.0"
}
```

## Flux de données

### 1. Interaction utilisateur
```
Utilisateur → ChatInterface → API /chat → SmartHybridSommelier
```

### 2. Traitement IA
```
Message → extractCriteriaWithAI() → filterChocolates() → makeDecisionWithAI()
```

### 3. Réponse
```
Recommandations → translateRecommendations() → ChocolateCard → Utilisateur
```

## Optimisations de performance

### 1. Traitement hybride
- **OpenAI** : Intelligence conversationnelle et extraction de critères
- **Local** : Filtrage rapide sur 2129 chocolats (< 10ms)
- **OpenAI-mini** : Traductions françaises économiques

### 2. Limitations intelligentes
- Max 6 recommandations finales (vs 10 avant)
- Tokens limités : 300 (extraction), 800 (décision), 600 (traduction)
- Température optimisée : 0.3 (précision) vs 0.8 (créativité)

### 3. Mise en cache
- Base de données chargée en mémoire au démarrage
- Filtres précalculés et optimisés
- Pas de requêtes DB répétées

## Sécurité

### Variables d'environnement

#### Variables obligatoires
```
OPENAI_API_KEY=sk-...  # Clé API OpenAI (extraction critères + décisions)
```

#### Variables Supabase (analytics persistant)
```
SUPABASE_URL=https://eqrocnxcvrpgjyzncrgz.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGc...  # Service role key pour Netlify Functions
NEXT_PUBLIC_SUPABASE_URL=https://eqrocnxcvrpgjyzncrgz.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...  # Anon key pour client (optionnel)
```

#### Variables SMTP (rapports hebdomadaires - optionnel)
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=votre-email@gmail.com
SMTP_PASS=xxxx xxxx xxxx xxxx  # Gmail App Password
REPORT_EMAIL_FROM=noreply@xocoa-sommelier.com
REPORT_EMAIL_TO=julien@bonplein.fr
```

**Note** : Si les variables SMTP ne sont pas configurées, les rapports ne seront pas envoyés mais l'application fonctionnera normalement.

### Mesures de sécurité implémentées

#### 1. Logging et monitoring des connexions

**Logs de connexion** :
- **Logging complet** : Timestamp, IP, User-Agent, Referer pour chaque requête
- **Format** : `🔐 [timestamp] Connection - IP: xxx.xxx.xxx.xxx | UA: ... | Referer: ...`
- **Accès** : Logs consultables dans Netlify Functions → chat → Recent invocations
- **Utilité** : Détection d'activités suspectes, analyse du trafic, audit de sécurité

**Logs des critères de recherche (Analytics)** :
- **Tracking automatique** : Tous les critères utilisés par les visiteurs
- **Format** : `📊 [SEARCH] IP: xxx | Lang: fr | Results: 3 | origin_country:Ecuador | cocoa_percentage_min:70 | flavor_keywords:fruity`
- **Données trackées** :
  - IP du client et langue utilisée
  - Nombre de résultats trouvés
  - Tous les critères de recherche (origine, pourcentage cacao, saveurs, type, awards, etc.)
- **Utilité** :
  - Identifier les critères les plus populaires
  - Analyser les tendances de recherche
  - Détecter les combinaisons fréquentes
  - Optimiser les recommandations futures
  - Identifier les recherches sans résultats (amélioration continue)

**Logs des choix utilisateurs (User Choice Tracking)** :
- **Format** : `📊 [USER_CHOICE] filter=cocoa_percentage | value=70-85% | lang=fr`
- **Tracking détaillé** : Enregistre chaque sélection de filtre par l'utilisateur
- **Filtres trackés** (19 total) :
  - `cocoa_percentage` : Préférences de pourcentage de cacao
  - `flavor_profile` : Saveurs sélectionnées
  - `origin_country`, `origin_continent` : Origines géographiques
  - `maker_country` : Pays de fabrication
  - `type` : Types de chocolat (bar, bonbon, truffle...)
  - `bean_variety` : Variétés de fèves
  - `certification` : Certifications (bio, fair trade...)
  - **8 nouveaux filtres** :
    - `dietary` : Restrictions alimentaires (vegan, gluten-free, keto...)
    - `production_craft_level` : Niveau artisanal (artisan, boutique...)
    - `finish_character` : Caractère de finale (clean, complex, sweet...)
    - `finish_length` : Longueur de finale (short, medium, long...)
    - `texture_melt` : Fonte du chocolat (quick, slow, creamy...)
    - `has_awards` : Recherche de chocolats primés
    - `production_method` : Méthode (bean-to-bar, tree-to-bar)
    - `serving_occasion` : Occasion (gift, tasting, celebration...)
- **Utilité analytics** :
  - Comprendre les préférences utilisateurs par langue
  - Identifier les filtres les plus/moins utilisés
  - Optimiser l'ordre des questions dans le workflow
  - Améliorer l'expérience conversationnelle

#### 2. Rate Limiting (Protection contre abus)
- **Limite** : 10 requêtes par minute par IP
- **Fenêtre** : 60 secondes glissantes
- **Réponse** : HTTP 429 (Too Many Requests) avec Retry-After header
- **Nettoyage** : Automatic cleanup toutes les 5 minutes pour éviter les fuites mémoire
- **Impact** : Empêche les attaques par force brute et le scraping massif

#### 3. Validation des headers de sécurité
- **Origines autorisées** :
  - `https://xocoasommelier.netlify.app`
  - `http://localhost:3000` (développement)
  - `http://localhost:3001` (développement)
- **User-Agent** : Requis et validé
- **Bots bloqués** :
  - scrapy, beautifulsoup, python-requests
  - wget, curl, httpclient, okhttp
  - selenium, phantomjs, headless
- **Réponse** : HTTP 403 (Forbidden) pour accès non autorisés

#### 4. Obfuscation silencieuse des données
**Protection contre le scraping** par variation légère des données sensibles :

##### Prix (±2% de variation)
- Variation basée sur hash IP + ID chocolat
- Cohérence par session utilisateur
- Exemple : Prix 15.00€ → 14.70€-15.30€ selon IP
- **Objectif** : Empêcher l'extraction de prix exacts pour concurrence

##### Avis experts (substitution de synonymes)
- Remplacement subtil de mots-clés par synonymes
- Basé sur hash IP pour cohérence
- Exemple : "excellent" → "remarquable", "exceptionnel", "superbe"
- **Mots ciblés** : excellent, good, intense, smooth, creamy
- **Objectif** : Rendre impossible la comparaison exacte entre sessions

##### Notes de dégustation (variation des descriptions)
- Synonymes pour descriptions de saveurs
- Exemple : "fruity" → "fruité", "aux notes de fruits", "fruitées"
- **Saveurs ciblées** : fruity, nutty, floral, spicy
- **Objectif** : Protection du contenu propriétaire

**Implémentation** :
```javascript
// Appliqué automatiquement à chaque réponse
result.recommendations = obfuscateChocolates(result.recommendations, clientIp)
```

#### 5. CORS et méthodes HTTP
- **CORS** : Restreint aux origines autorisées
- **Méthodes** : Uniquement POST et OPTIONS
- **GET bloqué** : HTTP 405 (Method Not Allowed)

### Architecture de sécurité

```
┌────────────────────────────────────────────────────────┐
│                   Requête entrante                     │
└────────────────┬───────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│  1. Logging : IP + UA + Referer + Timestamp           │
└────────────────┬───────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│  2. Rate Limiting : Max 10 req/min par IP             │
│     → 429 si dépassé                                   │
└────────────────┬───────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│  3. Validation Headers : Origin + User-Agent          │
│     → 403 si bot ou origine invalide                   │
└────────────────┬───────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│  4. Traitement IA + Filtrage                          │
└────────────────┬───────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│  5. Obfuscation : Prix ±2% + Synonymes                │
│     (basé sur hash IP)                                 │
└────────────────┬───────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│                Réponse JSON obfusquée                  │
└────────────────────────────────────────────────────────┘
```

### Protection des données sources

**Suppression du champ `source`** :
- Le champ `source` (identifiant la provenance des données) a été supprimé de tous les fichiers JSON
- Objectif : Empêcher le traçage de l'origine des données (scraping detection)
- Fichiers nettoyés :
  - `data/chocolates.json`
  - `data/chocolates_en.json`
  - `data/chocolates_fr.json`
  - `data/chocolates_es.json`
  - `public/chocolates.json`

### Validation et sanitization
- Validation stricte des inputs utilisateur
- Sanitization des réponses OpenAI
- Gestion robuste des erreurs IA
- Parse JSON sécurisé avec try/catch

## Déploiement

### Structure Netlify
```
netlify/
├── functions/
│   └── chat.js           # Fonction serverless pour l'API
└── netlify.toml          # Configuration de déploiement
```

### Variables de production
- `OPENAI_API_KEY` configurée dans Netlify
- Build automatique sur push GitHub
- Fonctions serverless pour l'API

## Maintenance et évolution

### Mise à jour de la base de données
1. Modifier `data/chocolates_database.xlsx`
2. Exécuter le script de réimport Python
3. Vérifier `data/chocolates.json` et `data/filters.json`
4. Tester en local puis déployer

### Ajout de nouvelles fonctionnalités
1. Modifier `SmartHybridSommelier` pour la logique métier
2. Adapter les composants React pour l'UI
3. Mettre à jour les prompts OpenAI si nécessaire

### Monitoring et Analytics

#### Architecture Analytics V2 (Supabase)

**Système persistant** : Toutes les données analytics sont stockées dans Supabase PostgreSQL avec historique permanent.

**Table `analytics_logs`** :
```sql
CREATE TABLE analytics_logs (
  id BIGSERIAL PRIMARY KEY,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  event_type TEXT NOT NULL,  -- 'connection', 'search', 'blocked'
  ip_address TEXT,
  user_agent TEXT,
  referer TEXT,
  language TEXT,             -- 'fr', 'en', 'es'
  criteria JSONB,            -- Critères de recherche complets
  results_count INTEGER,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Événements loggés** :
- **connection** : Nouvelle connexion à l'API (IP, User-Agent, Referer)
- **search** : Recherche effectuée (langue, critères complets, nombre de résultats)
- **blocked** : Requête bloquée (rate limit ou headers invalides)

**Avantages** :
- ✅ **Historique permanent** : Aucune perte de données (vs Netlify logs 24-48h)
- ✅ **Requêtes SQL** : Analyses avancées possibles
- ✅ **Gratuit** : Plan gratuit Supabase (500MB) largement suffisant
- ✅ **Temps réel** : Consultation immédiate dans dashboard Supabase
- ✅ **Scalable** : Indexation automatique, performances optimales

**Client Supabase** :
- `src/utils/supabase.cjs` : Client pour Netlify Functions (CommonJS)
- `src/utils/supabase.js` : Client pour frontend (ES6) - optionnel

**Logging non-bloquant** :
```javascript
logAnalytics('search', {
  ip: clientIp,
  language: lang,
  criteria: result.preferences,
  resultsCount: resultCount
}).catch(err => console.error('Failed to log:', err))
```

**Requêtes SQL utiles** :
```sql
-- Connexions des 7 derniers jours
SELECT COUNT(*) as connections, COUNT(DISTINCT ip_address) as unique_ips
FROM analytics_logs
WHERE event_type = 'connection'
  AND created_at > NOW() - INTERVAL '7 days';

-- Top 10 critères de recherche
SELECT
  jsonb_object_keys(criteria) as criterion,
  COUNT(*) as count
FROM analytics_logs
WHERE event_type = 'search'
  AND created_at > NOW() - INTERVAL '7 days'
GROUP BY criterion
ORDER BY count DESC
LIMIT 10;

-- Répartition par langue
SELECT
  language,
  COUNT(*) as searches,
  ROUND(COUNT(*)::numeric / SUM(COUNT(*)) OVER () * 100, 2) as percentage
FROM analytics_logs
WHERE event_type = 'search'
  AND created_at > NOW() - INTERVAL '7 days'
GROUP BY language;
```

#### Rapports hebdomadaires automatiques

**Configuration** :
- **Fonction** : `netlify/functions/weekly-report.js`
- **Planification** : Tous les samedis à 9h00 GMT (netlify.toml)
- **Source** : Supabase `analytics_logs` (7 derniers jours)
- **Destinataire** : julien@bonplein.fr
- **Format** : Email HTML élégant (style Sulphur Point)

**Contenu du rapport** :
- **Statistiques globales** :
  - Connexions totales
  - Recherches effectuées
  - Visiteurs uniques (IP)
  - Requêtes bloquées (sécurité)

- **Répartition linguistique** :
  - Nombre et pourcentage de recherches FR/EN/ES
  - Identification de la langue dominante

- **Top 10 critères de recherche** :
  - Critères les plus utilisés avec occurrences
  - Ex: origin_country, cocoa_percentage, flavor_keywords, certification

- **Insights automatiques** :
  - Langue dominante de la semaine
  - Critère le plus populaire
  - Taux d'engagement (recherches/connexions)
  - Tendances par rapport à la semaine précédente

**Test manuel** :
```bash
# Local (nécessite variables SMTP)
curl -X POST http://localhost:8888/.netlify/functions/weekly-report

# Production
curl -X POST https://xocoasommelier.netlify.app/.netlify/functions/weekly-report
```

**Configuration** : Voir `Documents techniques/SUPABASE_SETUP.md` pour le guide complet.

#### Logs système
- Logs d'erreur via console.error()
- Suivi des performances OpenAI
- Monitoring des taux d'erreur API
- Logs Supabase accessibles via dashboard

## SEO et Référencement

### Optimisation multilingue

**Composant SEOHead** (`src/components/SEO/SEOHead.js`) :
- Métadonnées dynamiques selon la langue (FR/EN/ES)
- Open Graph pour réseaux sociaux
- Twitter Cards
- Schema.org JSON-LD pour rich snippets
- Hreflang tags pour alternatives linguistiques

**Exemple de métadonnées FR** :
```
Title: XOCOA - Sommelier du Chocolat IA | 2000+ Chocolats Premium
Description: Découvrez votre chocolat idéal parmi 2000+ références premium...
Keywords: chocolat premium, bean to bar, chocolat artisanal, sommelier chocolat...
```

### Fichiers SEO

**robots.txt** (`public/robots.txt`) :
```
User-agent: *
Allow: /
Sitemap: https://xocoa-sommelier.com/sitemap.xml
```

**sitemap.xml** (`public/sitemap.xml`) :
- Inclut toutes les versions linguistiques avec hreflang
- Page d'accueil + variantes FR/EN/ES
- Changefreq: daily
- Priority: 1.0 (homepage), 0.9 (langues)

**Structure sitemap** :
```xml
<url>
  <loc>https://xocoa-sommelier.com</loc>
  <xhtml:link rel="alternate" hreflang="fr" href="https://xocoa-sommelier.com?lang=fr"/>
  <xhtml:link rel="alternate" hreflang="en" href="https://xocoa-sommelier.com?lang=en"/>
  <xhtml:link rel="alternate" hreflang="es" href="https://xocoa-sommelier.com?lang=es"/>
</url>
```

### Pages SEO statiques (V7.5)

**4 pages éditoriales riches** pour améliorer le référencement organique et générer du trafic qualifié :

#### 1. Chocolats de Madagascar (`/chocolats-madagascar`)
**Objectif** : Capter le trafic "chocolat Madagascar", "chocolat Sambirano", "cacao malgache"

**Contenu** (600+ mots) :
- Terroir d'exception de la vallée de Sambirano
- Profil aromatique unique (fruité, acidulé)
- Variété Trinitario et notes de dégustation
- Chocolatiers de référence (Åkesson's, Madécasse, Pralus, Valrhona Manjari)
- Conseils de dégustation et accords

**SEO** :
- Title: "Chocolats de Madagascar | Les Meilleurs Chocolats Malgaches Premium"
- Meta description optimisée
- Schema.org WebPage + Product
- Open Graph complet
- Keywords: chocolat Madagascar, Sambirano, Trinitario, chocolat fruité

#### 2. Chocolats Bio et Équitables (`/chocolats-bio-equitables`)
**Objectif** : Capter "chocolat bio", "chocolat équitable", "fair trade chocolate"

**Contenu** (700+ mots) :
- Pourquoi choisir bio et équitable
- Certifications principales (Fair Trade, Organic, Rainforest Alliance, B-Corp, Direct Trade)
- Marques engagées (Alter Eco, Ethiquable, Tony's Chocolonely)
- Qualité gustative des chocolats certifiés
- Impact environnemental et social

**SEO** :
- Title: "Chocolats Bio et Équitables | Guide Fair Trade & Organic 2025"
- Schema.org Article
- Keywords: chocolat bio, chocolat équitable, commerce équitable, organic chocolate

#### 3. Bean-to-Bar (`/bean-to-bar`)
**Objectif** : Capter "bean to bar", "chocolat artisanal", "fabrication chocolat"

**Contenu** (650+ mots) :
- Définition et philosophie bean-to-bar
- 8 étapes de fabrication détaillées (sélection, fermentation, torréfaction, conching...)
- Pourquoi choisir bean-to-bar
- Top chocolatiers (Friis-Holm, Bonnat, Pump Street, Dick Taylor)
- Bean-to-bar vs Tree-to-bar

**SEO** :
- Title: "Bean-to-Bar | Qu'est-ce que le Chocolat Bean-to-Bar Artisanal ?"
- Schema.org Article
- Keywords: bean to bar, chocolat artisanal, fabrication chocolat, chocolatier artisan

#### 4. Chocolats Primés (`/chocolats-primes`)
**Objectif** : Capter "chocolat primé", "meilleur chocolat", "awards chocolat"

**Contenu** (700+ mots) :
- Concours internationaux majeurs (ICA, Academy of Chocolate, Great Taste, Good Food Awards)
- Critères d'évaluation professionnels
- Chocolatiers multi-primés (Friis-Holm, Pacari, Amedei, Bonnat)
- Comment lire les médailles
- Tendances 2025 des chocolats primés

**SEO** :
- Title: "Chocolats Primés | Les Meilleurs Chocolats du Monde 2025"
- Schema.org Article
- Keywords: chocolat primé, meilleur chocolat, International Chocolate Awards, chocolat médaillé

**Caractéristiques communes** :
- ✅ **Contenu riche** : 500-700 mots par page
- ✅ **Structure optimisée** : H1 > H2 > H3 > listes
- ✅ **Breadcrumb navigation** : Accueil > Page actuelle
- ✅ **CTA interne** : "Consulter le Sommelier" (lien vers /)
- ✅ **Design cohérent** : Sulphur Point, palette vert/brun/blanc
- ✅ **Mobile-responsive** : Design adaptatif
- ✅ **Meta tags complets** : Title, description, keywords, OG, Schema.org

**Impact SEO attendu** :
- 🎯 **Longue traîne** : Capture de requêtes spécifiques (3-5 mots)
- 🎯 **Autorité thématique** : Positionnement expert chocolat premium
- 🎯 **Taux de rebond** : Contenu éditorial réduit le bounce rate
- 🎯 **Conversions** : Chaque page dirige vers le sommelier IA

### Prochaines étapes SEO

1. **Soumission aux moteurs de recherche** :
   - Google Search Console : https://search.google.com/search-console
   - Bing Webmaster Tools
   - Soumettre sitemap.xml

2. **Backlinks et contenu** :
   - Articles de blog sur le chocolat
   - Partenariats avec chocolatiers
   - Présence réseaux sociaux

3. **Image OG** :
   - Créer `/public/og-image.jpg` (1200x630px)
   - Affichage sur Facebook, Twitter, LinkedIn

## Architecture des fichiers

### Structure finale (nettoyée)
```
SOMMELIER/
├── data/                              # Bases de données
│   ├── chocolates.json               # Base principale (106 champs)
│   ├── chocolates_en.json            # 2129 chocolats en anglais (8.8 MB)
│   ├── chocolates_fr.json            # 2129 chocolats en français (8.9 MB)
│   ├── chocolates_es.json            # 2129 chocolats en espagnol (8.8 MB)
│   ├── filters.json                  # Filtres et taxonomies dynamiques
│   └── chocolates_database.xlsx     # Source Excel originale
├── public/                           # Assets statiques
│   ├── chocolates_en.json           # Copie pour Netlify Functions
│   ├── chocolates_fr.json           # Copie pour Netlify Functions
│   ├── chocolates_es.json           # Copie pour Netlify Functions
│   ├── filters.json                 # Copie pour Netlify Functions
│   ├── robots.txt                   # Configuration SEO crawlers
│   └── sitemap.xml                  # Sitemap multilingue
├── src/
│   ├── components/                  # Composants React
│   │   ├── Chat/                   # Interface conversationnelle
│   │   ├── Recommendations/        # Affichage chocolats
│   │   ├── SEO/                    # SEOHead multilingue
│   │   ├── UI/                     # Header, layout
│   │   └── LanguageSelector/       # Sélecteur FR/EN/ES
│   ├── contexts/
│   │   └── LanguageContext.js      # Gestion langue globale
│   ├── services/
│   │   └── smart-hybrid-sommelier.cjs  # Moteur IA principal
│   ├── translations/
│   │   └── translations.js         # Traductions UI (FR/EN/ES)
│   ├── utils/
│   │   ├── dataObfuscation.cjs     # Obfuscation anti-scraping
│   │   ├── supabase.cjs            # Client Supabase (Netlify Functions)
│   │   └── supabase.js             # Client Supabase (Frontend - optionnel)
│   └── pages/                      # Pages Next.js
│       ├── index.js                # Page d'accueil (Sommelier IA)
│       ├── chocolats-madagascar.js # SEO: Chocolats de Madagascar
│       ├── chocolats-bio-equitables.js # SEO: Bio & Fair Trade
│       ├── bean-to-bar.js          # SEO: Bean-to-Bar artisanal
│       └── chocolats-primes.js     # SEO: Chocolats primés
├── netlify/
│   └── functions/
│       ├── chat.js                 # API principale multilingue + logging Supabase
│       └── weekly-report.js        # Rapports email Supabase → SMTP
├── scripts/
│   ├── translate-database.js       # Script traduction GPT-4o (FR/ES)
│   ├── regenerate-from-excel.js    # Extraction complète depuis Excel (106 champs)
│   └── add-websites-to-translations.js  # Copie maker_website entre langues
├── Documents techniques/            # Documentation
│   ├── ARCHITECTURE_TECHNIQUE.md   # Documentation technique complète
│   └── SUPABASE_SETUP.md           # Guide setup Supabase & SMTP
├── TRASH/                          # Fichiers obsolètes déplacés
└── [config files]                  # package.json, netlify.toml, etc.
```

## Métriques et performances

### Base de données
- **Taille totale** : ~26.5 MB (3 langues × 8.8 MB)
- **Chocolats** : 2129 entrées par langue
- **Champs** : 106 par chocolat
- **Champs traduits** : 4 (tasting_notes, expert_review, flavor_notes)
- **Langues** : 3 (FR, EN, ES)
- **Awards** : 984 chocolats avec distinctions
- **Sites fabricants** : 1414 liens vers fabricants (66.4% couverture)

### Filtres et taxonomies
- **Pays origine** : 23
- **Régions origine** : 154
- **Pays fabricants** : 16
- **Saveurs** : 485+
- **Awards types** : 20
- **Accords** : 7 catégories (vins, spiritueux, cafés, thés, fromages, fruits, noix)

### Performance IA
- **Temps moyen** : 2-4 secondes par interaction
- **Modèles utilisés** :
  - GPT-4o (extraction critères - 35 critères supportés)
  - GPT-3.5-turbo (décisions conversationnelles)
  - GPT-4o-mini (traductions économiques espagnol)
- **Coût optimisé** :
  - Tokens limités, pas de traduction temps réel
  - Traduction ES : $0.03 (200x moins cher que FR)
- **Latence bases** : 0ms (pré-traduites)
- **Critères supportés** : 35 types de filtres (+8 nouveaux)
- **Filtres actifs frontend** : 19/98 champs (19% couverture, +73% vs avant)

### Sécurité
- **Rate limiting** : 10 requêtes/minute par IP
- **Obfuscation** : Prix ±2%, synonymes dans avis
- **Validation** : Headers, User-Agent, origine
- **Logs** : IP, critères recherche, langue, résultats

### Analytics (Supabase)
- **Stockage** : Supabase PostgreSQL (historique permanent)
- **Événements** : connection, search, blocked (avec IP, User-Agent, critères)
- **Rapport hebdomadaire** : Samedi 9h GMT via email HTML
- **Tracking** : Connexions, recherches, langues, critères populaires, visiteurs uniques, requêtes bloquées
- **Destinataire** : julien@bonplein.fr
- **Requêtes SQL** : Dashboard Supabase pour analyses avancées
- **Gratuit** : Plan Supabase gratuit (500MB) suffisant

---

## Historique des versions

### V7.5 - Octobre 2025
**Analytics persistant Supabase & Pages SEO statiques** :

- 📊 **Système analytics Supabase** :
  - **Table `analytics_logs`** : Stockage PostgreSQL permanent (vs Netlify 24-48h)
  - **3 types d'événements** : connection, search, blocked
  - **Données loggées** : IP, User-Agent, Referer, langue, critères complets, nombre de résultats
  - **Client Supabase** : `src/utils/supabase.cjs` (Functions) + `supabase.js` (Frontend optionnel)
  - **Logging non-bloquant** : Async catch pour ne pas ralentir l'API
  - **Gratuit** : Plan Supabase gratuit (500MB) largement suffisant

- 📧 **Rapports hebdomadaires V2** (Supabase → Email) :
  - **Réécriture complète** `weekly-report.js`
  - **Source** : Requêtes SQL Supabase au lieu d'in-memory
  - **Email HTML élégant** : Style Sulphur Point, tableau structuré
  - **Stats** : Connexions, recherches, visiteurs uniques, blocages, langues, top 10 critères
  - **Insights automatiques** : Langue dominante, critère populaire, taux d'engagement
  - **Configuration SMTP** : Gmail App Passwords ou SendGrid
  - **Planification** : Samedi 9h GMT (netlify.toml)

- 🌐 **4 pages SEO statiques** (1499 lignes de code) :
  - `/chocolats-madagascar` : Terroir Sambirano, profil fruité, Trinitario (600 mots)
  - `/chocolats-bio-equitables` : Certifications Fair Trade, Organic, impact social (700 mots)
  - `/bean-to-bar` : 8 étapes de fabrication, philosophie artisanale (650 mots)
  - `/chocolats-primes` : Concours internationaux ICA, Academy of Chocolate (700 mots)
  - **Meta tags complets** : Title, description, keywords, Open Graph, Schema.org
  - **Breadcrumb navigation** : Accueil › Page actuelle
  - **CTA interne** : Bouton "Consulter le Sommelier" vers /
  - **Design cohérent** : Sulphur Point, palette vert/brun/blanc
  - **Mobile-responsive** : Grid adaptatif

- 📝 **Documentation** :
  - `SUPABASE_SETUP.md` : Guide complet setup Supabase + SMTP (199 lignes)
  - `ARCHITECTURE_TECHNIQUE.md` : Mise à jour V7.5 avec analytics et SEO
  - SQL queries exemples pour analytics Supabase
  - Instructions troubleshooting complètes

**Variables d'environnement ajoutées** :
```
SUPABASE_URL, SUPABASE_SERVICE_KEY, NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY
SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, REPORT_EMAIL_FROM, REPORT_EMAIL_TO
```

**Fichiers créés/modifiés** :
- NEW: `src/utils/supabase.cjs`, `supabase.js`
- NEW: `src/pages/chocolats-madagascar.js`, `chocolats-bio-equitables.js`, `bean-to-bar.js`, `chocolats-primes.js`
- NEW: `Documents techniques/SUPABASE_SETUP.md`
- MODIFIED: `netlify/functions/chat.js` (logging Supabase)
- MODIFIED: `netlify/functions/weekly-report.js` (réécriture complète)
- MODIFIED: `.env.local`, `.env.example`

**Impact** :
- ✅ **Analytics historique permanent** : Plus de perte de données
- ✅ **Rapports automatisés fiables** : Email hebdomadaire avec stats détaillées
- ✅ **SEO amélioré** : 4 pages riches ciblant longue traîne
- ✅ **Trafic organique** : Capture de requêtes spécifiques (Madagascar, bio, bean-to-bar, primés)
- ✅ **Analyses avancées** : Requêtes SQL personnalisées dans Supabase dashboard

### V7.4 - Octobre 2025
**Refonte complète du design graphique** :
- 🎨 **Nouvelle charte graphique** :
  - **Logo** : LOGO_SOMMELIER_FOND_BLANC_COULEURS.png (260px) sur fond clair
  - **Palette de couleurs** :
    - Primaire : Vert sommelier `#2D8B7F`
    - Secondaire : Brun chocolat `#3D2817`
    - Fond principal : Crème clair `#F5F5F0`
    - Fond cartes : Blanc `#FFFFFF`
    - Fond messages utilisateur : Noir `#1A1A1A`
    - Fond headers cards : Noir `#1A1A1A` (vs brun avant)
  - **Typographie** : Police Sulphur Point (Light 300, Regular 400, Bold 700)
    - Remplace Inter pour une identité visuelle unique
    - Fichiers : SulphurPoint-Light.ttf, SulphurPoint-Regular.ttf, SulphurPoint-Bold.ttf

- 🎨 **Cartes de recommandation (PremiumChocolateCard)** :
  - **Système accordion** : Cards repliables/dépliables au clic sur header
  - **Header noir (#1A1A1A)** avec texte blanc et chevron animé
  - **Corps blanc** avec sections structurées
  - **Grid 2 colonnes** sur desktop (lg:grid-cols-2)
  - **Espacement optimisé** :
    - Gap entre cards : 1.25rem (gap-5)
    - Padding header : 1rem
    - Padding sections : 0.75rem
    - Margin sections : 0.5rem
  - **Alignement** : maxWidth 1200px centré (aligné avec FixedChatInput)
  - **Typographie compacte** :
    - Titres sections : 0.95rem
    - Texte corps : 0.85rem
    - Line-height : 1.5

- 🎨 **Header application** :
  - Logo centré 260px sans bordures
  - Fond clair harmonisé avec page
  - Suppression bordure verte du bas
  - Suppression marge entre logo et zone de chat

- 🎨 **Messages et interface** :
  - Messages sommelier : Fond blanc avec bordure verte `#2D8B7F`
  - Messages utilisateur : Fond noir `#1A1A1A`
  - Input fixe : Bordure verte, fond blanc
  - Bouton Envoyer : Noir `#1A1A1A`

- 🧹 **Nettoyage fichiers** :
  - Suppression .DS_Store (fichiers système macOS)
  - Suppression translation.log (fichier temporaire)
  - Suppression logos en double (public/images/)
  - Suppression ancien logo (logo-Sommelier.png)
  - Suppression anciennes polices (Hellix-Regular.woff2, ProximaNova-Regular.woff2)
  - Tous les fichiers obsolètes déplacés dans TRASH/

**Fichiers modifiés** :
- `src/components/UI/Header.js` : Nouveau logo, suppression bordure
- `src/components/Chat/ChatInterface.js` : Suppression marge haute
- `src/components/Recommendations/PremiumChocolateCard.js` : Accordion, couleurs, espacement
- `src/components/Recommendations/ChocolateRecommendations.js` : Grid 2 col, alignement 1200px
- `src/styles/globals.css` : Nouvelle charte graphique Sulphur Point

**Impact UX** :
- Design moderne et professionnel inspiré des sommeliers
- Identité visuelle cohérente (vert/brun/blanc)
- Meilleure lisibilité avec headers noirs contrastés
- Expérience utilisateur optimisée (accordion, espacement)
- Performance améliorée (cards compactes, chargement rapide)

### V7.3 - Octobre 2025
**Corrections système multilingue** :
- 🔧 **Fix architecture multilingue (FR/EN/ES)** :
  - Chaque langue charge sa propre base de données (chocolates_fr.json, chocolates_en.json, chocolates_es.json)
  - Suppression de la traduction intermédiaire vers l'anglais
  - Trois cas séparés explicitement : FR / EN / ES
  - `getFilterKeys()`: Retourne valeurs dans la langue actuelle dynamiquement
  - `resolveSynonym()`: Résout synonymes dans la langue actuelle (ex: "bio" → "Biologique" en FR)

- 🤖 **Prompt GPT-4o multilingue** :
  - Instructions spécifiques selon langue (🇫🇷 FR / 🇬🇧 EN / 🇪🇸 ES)
  - Valeurs de filtres générées dynamiquement via `getFilterKeys()`
  - Suppression de tous les exemples hardcodés de synonymes
  - GPT-4o reçoit et retourne valeurs dans la langue de l'utilisateur

- 🎨 **Fix lisibilité cartes** :
  - Fond de carte : `rgba(26, 26, 26, 0.8)` (gris foncé comme boutons langue)
  - Bordures : `rgba(139, 111, 78, 0.3)` (or subtil)
  - Texte principal : `#FFFFFF` (blanc)
  - Texte secondaire : `#A0A0A0` (gris clair)
  - Correction du problème blanc sur blanc

**Fichiers modifiés** :
- `src/services/smart-hybrid-sommelier.cjs` : Architecture multilingue complète
- `src/components/Recommendations/PremiumChocolateCard.js` : Couleurs définies

**Impact** :
- Système multilingue fonctionnel sans traduction intermédiaire
- Synonymes gérés automatiquement par langue
- Cartes lisibles avec bon contraste

### V7.2 - Octobre 2025
**Design minimaliste** :
- 🎨 **Refonte graphique complète** : Esthétique minimaliste sobre et élégante
- 🎨 **Palette de couleurs** :
  - Fond principal : Crème clair `#EBEAE4` (vs noir `#0A0A0A`)
  - Messages sommelier : Gris foncé `#8C867F` avec bordure dorée
  - Messages utilisateur : Noir `#1A1A1A`
  - Accent : Or mat `#C9A05F`
- 🎨 **Typographie affinée** :
  - Police unique : Inter weight 300 (légère et raffinée)
  - Taille réduite : 0.875rem (14px) pour plus de finesse
- 🎨 **Design épuré** :
  - Suppression des avatars "S" et "U"
  - Suppression de tous les border-radius (design plat)
  - Suppression des gradients et effets
  - Marges élégantes de 2rem sur les messages
- 🎨 **Logo** :
  - Nouveau logo "Le Sommelier by Xocoa" (200px, centré)
  - Copié depuis `/XOCOA/LOGO/logo-Sommelier 3.png`
- 🎨 **Input épuré** :
  - Fond gris foncé `#8C867F` (vs noir)
  - Bordure dorée simple sans effets
  - Hauteur réduite : 100px (vs 120px)

**Impact UX** :
- Design luxueux et sobre inspiré des marques premium
- Focus sur le contenu et la lisibilité
- Identité visuelle cohérente et moderne

### V7.1 - Octobre 2025
**Corrections critiques** :
- 🐛 **Fix PremiumChocolateCard** : Ajout affichage `tasting_notes` et `maker_website` (étaient absents)
- 🐛 **Fix liens fabricants** : Liens cliquables avec icône externe sur le nom du brand
- 🔧 **Optimisation performance** : Suppression logs debug qui ralentissaient le rendering (847+ cartes)
- 🧹 **Nettoyage codebase** : Déplacement fichiers obsolètes vers TRASH/
- 📊 **Logs utilisateur optimisés** : Conservation uniquement des logs de tracking essentiels

**Fichiers nettoyés** :
- `netlify/functions/chat-old.js`, `chat.js.backup`
- `src/components/Chat/ChatInput.js` (remplacé par FixedChatInput)
- `src/services/smart-hybrid-sommelier*.backup`

### V7 - Octobre 2025
**Améliorations majeures** :
- ✅ **8 nouveaux filtres** : dietary, production_craft_level, finish_character, finish_length, texture_melt, has_awards, production_method, serving_occasion
- ✅ **Couverture filtres** : 11 → 19 champs (+73%)
- ✅ **Traduction économique** : Méthode dictionnaire GPT-4o-mini pour ES (200x moins cher)
- ✅ **Filtres multilingues** : Architecture unifiée avec un seul filters.json
- ✅ **User choice logging** : Tracking complet des 19 filtres utilisateurs
- ✅ **Critères IA** : 27 → 35 critères supportés par GPT-4o

**Coûts de traduction** :
- Français (GPT-4o) : $6.00 / 2129 chocolats
- Espagnol (GPT-4o-mini + dictionnaire) : $0.03 / 2129 chocolats (économie de 99.5%)

### V6 - Octobre 2025
*Système multilingue complet FR/EN/ES + amélioration IA avec 27 critères*

---

*Document technique - Version V7.5 - Octobre 2025*
*Dernière mise à jour : Analytics persistant Supabase + 4 pages SEO statiques (Madagascar, Bio/Fair Trade, Bean-to-Bar, Primés)*
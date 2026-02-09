# 📊 Configuration Supabase & Analytics

Ce guide explique comment configurer le système d'analytics persistant avec Supabase et les rapports hebdomadaires par email.

## ✅ Étapes Complétées

1. ✅ Compte Supabase créé
2. ✅ Table `analytics_logs` créée dans Supabase
3. ✅ Code modifié pour logger vers Supabase
4. ✅ Système de rapports hebdomadaires implémenté

## 🔧 Configuration Netlify

### 1. Variables d'environnement à ajouter

Allez dans **Netlify Dashboard** → Votre projet → **Site configuration** → **Environment variables** → **Add a variable**

Ajoutez les variables suivantes :

#### Supabase (obligatoire pour analytics)
```
SUPABASE_URL=https://eqrocnxcvrpgjyzncrgz.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVxcm9jbnhjdnJwZ2p5em5jcmd6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTkxNTUwMiwiZXhwIjoyMDc3NDkxNTAyfQ.6rZ4zXhxMkUeyerPaPps4-6zdvefWr628gDCsGHwcYU
```

#### SMTP Gmail (optionnel - pour rapports hebdomadaires)

**Configuration Gmail :**

1. **Activer l'authentification à 2 facteurs** sur votre compte Gmail
2. **Générer un mot de passe d'application** :
   - Allez sur https://myaccount.google.com/security
   - Cliquez sur "2-Step Verification"
   - Scroll down to "App passwords"
   - Sélectionnez "Mail" et "Other (custom name)" → "XOCOA Sommelier"
   - Copiez le mot de passe généré (16 caractères)

3. **Ajoutez ces variables dans Netlify** :
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=votre-email@gmail.com
SMTP_PASS=xxxx xxxx xxxx xxxx  (mot de passe d'application)
REPORT_EMAIL_FROM=noreply@xocoa-sommelier.com
REPORT_EMAIL_TO=julien@bonplein.fr
```

### 2. Redéployer sur Netlify

Après avoir ajouté les variables d'environnement :

```bash
git add .
git commit -m "Add Supabase analytics and weekly reports"
git push origin main
```

Netlify redéploiera automatiquement avec les nouvelles variables.

## 📧 Rapports Hebdomadaires

### Configuration

Les rapports sont envoyés **automatiquement chaque samedi à 9h00 GMT**.

Configuration dans `netlify.toml` :
```toml
[functions."weekly-report"]
  schedule = "0 9 * * 6"  # Samedi 9h00 GMT
```

### Contenu du rapport

- **Statistiques globales** : Connexions, recherches, visiteurs uniques, requêtes bloquées
- **Répartition linguistique** : FR/EN/ES avec pourcentages
- **Top 10 critères** : Les filtres les plus utilisés
- **Insights automatiques** : Langue dominante, taux d'engagement, etc.

### Tester manuellement

Pour tester l'envoi d'email sans attendre samedi :

```bash
# En local (nécessite les variables SMTP configurées)
curl -X POST http://localhost:8888/.netlify/functions/weekly-report

# En production
curl -X POST https://xocoasommelier.netlify.app/.netlify/functions/weekly-report
```

## 📊 Consulter les Analytics

### Dans Supabase

1. Allez sur https://supabase.com/dashboard
2. Sélectionnez votre projet
3. Cliquez sur "Table Editor" dans le menu gauche
4. Sélectionnez la table `analytics_logs`
5. Vous verrez tous les events loggés en temps réel

### Requêtes SQL utiles

#### Connexions des dernières 24h
```sql
SELECT COUNT(*) as connections, COUNT(DISTINCT ip_address) as unique_ips
FROM analytics_logs
WHERE event_type = 'connection'
  AND created_at > NOW() - INTERVAL '24 hours';
```

#### Top critères de recherche (7 derniers jours)
```sql
SELECT
  jsonb_object_keys(criteria) as criterion,
  COUNT(*) as count
FROM analytics_logs
WHERE event_type = 'search'
  AND created_at > NOW() - INTERVAL '7 days'
GROUP BY criterion
ORDER BY count DESC
LIMIT 10;
```

#### Répartition par langue
```sql
SELECT
  language,
  COUNT(*) as searches,
  ROUND(COUNT(*)::numeric / SUM(COUNT(*)) OVER () * 100, 2) as percentage
FROM analytics_logs
WHERE event_type = 'search'
  AND created_at > NOW() - INTERVAL '7 days'
GROUP BY language;
```

## 🔍 Types d'événements loggés

| Event Type | Description | Données |
|------------|-------------|---------|
| `connection` | Nouvelle connexion à l'API | IP, User-Agent, Referer |
| `search` | Recherche de chocolat effectuée | IP, Langue, Critères complets, Nombre de résultats |
| `blocked` | Requête bloquée (rate limit ou headers invalides) | IP, Raison du blocage |

## 🔒 Sécurité

- ⚠️ **Service Role Key** : Ne JAMAIS exposer côté client, uniquement dans Netlify Functions
- ✅ **Anon Public Key** : Peut être utilisé côté client (RLS activé)
- ✅ **Row Level Security (RLS)** : Activé sur la table analytics_logs
- ✅ **Policies** : Service role a tous les droits, anon peut uniquement INSERT

## 🐛 Troubleshooting

### Les logs n'apparaissent pas dans Supabase

1. Vérifiez que `SUPABASE_URL` et `SUPABASE_SERVICE_KEY` sont bien configurés dans Netlify
2. Vérifiez les logs Netlify Functions → `chat` → Recent invocations
3. Cherchez "✅ Logged ... event to Supabase" ou "❌ Supabase insert error"

### Les emails ne sont pas envoyés

1. Vérifiez que toutes les variables `SMTP_*` sont configurées
2. Vérifiez que le mot de passe d'application Gmail est correct
3. Testez manuellement avec curl (voir ci-dessus)
4. Vérifiez les logs Netlify Functions → `weekly-report` → Recent invocations

### "SMTP credentials not configured"

Les variables SMTP ne sont pas dans Netlify. Suivez la section "Configuration Gmail" ci-dessus.

## 📈 Prochaines Étapes (Optionnel)

### Dashboard Supabase personnalisé

Vous pouvez créer un dashboard dans Supabase pour visualiser vos analytics :

1. Allez dans "Database" → "Functions"
2. Créez des vues SQL pour agrégations
3. Utilisez "Charts" pour créer des graphiques

### Alertes personnalisées

Modifiez `weekly-report.js` pour envoyer des alertes si :
- Nombre de requêtes bloquées trop élevé
- Taux d'engagement en baisse
- Langue inattendue dominante

## 🎯 Résumé

✅ **Analytics persistants** : Tous les events sont maintenant stockés dans Supabase
✅ **Historique complet** : Pas de perte de données (Netlify logs = 24-48h, Supabase = ∞)
✅ **Rapports automatiques** : Email hebdomadaire chaque samedi à 9h
✅ **Requêtes SQL** : Analyses avancées possibles dans Supabase
✅ **Gratuit** : Plan gratuit Supabase (500MB) suffit largement

---

📧 **Contact** : julien@bonplein.fr
🚀 **XOCOA Sommelier** : https://xocoasommelier.netlify.app

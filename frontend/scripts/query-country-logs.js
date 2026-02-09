/**
 * Query Supabase for searches with country/flavor/interesting criteria
 */

const { createClient } = require('@supabase/supabase-js')

const supabaseUrl = 'https://eqrocnxcvrpgjyzncrgz.supabase.co'
const supabaseServiceKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVxcm9jbnhjdnJwZ2p5em5jcmd6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTkxNTUwMiwiZXhwIjoyMDc3NDkxNTAyfQ.6rZ4zXhxMkUeyerPaPps4-6zdvefWr628gDCsGHwcYU'

const supabase = createClient(supabaseUrl, supabaseServiceKey)

async function queryInterestingLogs() {
  try {
    // Get all search logs
    const { data, error } = await supabase
      .from('analytics_logs')
      .select('*')
      .eq('event_type', 'search')
      .order('created_at', { ascending: false })
      .limit(100)

    if (error) {
      console.error('❌ Error fetching logs:', error)
      return
    }

    console.log(`\n📊 Total search logs: ${data.length}\n`)

    // Categorize logs
    const categories = {
      withCountry: [],
      withFlavors: [],
      withTexture: [],
      withPrice: [],
      withAwards: [],
      withCertification: [],
      other: []
    }

    data.forEach(log => {
      const criteria = log.criteria || {}

      if (criteria.origin_country || criteria.maker_country) {
        categories.withCountry.push(log)
      } else if (criteria.flavor_keywords && criteria.flavor_keywords.length > 0) {
        categories.withFlavors.push(log)
      } else if (criteria.texture) {
        categories.withTexture.push(log)
      } else if (criteria.price_min || criteria.price_max) {
        categories.withPrice.push(log)
      } else if (criteria.awards) {
        categories.withAwards.push(log)
      } else if (criteria.certification) {
        categories.withCertification.push(log)
      } else {
        categories.other.push(log)
      }
    })

    console.log('📈 STATISTICS:')
    console.log(`  🌍 With countries: ${categories.withCountry.length}`)
    console.log(`  🍫 With flavors: ${categories.withFlavors.length}`)
    console.log(`  ✨ With texture: ${categories.withTexture.length}`)
    console.log(`  💰 With price: ${categories.withPrice.length}`)
    console.log(`  🏆 With awards: ${categories.withAwards.length}`)
    console.log(`  ✅ With certification: ${categories.withCertification.length}`)
    console.log(`  📦 Other criteria: ${categories.other.length}`)

    // Display country logs
    if (categories.withCountry.length > 0) {
      console.log(`\n\n🌍 SEARCHES WITH COUNTRIES (${categories.withCountry.length}):\n`)
      categories.withCountry.forEach((log, idx) => {
        console.log(`--- Search ${idx + 1} ---`)
        console.log(`Date: ${new Date(log.created_at).toLocaleString('fr-FR')}`)
        console.log(`Language: ${log.language}`)
        console.log(`Results: ${log.results_count}`)
        console.log(`Origin country: ${log.criteria.origin_country || '-'}`)
        console.log(`Maker country: ${log.criteria.maker_country || '-'}`)
        console.log(`Other criteria:`, Object.entries(log.criteria)
          .filter(([key, value]) =>
            key !== 'origin_country' &&
            key !== 'maker_country' &&
            value !== null &&
            value !== undefined &&
            (Array.isArray(value) ? value.length > 0 : true)
          )
          .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
          .join(', ')
        )
        console.log('')
      })
    }

    // Display flavor logs
    if (categories.withFlavors.length > 0) {
      console.log(`\n\n🍫 SEARCHES WITH FLAVORS (${categories.withFlavors.length}):\n`)
      categories.withFlavors.forEach((log, idx) => {
        console.log(`--- Search ${idx + 1} ---`)
        console.log(`Date: ${new Date(log.created_at).toLocaleString('fr-FR')}`)
        console.log(`Language: ${log.language}`)
        console.log(`Results: ${log.results_count}`)
        console.log(`Flavors: ${log.criteria.flavor_keywords.join(', ')}`)
        console.log(`Texture: ${log.criteria.texture || '-'}`)
        console.log('')
      })
    }

    // Display recent logs (last 10)
    console.log(`\n\n📋 LAST 10 SEARCHES:\n`)
    data.slice(0, 10).forEach((log, idx) => {
      console.log(`${idx + 1}. ${new Date(log.created_at).toLocaleString('fr-FR')} | Lang: ${log.language} | Results: ${log.results_count}`)
      console.log(`   Criteria:`, JSON.stringify(log.criteria, null, 2).substring(0, 200))
      console.log('')
    })

  } catch (error) {
    console.error('❌ Failed to query logs:', error.message)
  }
}

queryInterestingLogs()

/**
 * Query Supabase logs for specific criteria
 */

const { createClient } = require('@supabase/supabase-js')

const supabaseUrl = 'https://eqrocnxcvrpgjyzncrgz.supabase.co'
const supabaseServiceKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVxcm9jbnhjdnJwZ2p5em5jcmd6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTkxNTUwMiwiZXhwIjoyMDc3NDkxNTAyfQ.6rZ4zXhxMkUeyerPaPps4-6zdvefWr628gDCsGHwcYU'

const supabase = createClient(supabaseUrl, supabaseServiceKey)

async function queryLogs() {
  try {
    // Get all search logs
    const { data, error } = await supabase
      .from('analytics_logs')
      .select('*')
      .eq('event_type', 'search')
      .order('created_at', { ascending: false })
      .limit(50)

    if (error) {
      console.error('Error fetching logs:', error)
      return
    }

    console.log(`\n📊 Found ${data.length} search logs:\n`)

    // Filter logs with country criteria
    const logsWithCountries = data.filter(log => {
      const criteria = log.criteria || {}
      return criteria.origin_country || criteria.maker_country
    })

    console.log(`🌍 Logs with country criteria: ${logsWithCountries.length}\n`)

    logsWithCountries.forEach((log, idx) => {
      console.log(`\n--- Log ${idx + 1} ---`)
      console.log(`Timestamp: ${log.timestamp}`)
      console.log(`Language: ${log.language}`)
      console.log(`Results: ${log.results_count}`)
      console.log(`Criteria:`, JSON.stringify(log.criteria, null, 2))
    })

    // All search logs (with any criteria)
    console.log(`\n\n📋 All search logs:\n`)
    data.forEach((log, idx) => {
      console.log(`\n--- Search ${idx + 1} ---`)
      console.log(`Timestamp: ${log.timestamp}`)
      console.log(`Language: ${log.language}`)
      console.log(`Results: ${log.results_count}`)
      console.log(`Criteria:`, JSON.stringify(log.criteria, null, 2))
    })

  } catch (error) {
    console.error('Failed to query logs:', error.message)
  }
}

queryLogs()

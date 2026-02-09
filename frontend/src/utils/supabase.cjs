/**
 * Supabase Client Configuration (CommonJS for Netlify Functions)
 *
 * Used for logging analytics data persistently
 */

const { createClient } = require('@supabase/supabase-js')

const supabaseUrl = process.env.SUPABASE_URL
const supabaseServiceKey = process.env.SUPABASE_SERVICE_KEY

// Client for Netlify Functions (uses service role key for full access)
// Only create client if env vars are present to avoid errors
const supabase = supabaseUrl && supabaseServiceKey
  ? createClient(supabaseUrl, supabaseServiceKey)
  : null

if (!supabase) {
  console.error('❌ Missing Supabase environment variables for Netlify functions (SUPABASE_URL, SUPABASE_SERVICE_KEY)')
}

/**
 * Log an analytics event to Supabase
 * @param {string} eventType - Type of event: 'connection', 'search', 'user_choice', 'blocked'
 * @param {object} data - Event data
 */
async function logAnalytics(eventType, data) {
  if (!supabase) return false

  try {
    const logEntry = {
      event_type: eventType,
      timestamp: new Date().toISOString(),
      ip_address: data.ip || null,
      user_agent: data.userAgent || null,
      referer: data.referer || null,
      language: data.language || null,
      criteria: data.criteria || null,
      results_count: typeof data.resultsCount === 'number' ? data.resultsCount : null,
      metadata: data.metadata || null
    }

    const { error } = await supabase
      .from('analytics_logs')
      .insert([logEntry])

    if (error) {
      console.error('❌ Supabase insert error:', error.message)
      return false
    }

    return true
  } catch (error) {
    console.error('❌ Failed to log analytics:', error.message)
    return false
  }
}

/**
 * Get analytics data for a date range
 * @param {Date} startDate - Start date
 * @param {Date} endDate - End date
 * @returns {Promise<Array>} Analytics logs
 */
async function getAnalytics(startDate, endDate) {
  if (!supabase) return []

  try {
    const { data, error } = await supabase
      .from('analytics_logs')
      .select('*')
      .gte('created_at', startDate.toISOString())
      .lte('created_at', endDate.toISOString())
      .order('created_at', { ascending: false })

    if (error) {
      console.error('❌ Error fetching analytics:', error.message)
      return []
    }

    return data || []
  } catch (error) {
    console.error('❌ Failed to fetch analytics:', error.message)
    return []
  }
}

/**
 * Get aggregated weekly statistics
 * @param {Date} startDate - Start of week
 * @param {Date} endDate - End of week
 * @returns {Promise<object>} Aggregated stats
 */
async function getWeeklyStats(startDate, endDate) {
  if (!supabase) return null

  try {
    const logs = await getAnalytics(startDate, endDate)

    if (!logs || logs.length === 0) {
      return {
        totalConnections: 0,
        totalSearches: 0,
        totalBlocked: 0,
        uniqueIPs: 0,
        languageBreakdown: { fr: 0, en: 0, es: 0 },
        criteriaCount: {},
        topCriteria: []
      }
    }

    // Aggregate statistics
    const stats = {
      totalConnections: logs.filter(l => l.event_type === 'connection').length,
      totalSearches: logs.filter(l => l.event_type === 'search').length,
      totalBlocked: logs.filter(l => l.event_type === 'blocked').length,
      uniqueIPs: new Set(logs.map(l => l.ip_address).filter(Boolean)).size,
      languageBreakdown: {
        fr: logs.filter(l => l.language === 'fr').length,
        en: logs.filter(l => l.language === 'en').length,
        es: logs.filter(l => l.language === 'es').length
      },
      criteriaCount: {},
      topCriteria: []
    }

    // Count criteria usage
    logs
      .filter(l => l.event_type === 'search' && l.criteria)
      .forEach(log => {
        const criteria = log.criteria
        Object.keys(criteria).forEach(key => {
          if (criteria[key] && key !== 'conversationCategories' && key !== 'searchType') {
            stats.criteriaCount[key] = (stats.criteriaCount[key] || 0) + 1
          }
        })
      })

    // Get top 10 criteria
    stats.topCriteria = Object.entries(stats.criteriaCount)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([criterion, count]) => ({ criterion, count }))

    return stats
  } catch (error) {
    console.error('❌ Failed to get weekly stats:', error.message)
    return null
  }
}

module.exports = {
  supabase,
  logAnalytics,
  getAnalytics,
  getWeeklyStats
}

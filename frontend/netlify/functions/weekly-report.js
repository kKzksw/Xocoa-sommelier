/**
 * Netlify Scheduled Function - Weekly Analytics Report
 *
 * Schedule: Every Saturday at 9:00 AM GMT
 * Configuration in netlify.toml
 *
 * Reads analytics from Supabase and sends email report
 */

const nodemailer = require('nodemailer')
const { getWeeklyStats } = require('../../src/utils/supabase.cjs')

// Email configuration
const EMAIL_CONFIG = {
  from: process.env.REPORT_EMAIL_FROM || 'noreply@xocoa-sommelier.com',
  to: process.env.REPORT_EMAIL_TO || 'julien@bonplein.fr',
  subject: '📊 XOCOA - Rapport Hebdomadaire Analytics'
}

/**
 * Generate HTML email report from Supabase analytics
 */
function generateWeeklyReport(stats, startDate, endDate) {
  const {
    totalConnections,
    totalSearches,
    totalBlocked,
    uniqueIPs,
    languageBreakdown,
    topCriteria
  } = stats

  const htmlReport = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body { font-family: 'Sulphur Point', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1A1A1A; max-width: 800px; margin: 0 auto; padding: 20px; background: #F5F5F0; }
    .container { background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 8px rgba(45, 139, 127, 0.1); }
    h1 { color: #2D8B7F; border-bottom: 3px solid #2D8B7F; padding-bottom: 15px; margin-bottom: 30px; font-weight: 700; }
    h2 { color: #3D2817; margin-top: 35px; margin-bottom: 20px; font-weight: 600; }
    .stat-box { background: #F5F5F0; border-left: 4px solid #2D8B7F; padding: 20px; margin: 15px 0; border-radius: 6px; transition: transform 0.2s; }
    .stat-box:hover { transform: translateX(5px); }
    .stat-box strong { color: #2D8B7F; font-size: 32px; display: block; margin-bottom: 8px; font-weight: 700; }
    .stat-box span { color: #3D2817; font-size: 14px; font-weight: 600; }
    .criteria-list { list-style: none; padding: 0; }
    .criteria-list li { background: #F5F5F0; margin: 8px 0; padding: 15px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; border-left: 3px solid #2D8B7F; }
    .badge { background: #2D8B7F; color: white; padding: 4px 12px; border-radius: 16px; font-size: 13px; font-weight: 600; }
    table { width: 100%; border-collapse: collapse; margin: 20px 0; background: white; }
    th, td { padding: 15px; text-align: left; border-bottom: 1px solid #e0e0e0; }
    th { background: #2D8B7F; color: white; font-weight: 600; }
    tr:hover { background: #F5F5F0; }
    .insight { background: #fff; border-left: 4px solid #3D2817; padding: 15px; margin: 10px 0; border-radius: 6px; }
    .insight strong { color: #3D2817; }
    .footer { margin-top: 50px; padding-top: 25px; border-top: 2px solid #e0e0e0; font-size: 13px; color: #666; text-align: center; }
    .period { background: #3D2817; color: white; padding: 10px 20px; border-radius: 6px; display: inline-block; margin-bottom: 30px; font-weight: 600; }
  </style>
</head>
<body>
  <div class="container">
    <h1>📊 XOCOA Sommelier - Rapport Hebdomadaire</h1>
    <div class="period">
      📅 Période : ${startDate.toLocaleDateString('fr-FR')} - ${endDate.toLocaleDateString('fr-FR')}
    </div>

    <h2>🔢 Statistiques Globales</h2>

    <div class="stat-box">
      <strong>${totalConnections}</strong>
      <span>Connexions totales</span>
    </div>

    <div class="stat-box">
      <strong>${totalSearches}</strong>
      <span>Recherches effectuées</span>
    </div>

    <div class="stat-box">
      <strong>${uniqueIPs}</strong>
      <span>Visiteurs uniques (IP)</span>
    </div>

    <div class="stat-box">
      <strong>${totalBlocked}</strong>
      <span>Requêtes bloquées (sécurité)</span>
    </div>

    <h2>🌍 Répartition par Langue</h2>
    <table>
      <tr>
        <th>Langue</th>
        <th>Recherches</th>
        <th>Pourcentage</th>
      </tr>
      <tr>
        <td>🇫🇷 Français</td>
        <td>${languageBreakdown.fr}</td>
        <td><strong>${totalSearches > 0 ? Math.round((languageBreakdown.fr / totalSearches) * 100) : 0}%</strong></td>
      </tr>
      <tr>
        <td>🇬🇧 Anglais</td>
        <td>${languageBreakdown.en}</td>
        <td><strong>${totalSearches > 0 ? Math.round((languageBreakdown.en / totalSearches) * 100) : 0}%</strong></td>
      </tr>
      <tr>
        <td>🇪🇸 Espagnol</td>
        <td>${languageBreakdown.es}</td>
        <td><strong>${totalSearches > 0 ? Math.round((languageBreakdown.es / totalSearches) * 100) : 0}%</strong></td>
      </tr>
    </table>

    <h2>🔍 Top 10 Critères de Recherche</h2>
    ${topCriteria.length > 0 ? `
      <ul class="criteria-list">
        ${topCriteria.map(({ criterion, count }) => `
          <li>
            <span style="font-weight: 600; color: #3D2817;">${criterion.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
            <span class="badge">${count} recherche${count > 1 ? 's' : ''}</span>
          </li>
        `).join('')}
      </ul>
    ` : '<p style="color: #666; font-style: italic;">Aucun critère de recherche cette semaine</p>'}

    <h2>💡 Insights Clés</h2>
    <div class="insight">
      <strong>Langue dominante:</strong>
      ${languageBreakdown.fr > languageBreakdown.en && languageBreakdown.fr > languageBreakdown.es ? '🇫🇷 Français' :
        languageBreakdown.en > languageBreakdown.es ? '🇬🇧 Anglais' : '🇪🇸 Espagnol'}
      (${Math.max(languageBreakdown.fr, languageBreakdown.en, languageBreakdown.es)} recherches)
    </div>

    ${topCriteria[0] ? `
      <div class="insight">
        <strong>Critère le plus populaire:</strong>
        ${topCriteria[0].criterion.replace(/_/g, ' ')}
        <span class="badge" style="margin-left: 10px;">${topCriteria[0].count} fois</span>
      </div>
    ` : ''}

    <div class="insight">
      <strong>Taux d'engagement:</strong>
      ${totalConnections > 0 ? Math.round((totalSearches / totalConnections) * 100) : 0}%
      (${totalSearches} recherches / ${totalConnections} connexions)
    </div>

    <div class="insight">
      <strong>Taux de blocage:</strong>
      ${totalConnections > 0 ? Math.round((totalBlocked / totalConnections) * 100) : 0}%
      (${totalBlocked} requêtes bloquées)
    </div>

    <div class="footer">
      <p><strong>Ce rapport est généré automatiquement chaque samedi à 9h00 GMT</strong></p>
      <p>Données stockées dans Supabase • Envoyé via Netlify Functions</p>
      <p style="margin-top: 20px; color: #2D8B7F; font-weight: 600;">XOCOA Sommelier • ${new Date().getFullYear()}</p>
    </div>
  </div>
</body>
</html>
  `

  return htmlReport
}

/**
 * Send email via SMTP
 */
async function sendEmailReport(htmlContent) {
  // Check if SMTP is configured
  if (!process.env.SMTP_USER || !process.env.SMTP_PASS) {
    throw new Error('SMTP credentials not configured. Please set SMTP_USER and SMTP_PASS environment variables.')
  }

  // Configure SMTP transporter
  const transporter = nodemailer.createTransport({
    host: process.env.SMTP_HOST || 'smtp.gmail.com',
    port: parseInt(process.env.SMTP_PORT || '587'),
    secure: false, // true for 465, false for other ports
    auth: {
      user: process.env.SMTP_USER,
      pass: process.env.SMTP_PASS
    }
  })

  // Verify connection
  await transporter.verify()
  console.log('✅ SMTP connection verified')

  // Send email
  const info = await transporter.sendMail({
    from: EMAIL_CONFIG.from,
    to: EMAIL_CONFIG.to,
    subject: EMAIL_CONFIG.subject,
    html: htmlContent
  })

  return info
}

/**
 * Netlify scheduled function handler
 */
exports.handler = async (event, context) => {
  try {
    console.log('📧 Starting weekly report generation...')

    // Calculate date range (last 7 days)
    const endDate = new Date()
    const startDate = new Date(endDate)
    startDate.setDate(startDate.getDate() - 7)

    console.log(`📅 Fetching analytics from ${startDate.toISOString()} to ${endDate.toISOString()}`)

    // Get weekly stats from Supabase
    const stats = await getWeeklyStats(startDate, endDate)

    if (!stats) {
      throw new Error('Failed to retrieve weekly stats from Supabase')
    }

    console.log(`📊 Stats retrieved: ${stats.totalSearches} searches, ${stats.uniqueIPs} unique visitors`)

    // Generate HTML report
    const htmlReport = generateWeeklyReport(stats, startDate, endDate)

    // Send email
    const emailInfo = await sendEmailReport(htmlReport)

    console.log(`✅ Weekly report sent successfully to ${EMAIL_CONFIG.to}`)
    console.log(`📨 Message ID: ${emailInfo.messageId}`)

    return {
      statusCode: 200,
      body: JSON.stringify({
        success: true,
        message: 'Weekly report sent successfully',
        recipient: EMAIL_CONFIG.to,
        stats: {
          totalConnections: stats.totalConnections,
          totalSearches: stats.totalSearches,
          uniqueIPs: stats.uniqueIPs
        }
      })
    }
  } catch (error) {
    console.error('❌ Error sending weekly report:', error)

    return {
      statusCode: 500,
      body: JSON.stringify({
        success: false,
        error: 'Failed to send weekly report',
        details: error.message
      })
    }
  }
}

const axios = require('axios');
const { logAnalytics } = require('../../src/utils/supabase.cjs');

// Backend URL - Default to localhost Docker for now
// In production, this should be an env var like process.env.BACKEND_API_URL
const BACKEND_URL = process.env.BACKEND_API_URL || 'http://localhost:8000/api/chat';

// Debug mode
const IS_DEBUG = process.env.DEBUG === 'true';

exports.handler = async (event, context) => {
  // 1. CORS Headers
  const corsValidOrigins = [
    'https://xocoa.co',
    'https://www.xocoa.co',
    'https://xocoa-sommelier.com',
    'https://www.xocoa-sommelier.com',
    'https://xocoasommelier.netlify.app',
    'https://www.xocoasommelier.netlify.app',
    'http://localhost:3000',
    'http://localhost:3001'
  ];

  const requestOrigin = event.headers.origin || '';
  const allowedOrigin = corsValidOrigins.some(v => requestOrigin.startsWith(v))
    ? requestOrigin
    : 'https://xocoa-sommelier.com';

  const headers = {
    'Access-Control-Allow-Origin': allowedOrigin,
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
  };

  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 200, headers, body: '' };
  }

  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, headers, body: JSON.stringify({ error: 'Method not allowed' }) };
  }

  try {
    const {
      message,
      conversationHistory = [],
      last_ranked_products = [],
      state = {}
    } = JSON.parse(event.body);
    
    // 2. Prepare Payload for Python Master Brain
    // Frontend sends: conversationHistory = [{type: 'user', content: '...'}, ...]
    // Backend expects: history = [{role: 'user', content: '...'}, ...]
    
    const mappedHistory = conversationHistory.map(msg => ({
      role: msg.type === 'assistant' ? 'assistant' : 'user',
      content: msg.content
    }));

    // 3. Forward to Python Backend
    IS_DEBUG && console.log(`🚀 Proxying to Master Brain: ${BACKEND_URL}`);
    
    const response = await axios.post(BACKEND_URL, {
      message: message,
      history: mappedHistory,
      last_ranked_products: last_ranked_products,
      state: state
    }, { timeout: 30000 }); // 30s timeout

    const backendData = response.data;

    // 4. Map Response to Frontend Format
    // Backend: { response_text: "...", products: [...] }
    // Frontend Expects: { message: "...", recommendations: [...], preferences: {} }
    
    const result = {
      message: backendData.response_text,
      recommendations: backendData.products || [],
      preferences: {}, // Decoupled: Backend handles logic internally
      debug_intent: backendData.intent_detected,
      followup_questions: backendData.followup_questions || [],
      conversation_state: backendData.conversation_state || state
    };

    // Log for analytics
    const clientIp = event.headers['x-forwarded-for']?.split(',')[0] || event.headers['client-ip'] || 'unknown';
    IS_DEBUG && console.log(`✅ Master Brain Replied. Intent: ${backendData.intent_detected}, Products: ${result.recommendations.length}`);

    return {
      statusCode: 200,
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify(result)
    };

  } catch (error) {
    console.error('❌ Master Brain Connection Error:', error.message);
    
    // Fallback error message
    return {
      statusCode: 500,
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        error: 'Backend Error',
        message: "Je suis désolé, mon cerveau principal est inaccessible pour le moment. (Backend Connection Failed)"
      })
    };
  }
};

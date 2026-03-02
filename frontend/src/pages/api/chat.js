export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method not allowed' })
  }

  try {
    const {
      message,
      conversationHistory = [],
      last_ranked_products = [],
      state = {}
    } = req.body

    // 1. Map Frontend format (type) to Backend API format (role)
    // The frontend uses 'type: user/assistant', backend needs 'role: user/assistant'
    const cleanHistory = (conversationHistory || []).map(msg => {
        const role = (msg.type === 'assistant' || msg.role === 'assistant') ? 'assistant' : 'user';
        return {
            role: role,
            content: msg.content
        };
    });

    const BACKEND_URL = process.env.BACKEND_API_URL || 'http://localhost:8000/api/chat'

    // 2. Call the Master Brain (Python Backend)
    const backendResponse = await fetch(BACKEND_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: message,
        history: cleanHistory,
        last_ranked_products: last_ranked_products,
        state: state
      })
    })

    if (!backendResponse.ok) {
      const errorText = await backendResponse.text();
      throw new Error(`Master Brain Error: ${errorText}`);
    }

    const data = await backendResponse.json()

    // 3. Map Backend Response -> Frontend Format
    // Frontend expects: { message, recommendations, preferences }
    const frontendResponse = {
      message: data.response_text,
      recommendations: data.products || [],
      preferences: {},
      intent: data.intent_detected,
      followup_questions: data.followup_questions || [],
      answer_options: data.answer_options || [],
      conversation_state: data.conversation_state || state
    }

    res.status(200).json(frontendResponse)

  } catch (error) {
    console.error('❌ Proxy Error:', error.message)
    res.status(500).json({
      message: "Mon cerveau principal est occupé à déguster des fèves. Veuillez réessayer dans un instant.",
      recommendations: []
    })
  }
}

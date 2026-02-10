import os
import re
from typing import List, Dict, Any
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class LLMExplainer:
    def __init__(self):
        """Initialize Groq client with API key from .env"""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("WARNING: GROQ_API_KEY not found. LLM explanations will be disabled.")
            self.client = None
        else:
            self.client = Groq(api_key=api_key)
            
        self.model = "llama-3.1-8b-instant"
        
        # THE ELITE SOMMELIER: Grounded, Precise, and Multilingual.
        self.system_prompt = (
            "You are XOCOA, a Master Chocolatier. You operate under a 'Strict Evidence' protocol.\n\n"
            
            "STRICT RULES:\n"
            "1. NO EXTERNAL KNOWLEDGE: Only recommend chocolates present in the 'DATABASE RESULTS' list provided below. If a brand is not in that list, DO NOT mention it, even if you are familiar with it.\n"
            "2. LANGUAGE LOCK: Respond in the SAME language the user uses. If they speak French, your entire response must be in elegant French.\n"
            "3. DATA INTEGRITY: Use the 'BRAND', 'NAME', and 'PRICE' fields exactly as provided. Do NOT invent prices or weights.\n"
            "4. RAPPORT: Greet the user warmly. If the request is for a gift, ask about the recipient's taste (Adventurous vs traditional).\n"
            "5. DISCOVERY: If you have a list, pick 1-2 bars and explain why their FLAVORS match the user's request. Connect the dots (e.g., 'The blackberry notes will please a fruity palate').\n"
            "6. INTERNAL SIGNAL: If the user wants chocolate but the list is empty, output ONLY: [SEARCH: <query>].\n"
            "7. NO REPETITION: Do not repeat technical data pointlessly. Weave them into a sophisticated narrative.\n"
        )

    def chat(self, history: List[Dict[str, str]], context_data: str = "") -> str:
        """
        Handle a conversational turn.
        history: List of {"role": "user"/"assistant", "content": "..."}
        context_data: String containing search results or DB stats.
        """
        if not self.client:
            return "I am unable to chat right now (API Key missing)."

        # Construct messages list
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add conversation history (limited to last 6 turns to save context window)
        for msg in history[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
        # Inject context if available (as a system note before the last user message)
        if context_data:
            # Insert before the last message (which is usually the user's latest query)
            messages.insert(-1, {"role": "system", "content": f"CONTEXT FROM DATABASE:\n{context_data}"})

        import time
        import random
        
        max_retries = 3
        base_delay = 2

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7, # Conversational warmth
                    max_tokens=400
                )
                text = response.choices[0].message.content
                
                # Legacy Frontend Compatibility: Strip Markdown formatting
                text = text.replace("**", "").replace("__", "")
                
                return text

            except Exception as e:
                error_str = str(e).lower()
                # Check for rate limit error (429)
                if "429" in error_str or "rate limit" in error_str:
                    if attempt < max_retries - 1:
                        # Exponential backoff with jitter: 2s, 4s, 8s... + random
                        sleep_time = (base_delay * (2 ** attempt)) + (random.random() * 0.5)
                        print(f"⚠️ Rate limit hit. Retrying in {sleep_time:.2f}s...")
                        time.sleep(sleep_time)
                        continue
                    else:
                        return "I'm a bit overwhelmed with requests right now. Could you ask me again in a few seconds?"
                else:
                    # Non-retryable error
                    return f"I'm having trouble thinking right now. ({str(e)})"

    def explain(self, query: str, products: List[Dict]) -> str:
        """Legacy explanation method (wraps chat)"""
        # Format products into a context string
        context = "RECOMMENDED PRODUCTS:\n"
        for i, p in enumerate(products[:3], 1):
            context += f"{i}. {p.get('name')} by {p.get('maker_name')} ({p.get('maker_country')}). "
            context += f"Notes: {p.get('flavor_notes_primary')}. Review: {p.get('expert_review')}\n"
            
        history = [{"role": "user", "content": query}]
        return self.chat(history, context)
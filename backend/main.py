import json
import os
import logging
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import Core Services
# Note: We run this as a module (python -m backend.main), so imports work from root
from channel_a.api import ChannelAService
from channel_b.service import ChannelBService
from channel_c.explainer import LLMExplainer
from orchestration.intent_router import SemanticIntentRouter
from orchestration.recommender import RecommenderService
from orchestration.reference_resolver import resolve_reference

# -----------------------------------------------------------------------------
# Logging Setup
# -----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("XOCOA_API")

# -----------------------------------------------------------------------------
# Data Models
# -----------------------------------------------------------------------------
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[Message] = []
    # Client should send back the products from the last turn if they exist
    # This enables "reference" resolution (e.g. "tell me about the first one") without server-side session state
    last_ranked_products: Optional[List[Dict[str, Any]]] = None 

class ChatResponse(BaseModel):
    response_text: str
    products: List[Dict[str, Any]] = []
    intent_detected: str
    debug_info: Optional[Dict[str, Any]] = None

# -----------------------------------------------------------------------------
# Global State (Loaded on Startup)
# -----------------------------------------------------------------------------
services = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Load heavy models and data on startup.
    This ensures the first user request is fast.
    """
    logger.info("🍫 XOCOA Backend Starting...")
    
    try:
        # 1. Load Data
        logger.info(">>> Loading Chocolates JSON...")
        with open("data/chocolates.json", "r", encoding="utf-8") as f:
            chocolates = json.load(f)
            
        # 2. Init Channel A (The Guard)
        logger.info(">>> Initializing Channel A...")
        channel_a = ChannelAService(chocolates)
        
        # 3. Init Channel B (The Scout) - Heavy Load
        logger.info(">>> Initializing Channel B (Embeddings)...")
        # Ensure path is correct relative to root
        if os.path.exists("data/chocolate_embeddings.json"):
            channel_b = ChannelBService("data/chocolate_embeddings.json")
        else:
            logger.error("CRITICAL: Embeddings file not found!")
            raise FileNotFoundError("data/chocolate_embeddings.json")

        # 4. Init Channel C (The Persona)
        logger.info(">>> Initializing Channel C (LLM)...")
        explainer = LLMExplainer()
        
        # 5. Init Orchestration
        logger.info(">>> Initializing Router & Recommender...")
        router = SemanticIntentRouter(channel_b.model) # Share the encoder
        recommender = RecommenderService(channel_a, channel_b, explainer)
        
        # Store in global state
        services["chocolates"] = chocolates
        services["channel_a"] = channel_a
        services["channel_b"] = channel_b
        services["explainer"] = explainer
        services["router"] = router
        services["recommender"] = recommender
        
        logger.info("✅ XOCOA Backend Ready!")
        yield
        
    except Exception as e:
        logger.error(f"❌ Startup Failed: {e}")
        raise e
    finally:
        logger.info("🛑 XOCOA Backend Shutting Down...")

# -----------------------------------------------------------------------------
# App Definition
# -----------------------------------------------------------------------------
app = FastAPI(title="XOCOA API", version="1.0.0", lifespan=lifespan)

# Allow CORS for Netlify/Localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # TODO: Lock this down to specific Netlify domain in Production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "xocoa-sommelier"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main conversational endpoint.
    """
    try:
        user_input = request.message
        # ELITE OPERATOR FIX: Ensure the current message is part of the history for the LLM
        # This fixes the "empty first response" issue caused by React state timing.
        history_dicts = [{"role": m.role, "content": m.content} for m in request.history]
        if not history_dicts or history_dicts[-1]["content"] != user_input:
            history_dicts.append({"role": "user", "content": user_input})
        
        # 0. Context Rehydration (Self-Healing)
        if not request.last_ranked_products and request.history:
            last_bot_msg = next((m.content for m in reversed(request.history) if m.role == "assistant"), None)
            if last_bot_msg:
                rehydrated = []
                for p in services["chocolates"]:
                    p_name = p.get("name", "")
                    if p_name and len(p_name) > 3 and p_name in last_bot_msg:
                         rehydrated.append(p)
                if rehydrated:
                    logger.info(f"Rehydrating Context from History: found {len(rehydrated)} products.")
                    request.last_ranked_products = rehydrated

        # 1. Detect Intent
        router = services["router"]
        explainer = services["explainer"]
        recommender = services["recommender"]
        chocolates = services["chocolates"]
        
        # --- LANGUAGE DETECTION (Dynamic) ---
        user_lang = "English"
        q_low = user_input.lower()
        if any(w in q_low for w in ["bonjour", "salut", "merci", "cherche", "lait", "noir", "je", "vous", "est-ce"]):
            user_lang = "French"
        elif any(w in q_low for w in ["hola", "gracias", "quiero", "leche", "negro", "usted"]):
            user_lang = "Spanish"
        elif any(w in q_low for w in ["hallo", "danke", "ich", "schokolade", "bitte"]):
            user_lang = "German"
        elif any(w in q_low for w in ["namaste", "dhanyavad", "chahiye", "hindi", "indian"]):
            user_lang = "English (with Indian context)" # Respond in English but acknowledge culture
        
        lang_instruction = f"SYSTEM: The user is currently speaking {user_lang}. You MUST respond in {user_lang}."

        intent = router.detect_intent(user_input)
        logger.info(f"Input: '{user_input}' | Language: {user_lang} | Intent: {intent}")
        
        response_text = ""
        products = []
        
        # 2. Execute Logic
        if intent == "chat":
            # Pure conversation - NO product context passed initially
            # Inject language instruction
            response_text = explainer.chat(history_dicts, context_data=lang_instruction)
            
            # SELF-CORRECTION: Did the LLM realize it needs to search?
            if "[SEARCH:" in response_text:
                import re
                match = re.search(r"\[SEARCH: (.*?)\]", response_text)
                if match:
                    search_query = match.group(1)
                    logger.info(f"LLM Triggered Search: '{search_query}'")
                    result = recommender.recommend(search_query, top_k=5)
                    ranked_ids = result.get("ranked", [])
                    products = [p for p in chocolates if p["id"] in ranked_ids]
                    
                    if not products:
                        response_text = explainer.chat(history_dicts, context_data=f"{lang_instruction}\nSYSTEM: Search for '{search_query}' returned zero results.")
                    else:
                        list_items = [f"{i}. **{p.get('name')}** ({p.get('cocoa_percentage', '?')}% cocoa)" for i, p in enumerate(products, 1)]
                        context_str = f"{lang_instruction}\nDATABASE RESULTS:\n" + "\n".join(list_items)
                        explanation = explainer.chat(history_dicts, context_data=context_str)
                        response_text = f"I found **{len(products)}** chocolates for you:\n\n" + "\n".join(list_items) + "\n\n" + explanation
                    intent = "search_fallback"

        elif intent in ["search", "refine"]:
            current_q = user_input
            # Context-aware refinement (ELITE OPERATOR UPGRADE)
            last_q = next((msg.content for msg in reversed(request.history) if msg.role == "user" and msg.content != user_input), None)
            if last_q and (len(user_input.split()) < 5 or any(k in user_input.lower() for k in ["more", "else", "other", "another", "instead", "under", "above"])):
                if not any(word in user_input.lower() for word in last_q.lower().split() if len(word) > 3):
                    current_q = last_q + " " + user_input
                    logger.info(f"Refining Search Context: '{current_q}'")
            
            result = recommender.recommend(current_q, top_k=5)
            ranked_ids = result.get("ranked", [])
            products = [p for p in chocolates if p["id"] in ranked_ids]
            
            if not products:
                response_text = explainer.chat(history_dicts, context_data=f"{lang_instruction}\nSYSTEM: Search for '{current_q}' returned zero results.")
            else:
                # Build rich, structured context for the LLM
                list_items = []
                for i, p in enumerate(products, 1):
                    # YAML-like structure is much harder for the LLM to hallucinate over
                    item_str = f"- ITEM_ID: {i}\n"
                    item_str += f"  BRAND: {p.get('brand', 'N/A')}\n"
                    item_str += f"  NAME: {p.get('name', 'N/A')}\n"
                    item_str += f"  COCOA: {p.get('cocoa_percentage', '?')}%\n"
                    item_str += f"  PRICE: {p.get('price_retail', 'N/A')} {p.get('price_currency', 'USD')}\n"
                    item_str += f"  FLAVORS: {p.get('flavor_notes_primary', '')}, {p.get('flavor_notes_secondary', '')}\n"
                    item_str += f"  EXPERT_RATING: {p.get('rating', 'N/A')}/5\n"
                    item_str += f"  WEBSITE: {p.get('maker_website', 'N/A')}\n"
                    list_items.append(item_str)
                
                is_vague = len(user_input.split()) < 4 and not any(k in q_low for k in ["under", "above", "percent", "%"])
                
                system_note = f"{lang_instruction}\nSYSTEM: ONLY recommend from the list below.\n"
                if is_vague:
                    system_note += "SYSTEM: User request is vague. Recommend ONLY 2 items and ask a discovery question.\n"
                
                context_str = system_note + "DATABASE RESULTS:\n" + "\n".join(list_items)
                explanation = explainer.chat(history_dicts, context_data=context_str)
                
                response_text = f"I found **{len(products)}** chocolates for you:\n\n" + explanation

        elif intent == "reference":
            if not request.last_ranked_products:
                # ELITE OPERATOR SILENT RECOVERY:
                # If we think it's a reference but have no list, treat it as a SEARCH.
                # This prevents the "I don't have a list" error message.
                logger.info(f"Reference intent detected but no context. Falling back to Search for: '{user_input}'")
                intent = "search"
                # Proceed to search logic below
                result = recommender.recommend(user_input, top_k=5)
                ranked_ids = result.get("ranked", [])
                products = [p for p in chocolates if p["id"] in ranked_ids]
                if not products:
                    response_text = explainer.chat(history_dicts, context_data=f"{lang_instruction}\nSYSTEM: Search for '{user_input}' returned zero results.")
                else:
                    list_items = [f"{i}. **{p.get('name')}** ({p.get('cocoa_percentage', '?')}% cocoa)" for i, p in enumerate(products, 1)]
                    context_str = f"{lang_instruction}\nDATABASE RESULTS:\n" + "\n".join(list_items)
                    explanation = explainer.chat(history_dicts, context_data=context_str)
                    response_text = f"I found **{len(products)}** chocolates for you:\n\n" + explanation
            else:
                fact_text, idx = resolve_reference(user_input, request.last_ranked_products)
                response_text = explainer.chat(history_dicts, context_data=f"{lang_instruction}\nFACTUAL ANSWER: {fact_text}")
                products = request.last_ranked_products

        else:
            response_text = explainer.chat(history_dicts, context_data=lang_instruction)

        # FINAL SANITIZATION: Strip internal tokens
        import re
        response_text = re.sub(r"\[SEARCH:.*?\]", "", response_text).strip()

        return ChatResponse(
            response_text=response_text,
            products=products,
            intent_detected=intent,
            debug_info={"router_score": "hidden"}
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        # Graceful degradation
        return ChatResponse(
            response_text="I'm having a bit of trouble accessing my chocolate cellar right now. Please try again in a moment.",
            products=[],
            intent_detected="error",
            debug_info={"error": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    # Dev mode
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

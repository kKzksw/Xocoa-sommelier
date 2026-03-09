import json
import os
import logging
import re
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from prometheus_fastapi_instrumentator import Instrumentator

# Import Core Services
# Note: We run this as a module (python -m backend.main), so imports work from root
from channel_a.api import ChannelAService
from channel_b.service import ChannelBService
from channel_c.explainer import LLMExplainer
from orchestration.intent_router import SemanticIntentRouter
from orchestration.recommender import RecommenderService
from orchestration.reference_resolver import resolve_reference
from orchestration.agentic_sommelier_engine import (
    SEGMENT_SELECTION_PROMPT,
    build_agentic_filters,
    build_agentic_retrieval_query,
    get_clarification_turns,
    normalize_state,
    set_ambiguity_helper,
)
from orchestration.agentic_runtime import (
    is_question_action,
    read_agent_trace,
    run_pre_retrieval_agent_turn,
    run_post_retrieval_verification,
)

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
    history: List[Message] = Field(default_factory=list)
    # Client should send back the products from the last turn if they exist
    # This enables "reference" resolution (e.g. "tell me about the first one") without server-side session state
    last_ranked_products: Optional[List[Dict[str, Any]]] = None 
    # Frontend can persist this and send it back each turn (stateless backend memory).
    state: Dict[str, str] = Field(default_factory=dict)

class ChatResponse(BaseModel):
    response_text: str
    products: List[Dict[str, Any]] = Field(default_factory=list)
    intent_detected: str
    followup_questions: List[str] = Field(default_factory=list)
    answer_options: List[str] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    agent_trace: List[Dict[str, Any]] = Field(default_factory=list)
    conversation_state: Dict[str, str] = Field(default_factory=dict)
    debug_info: Optional[Dict[str, Any]] = None

# -----------------------------------------------------------------------------
# Global State (Loaded on Startup)
# -----------------------------------------------------------------------------
services = {}


def _contradicts_available_results(text: str) -> bool:
    lower = (text or "").lower()
    contradiction_markers = [
        "couldn't find",
        "could not find",
        "no match",
        "no matches",
        "not find a match",
        "no results",
    ]
    return any(marker in lower for marker in contradiction_markers)


def _fallback_sommelier_recommendation(products: List[Dict[str, Any]], max_items: int = 5) -> str:
    selected = products[:max_items]
    if not selected:
        return "I couldn't find a confident match. Could you share one more preference?"
    lines = ["Here are my top chocolate recommendations for you:"]
    for idx, p in enumerate(selected, 1):
        name = p.get("name", "Unknown chocolate")
        brand = p.get("brand", "Unknown maker")
        cocoa = p.get("cocoa_percentage", "?")
        price = p.get("price_retail", "N/A")
        currency = p.get("price_currency", "USD")
        notes = ", ".join(
            [
                str(p.get("flavor_notes_primary", "")).strip(),
                str(p.get("flavor_notes_secondary", "")).strip(),
            ]
        ).strip(", ").strip()
        why = f"{notes}" if notes else "balanced artisanal profile"
        lines.append(
            f"{idx}. {name} by {brand} ({cocoa}% cocoa, {price} {currency}) - Why it fits: {why}."
        )
    return "\n".join(lines)


def _format_explanation_layer(layer: Optional[Dict[str, Any]]) -> str:
    if not isinstance(layer, dict):
        return ""
    matched = layer.get("matched_preferences", [])
    relaxed = layer.get("relaxed_preferences", [])
    tradeoff = str(layer.get("tradeoff", "")).strip()

    matched_str = ", ".join(matched) if matched else "none explicitly matched"
    relaxed_str = ", ".join(relaxed) if relaxed else "none"

    lines = [
        "Matched preferences: " + matched_str,
        "Relaxed preferences: " + relaxed_str,
    ]
    if tradeoff:
        lines.append("Tradeoff: " + tradeoff)
    return "\n".join(lines)


def _flavor_direction_label(product: Dict[str, Any]) -> str:
    blob = " ".join(
        [
            str(product.get("flavor_notes_primary", "")),
            str(product.get("flavor_notes_secondary", "")),
            str(product.get("tasting_notes", "")),
        ]
    ).lower()
    if any(k in blob for k in ["fruit", "berry", "citrus", "plum", "peach"]):
        return "Fruity & bright"
    if any(k in blob for k in ["nut", "hazelnut", "almond", "praline", "caramel", "toffee"]):
        return "Nutty & gourmand"
    if any(k in blob for k in ["pepper", "spice", "chili", "smoke", "wood", "earth"]):
        return "Bold & intense"
    return "Classic balanced"


def _build_tasting_flight_prompt(products: List[Dict[str, Any]]) -> tuple[str, List[str]]:
    if not products:
        return (
            "I can prepare a tasting flight, but I need one hint: do you want fruity, nutty, or intense?",
            ["Fruity & bright", "Nutty & gourmand", "Bold & intense"],
        )

    lines = ["Here is a 3-piece tasting flight to help you pick your direction:"]
    options: List[str] = []
    for idx, product in enumerate(products[:3], 1):
        direction = _flavor_direction_label(product)
        name = product.get("name", "Unknown chocolate")
        brand = product.get("brand", "Unknown maker")
        cocoa = product.get("cocoa_percentage", "?")
        lines.append(f"{idx}. {name} by {brand} ({cocoa}% cocoa) - Direction: {direction}")
        if direction not in options:
            options.append(direction)

    lines.append("Which direction should I focus on next?")
    return "\n".join(lines), options[:3]


def _is_more_recommendations_request(text: str) -> bool:
    lower = (text or "").strip().lower()
    if not lower:
        return False
    return bool(
        re.search(
            r"\b(another|more|other|else|different)\b.*\b(recommendation|recommend|option|options|choice|choices)\b",
            lower,
        )
        or re.search(r"\b(show me|give me)\b.*\b(more|another|other)\b", lower)
        or lower in {"more", "another", "something else", "other options"}
    )


def _extract_product_ids(products: Optional[List[Dict[str, Any]]]) -> List[int]:
    ids: List[int] = []
    for product in products or []:
        pid = product.get("id")
        try:
            ids.append(int(pid))
        except (TypeError, ValueError):
            continue
    return ids


def _read_shown_product_ids(state: Dict[str, str]) -> List[int]:
    raw = (state or {}).get("_shown_product_ids", "")
    if not raw:
        return []
    ids: List[int] = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            ids.append(int(token))
        except ValueError:
            continue
    return ids


def _write_shown_product_ids(state: Dict[str, str], ids: List[int]) -> Dict[str, str]:
    unique_sorted = sorted({int(pid) for pid in ids})
    state["_shown_product_ids"] = ",".join(str(pid) for pid in unique_sorted)
    return state


def _filter_unseen_products(
    products: List[Dict[str, Any]],
    seen_ids: List[int],
    limit: int = 5,
) -> List[Dict[str, Any]]:
    seen = {int(pid) for pid in seen_ids}
    unseen = []
    for product in products:
        pid = product.get("id")
        try:
            pid_int = int(pid)
        except (TypeError, ValueError):
            continue
        if pid_int in seen:
            continue
        unseen.append(product)
        if len(unseen) >= limit:
            break
    return unseen

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
        # Optional LLM ambiguity helper for the agentic clarification policy.
        set_ambiguity_helper(explainer.structured_ambiguity_check)
        
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

# Add Prometheus Instrumentation
Instrumentator().instrument(app).expose(app)

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
        conversation_state = normalize_state(request.state)

        # Ensure current user turn is always part of LLM history.
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

        # 1) Agentic runtime step before retrieval.
        router = services["router"]
        explainer = services["explainer"]
        recommender = services["recommender"]
        chocolates = services["chocolates"]

        agent_runtime = run_pre_retrieval_agent_turn(
            user_input,
            conversation_state,
            recommender=recommender,
            total_catalog_count=len(chocolates),
        )
        decision = agent_runtime["decision"]
        conversation_state = agent_runtime["conversation_state"]
        candidate_count = agent_runtime["candidate_count"]
        probe_query = agent_runtime["probe_query"]
        filter_bundle = agent_runtime["filter_bundle"]
        agent_action = str(decision.get("action", "RETRIEVE"))
        agent_question = str(decision.get("question", "")).strip()
        agent_answer_options = list(decision.get("answer_options", []))
        fallback_mode = str(decision.get("fallback_mode", "")).strip()
        if is_question_action(agent_action) and agent_question:
            is_segment_prompt = agent_question.strip() == SEGMENT_SELECTION_PROMPT.strip()
            return ChatResponse(
                response_text=agent_question,
                products=[],
                intent_detected="segment_selection" if is_segment_prompt else "clarification",
                followup_questions=[agent_question],
                answer_options=agent_answer_options,
                evidence=[],
                agent_trace=read_agent_trace(conversation_state),
                conversation_state=conversation_state,
                debug_info={
                    "router_score": "hidden",
                    "segment": conversation_state.get("segment", ""),
                    "agent_action": agent_action,
                    "candidate_count": candidate_count,
                    "explicit_constraints": filter_bundle.get("explicit", {}),
                    "hard_filters": filter_bundle.get("hard", {}),
                    "required_constraints": filter_bundle.get("required", {}),
                    "soft_preferences": filter_bundle.get("soft", {}),
                },
            )

        chocolate_by_id = {}
        for product in chocolates:
            pid = product.get("id")
            if pid is None:
                continue
            try:
                chocolate_by_id[int(pid)] = product
            except (TypeError, ValueError):
                continue

        def run_retrieval(search_text: str, top_k: int = 5):
            retrieval_query = build_agentic_retrieval_query(search_text, conversation_state)
            active_filters = build_agentic_filters(conversation_state)
            result = recommender.recommend(
                retrieval_query,
                top_k=top_k,
                segment=conversation_state.get("segment"),
                state=conversation_state,
                hard_filters=active_filters.get("hard"),
            )
            ranked_ids = result.get("ranked", [])
            products_out = [
                chocolate_by_id[pid]
                for pid in ranked_ids
                if pid in chocolate_by_id
            ]
            return retrieval_query, result, products_out

        if fallback_mode == "TASTING_FLIGHT":
            _, result, candidates = run_retrieval("tasting flight chocolate profiles", top_k=30)
            flight_ids = recommender.build_tasting_flight(result.get("ranked", []), size=3)
            flight_products = [chocolate_by_id[pid] for pid in flight_ids if pid in chocolate_by_id]
            prompt_text, direction_options = _build_tasting_flight_prompt(flight_products)
            shown_ids = _read_shown_product_ids(conversation_state) + _extract_product_ids(flight_products)
            conversation_state = _write_shown_product_ids(conversation_state, shown_ids)
            return ChatResponse(
                response_text=prompt_text,
                products=flight_products,
                intent_detected="tasting_flight",
                followup_questions=["Which direction should I focus on next?"],
                answer_options=direction_options,
                evidence=[],
                agent_trace=read_agent_trace(conversation_state),
                conversation_state=conversation_state,
                debug_info={
                    "router_score": "hidden",
                    "segment": conversation_state.get("segment", ""),
                    "fallback_mode": "TASTING_FLIGHT",
                },
            )
        
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
        # While we are in an active clarification journey, short answers like
        # "yes/no/vegan" should continue the retrieval flow, not generic chat.
        if get_clarification_turns(conversation_state) > 0 and intent == "chat":
            intent = "search"
        more_recs_requested = _is_more_recommendations_request(user_input)
        logger.info(f"Input: '{user_input}' | Language: {user_lang} | Intent: {intent}")
        
        response_text = ""
        products = []
        latest_explanation_layer: Dict[str, Any] = {}
        latest_verification: Dict[str, Any] = {}
        final_answer_options: List[str] = []
        
        # 3. Execute Logic
        if intent == "chat":
            response_text = explainer.chat(history_dicts, context_data=lang_instruction)
            
            # SELF-CORRECTION: Did the LLM realize it needs to search?
            if "[SEARCH:" in response_text:
                match = re.search(r"\[SEARCH: (.*?)\]", response_text)
                if match:
                    search_query = match.group(1)
                    logger.info(f"LLM Triggered Search: '{search_query}'")
                    retrieval_query, result, products = run_retrieval(search_query)
                    latest_explanation_layer = result.get("explanation_layer", {}) if isinstance(result, dict) else {}
                    verification = run_post_retrieval_verification(
                        user_message=user_input,
                        state=conversation_state,
                        retrieval_result=result,
                        products=products,
                        total_catalog_count=len(chocolates),
                    )
                    latest_verification = verification
                    verify_question = str(verification.get("question", "")).strip()
                    if str(verification.get("action", "")).upper() == "VERIFY" and verify_question:
                        conversation_state = normalize_state(verification.get("updated_state", conversation_state))
                        return ChatResponse(
                            response_text=verify_question,
                            products=[],
                            intent_detected="clarification",
                            followup_questions=[verify_question],
                            answer_options=list(verification.get("answer_options", [])),
                            evidence=list(verification.get("evidence", [])),
                            agent_trace=read_agent_trace(conversation_state),
                            conversation_state=conversation_state,
                            debug_info={
                                "router_score": "hidden",
                                "segment": conversation_state.get("segment", ""),
                                "agent_post_action": "VERIFY",
                                "verify_reason": verification.get("reason", ""),
                                "verify_metrics": verification.get("metrics", {}),
                                "evidence_preview": verification.get("evidence", []),
                            },
                        )
                    conversation_state = normalize_state(verification.get("updated_state", conversation_state))
                    
                    if not products:
                        response_text = explainer.chat(history_dicts, context_data=f"{lang_instruction}\nSYSTEM: Search for '{retrieval_query}' returned zero results.")
                    else:
                        list_items = [f"{i}. {p.get('name')} ({p.get('cocoa_percentage', '?')}% cocoa)" for i, p in enumerate(products, 1)]
                        available_n = min(5, len(list_items))
                        context_str = (
                            f"{lang_instruction}\n"
                            f"SYSTEM: Write a concise sommelier recommendation for exactly {available_n} product(s) from the list.\n"
                            "SYSTEM: Explain why each match fits the user's preferences.\n"
                            "SYSTEM: Optional: include pairing suggestions.\n"
                            "SYSTEM: If availability is limited, explicitly say so and do not invent extra products.\n"
                            "DATABASE RESULTS:\n"
                            + "\n".join(list_items[:5])
                        )
                        explanation = explainer.chat(history_dicts, context_data=context_str)
                        response_text = explanation
                    intent = "search_fallback"

        elif intent in ["search", "refine"]:
            current_q = user_input
            last_q = next((msg.content for msg in reversed(request.history) if msg.role == "user" and msg.content != user_input), None)
            if last_q and (len(user_input.split()) < 5 or any(k in user_input.lower() for k in ["more", "else", "other", "another", "instead", "under", "above"])):
                if not any(word in user_input.lower() for word in last_q.lower().split() if len(word) > 3):
                    current_q = last_q + " " + user_input
                    logger.info(f"Refining Search Context: '{current_q}'")

            retrieval_top_k = 25 if more_recs_requested else 5
            retrieval_query, result, products = run_retrieval(current_q, top_k=retrieval_top_k)
            latest_explanation_layer = result.get("explanation_layer", {}) if isinstance(result, dict) else {}

            if products:
                seen_ids = _read_shown_product_ids(conversation_state)
                seen_ids.extend(_extract_product_ids(request.last_ranked_products))
                if more_recs_requested:
                    products = _filter_unseen_products(products, seen_ids, limit=5)
                    if not products:
                        response_text = (
                            "I have already shown the closest unique matches for your current criteria. "
                            "Would you like me to broaden one filter (certification, dietary, cocoa intensity, or budget)?"
                        )
                        return ChatResponse(
                            response_text=response_text,
                            products=[],
                            intent_detected="clarification",
                            followup_questions=[
                                "Would you like me to broaden one filter (certification, dietary, cocoa intensity, or budget)?"
                            ],
                            answer_options=["Broaden certification", "Broaden dietary", "Broaden cocoa intensity", "Broaden budget"],
                            evidence=[],
                            agent_trace=read_agent_trace(conversation_state),
                            conversation_state=conversation_state,
                            debug_info={
                                "router_score": "hidden",
                                "segment": conversation_state.get("segment", ""),
                                "no_repeat_candidates_exhausted": True,
                            },
                        )
                shown_ids_updated = seen_ids + _extract_product_ids(products)
                conversation_state = _write_shown_product_ids(conversation_state, shown_ids_updated)

            verification = run_post_retrieval_verification(
                user_message=user_input,
                state=conversation_state,
                retrieval_result=result,
                products=products,
                total_catalog_count=len(chocolates),
            )
            latest_verification = verification
            verify_question = str(verification.get("question", "")).strip()
            if str(verification.get("action", "")).upper() == "VERIFY" and verify_question:
                conversation_state = normalize_state(verification.get("updated_state", conversation_state))
                return ChatResponse(
                    response_text=verify_question,
                    products=[],
                    intent_detected="clarification",
                    followup_questions=[verify_question],
                    answer_options=list(verification.get("answer_options", [])),
                    evidence=list(verification.get("evidence", [])),
                    agent_trace=read_agent_trace(conversation_state),
                    conversation_state=conversation_state,
                    debug_info={
                        "router_score": "hidden",
                        "segment": conversation_state.get("segment", ""),
                        "agent_post_action": "VERIFY",
                        "verify_reason": verification.get("reason", ""),
                        "verify_metrics": verification.get("metrics", {}),
                        "evidence_preview": verification.get("evidence", []),
                    },
                )
            conversation_state = normalize_state(verification.get("updated_state", conversation_state))
            
            if not products:
                response_text = explainer.chat(history_dicts, context_data=f"{lang_instruction}\nSYSTEM: Search for '{retrieval_query}' returned zero results.")
                if not response_text.strip():
                    response_text = "I am sorry, but I could not find any chocolates that match your search criteria. Would you like to try a different search?"
            else:
                list_items = []
                for i, p in enumerate(products, 1):
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
                
                available_n = min(5, len(list_items))
                system_note = f"{lang_instruction}\nSYSTEM: ONLY recommend from the list below.\n"
                if more_recs_requested:
                    system_note += "SYSTEM: User asked for another recommendation. Do not repeat previously shown products.\n"
                    system_note += f"SYSTEM: Recommend exactly {available_n} NEW option(s) only.\n"
                elif is_vague:
                    system_note += f"SYSTEM: User request is vague. Recommend up to {available_n} item(s) and ask one concise discovery question.\n"
                else:
                    system_note += f"SYSTEM: Recommend exactly {available_n} product(s) in refined sommelier tone with short WHY lines.\n"
                system_note += "SYSTEM: If only one product is available, clearly say only one match exists. Do not fabricate additional options.\n"
                
                context_str = system_note + "DATABASE RESULTS:\n" + "\n".join(list_items)
                explanation = explainer.chat(history_dicts, context_data=context_str)
                response_text = explanation

        elif intent == "reference":
            if not request.last_ranked_products:
                logger.info(f"Reference intent detected but no context. Falling back to Search for: '{user_input}'")
                intent = "search"
                retrieval_query, result, products = run_retrieval(user_input)
                latest_explanation_layer = result.get("explanation_layer", {}) if isinstance(result, dict) else {}
                if not products:
                    response_text = explainer.chat(history_dicts, context_data=f"{lang_instruction}\nSYSTEM: Search for '{retrieval_query}' returned zero results.")
                else:
                    list_items = [f"{i}. {p.get('name')} ({p.get('cocoa_percentage', '?')}% cocoa)" for i, p in enumerate(products, 1)]
                    context_str = f"{lang_instruction}\nDATABASE RESULTS:\n" + "\n".join(list_items)
                    explanation = explainer.chat(history_dicts, context_data=context_str)
                    response_text = explanation
            else:
                fact_text, idx = resolve_reference(user_input, request.last_ranked_products)
                response_text = explainer.chat(history_dicts, context_data=f"{lang_instruction}\nFACTUAL ANSWER: {fact_text}")
                products = request.last_ranked_products

        else:
            response_text = explainer.chat(history_dicts, context_data=lang_instruction)

        # FINAL SANITIZATION: Strip internal tokens
        response_text = re.sub(r"\[SEARCH:.*?\]", "", response_text).strip()

        # If products are available, do not allow contradictory "no match" narratives.
        if products and (_contradicts_available_results(response_text) or not response_text.strip()):
            response_text = _fallback_sommelier_recommendation(products)

        if products and latest_explanation_layer:
            layer_text = _format_explanation_layer(latest_explanation_layer)
            if layer_text and "Matched preferences:" not in response_text:
                response_text = f"{response_text}\n\n{layer_text}".strip()

        if not response_text:
            response_text = "I am having trouble finding the right words (or chocolates) at the moment. Could you rephrase that?"

        if products:
            cumulative_ids = _read_shown_product_ids(conversation_state)
            cumulative_ids.extend(_extract_product_ids(products))
            conversation_state = _write_shown_product_ids(conversation_state, cumulative_ids)

        return ChatResponse(
            response_text=response_text,
            products=products,
            intent_detected=intent,
            followup_questions=[],
            answer_options=final_answer_options,
            evidence=list(latest_verification.get("evidence", [])),
            agent_trace=read_agent_trace(conversation_state),
            conversation_state=conversation_state,
            debug_info={
                "router_score": "hidden",
                "segment": conversation_state.get("segment", ""),
                "agent_action": locals().get("agent_action"),
                "agent_post_action": latest_verification.get("action", "N/A"),
                "verify_reason": latest_verification.get("reason", ""),
                "verify_metrics": latest_verification.get("metrics", {}),
                "evidence_preview": latest_verification.get("evidence", []),
                "candidate_count": locals().get("candidate_count"),
                "probe_query": locals().get("probe_query"),
            },
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        # Graceful degradation
        return ChatResponse(
            response_text="I'm having a bit of trouble accessing my chocolate cellar right now. Please try again in a moment.",
            products=[],
            intent_detected="error",
            followup_questions=[],
            answer_options=[],
            evidence=[],
            agent_trace=read_agent_trace(locals().get("conversation_state", normalize_state({}))),
            conversation_state=locals().get("conversation_state", normalize_state({})),
            debug_info={"error": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    # Dev mode
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

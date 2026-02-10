import requests
import json
import time
import statistics
from typing import List, Dict, Any

# Configuration
API_URL = "http://localhost:8000/api/chat"
DATASET_PATH = "tests/data/silver_dataset.json"
REPORT_PATH = "rag_evaluation_report.md"

def load_dataset(path: str) -> List[Dict[str, Any]]:
    with open(path, "r") as f:
        return json.load(f)

def validate_product(product: Dict[str, Any], attributes: Dict[str, Any]) -> bool:
    """
    Checks if a product satisfies the expected attributes.
    """
    # 1. Cocoa Percentage
    if "cocoa_percentage" in attributes:
        p_cocoa = product.get("cocoa_percentage")
        if p_cocoa is not None:
            # Handle string like "70%"
            if isinstance(p_cocoa, str):
                try:
                    p_cocoa = float(p_cocoa.replace("%", ""))
                except:
                    p_cocoa = 0
            
            constraints = attributes["cocoa_percentage"]
            if "min" in constraints and p_cocoa < constraints["min"]:
                return False
            if "max" in constraints and p_cocoa > constraints["max"]:
                return False

    # 2. Price
    if "price_retail" in attributes:
        p_price = product.get("price_retail")
        if p_price is not None:
             # Handle string prices if necessary
            if isinstance(p_price, str):
                try:
                    p_price = float(re.sub(r'[^\d.]', '', p_price))
                except:
                    pass
            
            constraints = attributes["price_retail"]
            if "min" in constraints and p_price < constraints["min"]:
                return False
            if "max" in constraints and p_price > constraints["max"]:
                return False

    # 3. Flavor Keywords
    if "flavor_match" in attributes:
        keywords = attributes["flavor_match"]
        # Search in name, notes, description
        text_corpus = (
            str(product.get("name", "")) + " " + 
            str(product.get("flavor_notes_primary", "")) + " " + 
            str(product.get("flavor_notes_secondary", "")) + " " +
            str(product.get("tasting_notes", ""))
        ).lower()
        
        if not any(k.lower() in text_corpus for k in keywords):
            return False

    # 4. Dietary
    if "dietary_match" in attributes:
        keywords = attributes["dietary_match"]
        text_corpus = (
            str(product.get("dietary", "")) + " " + 
            str(product.get("allergens", "")) + " " +
            str(product.get("name", ""))
        ).lower()
        if not any(k.lower() in text_corpus for k in keywords):
            return False

    return True

def evaluate_query(test_case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runs a single test case against the API and scores it.
    """
    query = test_case["query"]
    expected_intent = test_case["expected_intent"]
    
    payload = {
        "message": query,
        "history": [], # TODO: Support multi-turn via 'requires_context' flag
        "last_ranked_products": []
    }
    
    # Simulate context if needed (Mocking a previous search result)
    if test_case.get("requires_context"):
        payload["last_ranked_products"] = [
            {"id": "mock_1", "name": "Mock Chocolate", "description": "A tasty mock chocolate."}
        ]

    start_time = time.time()
    try:
        response = requests.post(API_URL, json=payload, timeout=30)
        latency = time.time() - start_time
        
        if response.status_code != 200:
            return {
                "id": test_case["id"],
                "success": False,
                "error": f"HTTP {response.status_code}",
                "latency": latency
            }
            
        data = response.json()
        
        # Scoring Logic
        actual_intent = data.get("intent_detected")
        products = data.get("products", [])
        
        # Logic fix: Allow refinement to count as search if expected
        intent_match = (actual_intent == expected_intent) or \
                       (expected_intent == "search" and actual_intent == "refine")
        
        product_count_pass = len(products) >= test_case.get("expected_min_products", 0)
        
        # --- NEW: Relevance Check ---
        relevance_score = 1.0 # Default full score if no attributes to check
        if products and "expected_attributes" in test_case:
            valid_products = [p for p in products if validate_product(p, test_case["expected_attributes"])]
            relevance_score = len(valid_products) / len(products)
            
            # If we expected products but got none relevant, that's a fail
            if len(valid_products) == 0:
                product_count_pass = False 

        # Adversarial Check: Did we leak system info? (Naive check)
        safety_pass = True
        if "jailbreak" in test_case.get("tags", []):
            if "SYSTEM:" in data.get("response_text", "") or "You are a specialized AI" in data.get("response_text", ""):
                safety_pass = False

        # Weighted Score: Intent (Binary) * Safety (Binary) * Relevance (Float)
        # If Intent/Safety fail, score is 0. If they pass, score is Relevance.
        score = 0.0
        if intent_match and safety_pass:
            if test_case.get("expected_min_products", 0) > 0:
                # If we need products, relevance matters
                score = relevance_score if product_count_pass else 0.0
            else:
                # If we don't need products (e.g. Chat), just passing intent is 1.0
                score = 1.0
        
        return {
            "id": test_case["id"],
            "query": query,
            "success": True,
            "score": score,
            "latency": latency,
            "metrics": {
                "intent_match": intent_match,
                "expected_intent": expected_intent,
                "actual_intent": actual_intent,
                "product_count": len(products),
                "relevance_score": relevance_score,
                "safety_pass": safety_pass
            }
        }

    except Exception as e:
        return {
            "id": test_case["id"],
            "success": False,
            "error": str(e),
            "latency": time.time() - start_time
        }


def run_evaluation():
    print("🧪 Starting RAG Evaluation...")
    try:
        dataset = load_dataset(DATASET_PATH)
    except Exception as e:
        print(f"❌ Failed to load dataset: {e}")
        return

    results = []
    
    for case in dataset:
        print(f"   Running {case['id']}: {case['query'][:40]}...")
        res = evaluate_query(case)
        results.append(res)
        
    # Aggregating Metrics
    total = len(results)
    successful_runs = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]
    
    if not successful_runs:
        print("❌ Critical Failure: No queries succeeded.")
        return

    avg_latency = statistics.mean([r["latency"] for r in successful_runs])
    avg_score = statistics.mean([r["score"] for r in successful_runs])
    
    # Generate Report
    markdown = f"# 📊 XOCOA RAG Evaluation Report\n\n"
    markdown += f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    markdown += f"**Overall Score:** {avg_score*100:.1f}%\n"
    markdown += f"**Avg Latency:** {avg_latency:.2f}s\n"
    markdown += f"**Success Rate:** {len(successful_runs)}/{total}\n\n"
    
    markdown += "## 📝 Detailed Breakdown\n"
    markdown += "| ID | Query | Intent | Count | Relevance | Safety | Latency | Result |\n"
    markdown += "|--- |--- |--- |--- |--- |--- |--- |--- |\n"
    
    for r in successful_runs:
        m = r["metrics"]
        status_icon = "✅" if r["score"] == 1.0 else ("⚠️" if r["score"] > 0 else "❌")
        markdown += f"| {r['id']} | {r['query'][:25]}... | {m['actual_intent']} ({'✅' if m['intent_match'] else '❌'}) | {m['product_count']} | {m['relevance_score']:.2f} | {'✅' if m['safety_pass'] else '❌'} | {r['latency']:.2f}s | {status_icon} |\n"
        
    if failures:
        markdown += "\n## ❌ Errors\n"
        for f in failures:
            markdown += f"- **{f['id']}**: {f['error']}\n"
            
    with open(REPORT_PATH, "w") as f:
        f.write(markdown)
        
    print(f"\n✅ Evaluation Complete! Score: {avg_score*100:.1f}%")
    print(f"📄 Report saved to {REPORT_PATH}")

if __name__ == "__main__":
    run_evaluation()
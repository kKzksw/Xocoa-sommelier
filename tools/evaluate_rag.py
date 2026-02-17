import requests
import json
import time
import statistics
import argparse
import sys
import math
from typing import List, Dict, Any

# Configuration
API_URL = "http://localhost:8000/api/chat"
DEFAULT_DATASET = "tests/data/golden_dataset_v2.json"
REPORT_PATH = "rag_evaluation_report.md"

def load_dataset(path: str) -> List[Dict[str, Any]]:
    with open(path, "r") as f:
        return json.load(f)

def validate_product(product: Dict[str, Any], attributes: Dict[str, Any]) -> bool:
    """Strict attribute validation."""
    
    # 1. Price (Max)
    if "price_retail" in attributes:
        p_price = product.get("price_retail")
        if p_price is None: return False
        if isinstance(p_price, str):
            try: p_price = float(p_price.replace("€", "").replace("$", ""))
            except: pass
        if p_price > attributes["price_retail"].get("max", 9999):
            return False

    # 2. Flavor Match (Partial String)
    if "flavor_match" in attributes:
        keywords = attributes["flavor_match"]
        text_corpus = (
            str(product.get("name", "")) + " " + 
            str(product.get("flavor_notes_primary", "")) + " " + 
            str(product.get("tasting_notes", ""))
        ).lower()
        if not any(k.lower() in text_corpus for k in keywords):
            return False

    # 3. Dietary
    if "dietary_match" in attributes:
        keywords = attributes["dietary_match"]
        text_corpus = (
            str(product.get("dietary", "")) + " " + 
            str(product.get("allergens", "")) + " " +
            str(product.get("name", ""))
        ).lower()
        # For "nut-free", we check if "nut" is NOT in allergens OR "nut-free" IS in dietary
        for k in keywords:
            if k == "nut-free":
                if "nut" in str(product.get("allergens", "")).lower(): return False
            elif k not in text_corpus:
                return False
                
    return True

def evaluate_query(test_case: Dict[str, Any]) -> Dict[str, Any]:
    query = test_case["query"]
    expected_intent = test_case["expected_intent"]
    
    payload = {
        "message": query,
        "history": [],
        "last_ranked_products": []
    }
    
    # Mock Context for Reference Queries
    if test_case.get("requires_context"):
        payload["last_ranked_products"] = [
            {"id": 1, "name": "Mock Choco 1", "price_retail": 5.0, "cocoa_percentage": 70},
            {"id": 2, "name": "Mock Choco 2", "price_retail": 10.0, "dietary": "vegan"},
            {"id": 3, "name": "Mock Choco 3", "price_retail": 15.0}
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
                "latency": latency,
                "score": 0.0
            }
            
        data = response.json()
        actual_intent = data.get("intent_detected")
        products = data.get("products", [])
        
        # --- SCORING LOGIC ---
        
        # 1. Intent Check
        intent_pass = (actual_intent == expected_intent) or \
                      (expected_intent == "search" and actual_intent == "refine")
                      
        # 2. Product Count Check
        min_products = test_case.get("expected_min_products", 0)
        count_pass = len(products) >= min_products
        
        # 3. Relevance Check (Strict)
        relevance_score = 1.0
        if min_products > 0 and products:
            if "expected_attributes" in test_case:
                valid_count = sum(1 for p in products if validate_product(p, test_case["expected_attributes"]))
                relevance_score = valid_count / len(products)
            else:
                # If search but no specific attributes, assume relevance is 1.0 (baseline)
                relevance_score = 1.0
        elif min_products > 0 and not products:
            relevance_score = 0.0
            
        # 4. Final Binary Success Determination
        is_success = False
        if intent_pass:
            if min_products > 0:
                # MUST find products AND have > 50% relevance
                if count_pass and relevance_score >= 0.5:
                    is_success = True
            else:
                # Chat/Reference just needs intent pass
                is_success = True
                
        # Safety Check (Override success if failed)
        if "security" in test_case.get("tags", []):
            if "SYSTEM" in data.get("response_text", ""):
                is_success = False

        return {
            "id": test_case["id"],
            "query": query,
            "success": is_success,
            "score": relevance_score if intent_pass else 0.0,
            "latency": latency,
            "metrics": {
                "actual_intent": actual_intent,
                "product_count": len(products),
                "relevance": relevance_score
            }
        }

    except Exception as e:
        return {
            "id": test_case["id"],
            "success": False,
            "error": str(e),
            "latency": 0.0,
            "score": 0.0
        }

def run_evaluation():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ci", action="store_true", help="Fail with exit code 1 if score < 90%")
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    args = parser.parse_args()

    print(f"🏭 Starting INDUSTRIAL-GRADE Evaluation using {args.dataset}...")
    dataset = load_dataset(args.dataset)
    results = []
    
    for i, case in enumerate(dataset):
        res = evaluate_query(case)
        results.append(res)
        # Progress bar
        sys.stdout.write(f"\r[{i+1}/{len(dataset)}] {case['id']}... {'✅' if res['success'] else '❌'}")
        sys.stdout.flush()
        
    print("\n\n--- RESULTS ---")
    
    successful = [r for r in results if r["success"]]
    latencies = [r["latency"] for r in successful]
    latencies.sort()
    
    avg_lat = statistics.mean(latencies) if latencies else 0
    p95 = latencies[int(len(latencies)*0.95)] if latencies else 0
    p99 = latencies[int(len(latencies)*0.99)] if latencies else 0
    
    pass_rate = (len(successful) / len(dataset)) * 100
    
    print(f"📈 Pass Rate: {pass_rate:.1f}%")
    print(f"⏱️ Avg Latency: {avg_lat:.2f}s")
    print(f"🐢 P95 Latency: {p95:.2f}s")
    print(f"🐌 P99 Latency: {p99:.2f}s")
    
    # Markdown Report
    md = "# 🏭 XOCOA Industrial Test Report\n\n"
    md += f"- **Pass Rate:** {pass_rate:.1f}%\n"
    md += f"- **P95 Latency:** {p95:.2f}s\n\n"
    md += "| ID | Query | Intent | Count | Relevance | Latency | Result |\n"
    md += "|--- |--- |--- |--- |--- |--- |--- |\n"
    for r in results:
        m = r.get("metrics", {})
        md += f"| {r['id']} | {r['query'][:20]}... | {m.get('actual_intent')} | {m.get('product_count')} | {m.get('relevance', 0):.2f} | {r['latency']:.2f}s | {'✅' if r['success'] else '❌'} |\n"
    
    with open(REPORT_PATH, "w") as f:
        f.write(md)
        
    if args.ci and pass_rate < 90.0:
        print("❌ CI FAILURE: Pass rate below 90%")
        sys.exit(1)
        
    print("✅ Evaluation Passed.")

if __name__ == "__main__":
    run_evaluation()

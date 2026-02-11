# channel_a/query/parse.py

import re
from warnings import filters

from channel_a import query
from channel_a.normalization.normalize import normalize_country_from_query

def parse_query_to_filters(query: str) -> dict:
    """
    Convert user text into Channel A filters.
    Deterministic. Rule-based only.
    """
    q = query.lower()
    filters = {}

    # --- 1. FLAVOR EXTRACTION (New) ---
    flavor_map = {
        "fruity": ["fruit", "berry", "citrus", "orange", "lemon", "lime", "raspberry", "strawberry", "cherry", "acidic"],
        "nutty": ["nut", "hazelnut", "almond", "pecan", "walnut", "cashew", "pistachio", "praline"],
        "spicy": ["spic", "chili", "pepper", "cinnamon", "cardamom", "ginger"],
        "floral": ["floral", "flower", "jasmine", "rose", "lavender", "vanilla"],
        "earthy": ["earth", "soil", "wood", "smoke", "tobacco", "leather"],
        "sweet": ["sweet", "caramel", "honey", "sugar", "candy", "toffee"],
        "creamy": ["creamy", "smooth", "butter", "milk"],
        "bitter": ["bitter", "intense", "strong", "dark"]
    }
    
    found_flavors = []
    for category, keywords in flavor_map.items():
        if any(k in q for k in keywords):
            # If user asks for "fruity", we add "fruit" to keywords to match index
            # But wait, index matches substrings. So adding the category key might be enough if it appears in text.
            # Let's add the specific keyword matched? No, let's add the Category keywords.
            # Actually, let's just add the Category name if it's broad, or specific text?
            # Better: if "fruity" is found, add ["fruit", "berry"...] to valid keywords?
            # No, filter logic checks `all(k in blob)`.
            # If I add "fruity", and blob has "fruit", it fails.
            # So I should map "fruity" -> "fruit".
            if category == "fruity": found_flavors.append("fruit")
            elif category == "nutty": found_flavors.append("nut")
            elif category == "spicy": found_flavors.append("spic") # Matches spicy, spice
            elif category == "floral": found_flavors.append("flor")
            elif category == "earthy": found_flavors.append("earth")
            elif category == "creamy": found_flavors.append("cream")
            # "Sweet" and "Bitter" are usually traits, not just flavor notes.
            # But let's add them.
            elif category == "sweet": found_flavors.append("sweet")
            # Bitter is tricky, might mean high cocoa.
            
    if found_flavors:
        filters["flavor_keywords"] = found_flavors

    # --- 2. PRICE EXTRACTION (Robust) ---
    # Currency symbols: $, €, £, "euros", "dollars"
    # Patterns: "under 10", "< 10", "10 euros", "$10"
    
    # "Cheap" / "Affordable"
    if "cheap" in q or "affordable" in q or "budget" in q:
        filters["price_max"] = 8.0 # Strict budget

    # "Expensive" / "Luxury"
    if "expensive" in q or "luxury" in q or "premium" in q:
        filters["price_range"] = (15.0, 1000.0)

    # Explicit Max Price
    # Matches: "under 5", "< 5", "max 5", "5 euros", "5$"
    # Regex look for number near "under" or "<"
    under_match = re.search(r"(?:under|below|less than|<|max)\s?\$?(\d+)", q)
    if under_match:
        filters["price_max"] = float(under_match.group(1))
    
    # Matches: "5$ or less" (Not common but possible)
    
    # --- 3. TYPE ---
    if re.search(r"\b(drak|drark|dark|darker)\b", q):
        filters["cocoa_percentage"] = (70, 100)
        filters["exclude_types"] = ["milk", "white"]
    elif re.search(r"\b(mlik|mikl|milk|milky)\b", q):
        filters["cocoa_percentage"] = (30, 60) # Relaxed upper bound for dark milk
        filters["exclude_types"] = ["dark", "white"]
    elif re.search(r"\b(wite|whiite|white)\b", q):
        filters["cocoa_percentage"] = (0, 40)
        filters["exclude_types"] = ["dark", "milk"]

    # --- 4. COCOA % ---
    # "100%", "85 %"
    exact_match = re.search(r"\b(\d{1,3})\s?%", q)
    if exact_match:
        val = float(exact_match.group(1))
        filters["cocoa_percentage"] = (val - 2, val + 2) # Range +/- 2%

    # --- 5. DIETARY & ALLERGENS ---
    if "vegan" in q:
        filters.setdefault("dietary_exclusions", []).append("non-vegan")
        filters.setdefault("exclude_allergens", []).append("milk") # Vegan implies no milk

    if "gluten free" in q or "gluten-free" in q:
        filters.setdefault("dietary_exclusions", []).append("gluten")

    # Robust Nut Exclusion
    if re.search(r"\b(nut\s?free|no\s+nuts?|without\s+nuts?)\b", q):
        nut_types = ["nuts", "hazelnuts", "almonds", "pecans", "walnuts", "cashews", "pistachios", "macadamia", "peanut"]
        filters.setdefault("exclude_allergens", []).extend(nut_types)

    if "dairy free" in q or "no dairy" in q or "without milk" in q:
         filters.setdefault("exclude_allergens", []).append("milk")

    # --- 6. COUNTRY ---
    country = normalize_country_from_query(query)
    if country:
        non_producers = [
            "Switzerland", "Belgium", "France", "Germany", "Italy", "UK", 
            "Canada", "Japan", "USA", "Netherlands", "Austria", "Spain"
        ]
        # Heuristic: If known non-producer, assume Maker. Else assume Origin.
        if country in non_producers:
            filters["maker_country"] = country
        else:
            # "Vietnam chocolate" -> Origin
            filters["origin_country"] = country

    return filters

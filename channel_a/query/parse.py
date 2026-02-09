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

    # --- TYPE ---

    # Catch common typos using regex patterns
    if re.search(r"\b(drak|drark|dark|darker)\b", q):
        filters["cocoa_percentage"] = (70, 100)
        filters["exclude_types"] = ["milk", "white"]
        
    elif re.search(r"\b(mlik|mikl|milk|milky)\b", q):
        filters["cocoa_percentage"] = (30, 55)
        filters["exclude_types"] = ["dark", "white"]

    elif re.search(r"\b(wite|whiite|white)\b", q):
        filters["cocoa_percentage"] = (0, 20)
        filters["exclude_types"] = ["dark", "milk"]

    # Qualitative Cocoa Ranges
    if "low cocoa" in q or "lower cocoa" in q or "mild" in q:
        filters["cocoa_percentage"] = (0, 55)
    
    if "high cocoa" in q or "higher cocoa" in q or "strong" in q or "intense" in q or "bitter" in q:
        filters["cocoa_percentage"] = (80, 100)

    # Explicit Numeric Constraints (e.g., "above 70%", "under 50%", "> 60")
    # Handle "above/over/>"
    above_match = re.search(r"(?:above|over|more than|higher than|>)[\s]?(\d{1,3})", q)
    if above_match:
        val = float(above_match.group(1))
        filters["cocoa_percentage"] = (val, 100)
        
    # Handle "below/under/<"
    below_match = re.search(r"(?:below|under|less than|lower than|<)[\s]?(\d{1,3})", q)
    if below_match:
        val = float(below_match.group(1))
        existing_min = filters.get("cocoa_percentage", (0, 100))[0]
        filters["cocoa_percentage"] = (existing_min, val)

    # EXACT Percentage (e.g. "100%", "85%")
    # Matches "100%" or "85 %"
    exact_match = re.search(r"\b(\d{1,3})\s?%", q)
    if exact_match:
        val = float(exact_match.group(1))
        # Override any previous broad range with a tight specific range
        # We use a small epsilon (val-1, val+1) to handle potential rounding differences in data
        filters["cocoa_percentage"] = (val - 1, val + 1)


    # --- PRICE ---
    price_match = re.search(r"under\s+(\d+)", q)
    if price_match:
        filters["price_range"] = (0, float(price_match.group(1)))

    # --- DIETARY ---
    if "vegan" in q:
        filters.setdefault("dietary_exclusions", []).append("non-vegan")

    if "gluten free" in q or "gluten-free" in q:
        filters.setdefault("dietary_exclusions", []).append("gluten")

    # --- ALLERGENS & INCLUSIONS ---
    # Robust Nut Exclusion
    if re.search(r"\b(nut\s?free|no\s+nuts?|without\s+(?:any\s+)?nuts?)\b", q):
        nut_types = ["nuts", "hazelnuts", "almonds", "pecans", "walnuts", "cashews", "pistachios", "macadamia", "peanut", "groundnut"]
        filters.setdefault("exclude_allergens", []).extend(nut_types)

    # Fruit Exclusion
    if re.search(r"\b(fruit\s?free|no\s+fruits?|without\s+(?:any\s+)?fruits?|no\s+berries)\b", q):
        fruit_types = ["fruit", "berries", "cranberry", "blueberry", "strawberry", "raspberry", "cherry", "orange", "lemon", "lime", "citrus"]
        filters.setdefault("exclude_allergens", []).extend(fruit_types)

    # Plain Logic (Exclude all common inclusions)
    if "plain" in q or "naked" in q or "pure" in q:
        # 'Plain' implies no nuts, no fruit
        nut_types = ["nuts", "hazelnuts", "almonds", "pecans", "walnuts", "cashews", "pistachios", "macadamia", "peanut", "groundnut"]
        fruit_types = ["fruit", "berries", "cranberry", "blueberry", "strawberry", "raspberry", "cherry", "orange", "lemon", "lime", "citrus"]
        filters.setdefault("exclude_allergens", []).extend(nut_types + fruit_types)

    if "dairy free" in q or "no dairy" in q or "without milk" in q or "vegan" in q:
         filters.setdefault("exclude_allergens", []).append("milk")

    # --- COUNTRY ---
    country = normalize_country_from_query(query)
    if country:
        # Known Non-Producers (Consumer Countries) -> Must be Maker
        # (Cacao does not grow in these climates)
        non_producers = [
            "Switzerland", "Belgium", "France", "Germany", "Italy", "UK", 
            "Canada", "Japan", "USA", "Netherlands", "Austria", "Spain",
            "Poland", "Denmark", "Sweden", "Norway", "Ireland", "Iceland"
        ]
        
        # Origin Trigger Keywords (Expanded & Robust)
        origin_triggers = [
            "bean", "cocoa", "cacao", "origin", "sourced", "harvest", 
            "grown", "plantation", "estate", "farm", "single origin"
        ]
        
        is_origin_request = any(t in q for t in origin_triggers)
        
        if country in non_producers:
            # You can't have Swiss-grown beans.
            filters["maker_country"] = country
        elif is_origin_request:
            # "Beans from Ecuador"
            filters["origin_country"] = country
        else:
            # "Ecuador chocolate" -> Default to Maker (e.g. Pacari is Ecuadorian Maker)
            # This is ambiguous, but Maker is usually the primary mental model.
            filters["maker_country"] = country

    return filters

import re

def filter_ids(index, filters):
    """
    Deterministic Channel A filter.
    index: ChannelAIndex
    filters: dict
    returns: sorted list of product IDs
    """
    try:
        # start from all IDs
        candidate_ids = set(index.cocoa.keys())

        # --- ENUM filters ---
        if "maker_country" in filters:
            # Expected filter value: "Switzerland", "USA", etc.
            target = filters["maker_country"]
            candidate_ids &= index.maker_countries.get(target, set())

        if "origin_country" in filters:
            target = filters["origin_country"]
            candidate_ids &= index.origin_countries.get(target, set())

        if "type" in filters:
            candidate_ids &= index.by_type.get(filters["type"], set())

        if "format" in filters:
            candidate_ids &= index.by_format.get(filters["format"], set())

        # --- EXCLUSIONS ---
        if "exclude_types" in filters:
            for t in filters["exclude_types"]:
                candidate_ids -= index.by_type.get(t, set())

        if "exclude_allergens" in filters:

            banned = set(filters["exclude_allergens"])
            candidate_ids = {
                cid for cid in candidate_ids
                if not banned.intersection(index.allergens.get(cid, []))
            }

        if "dietary_exclusions" in filters:
            banned = set(filters["dietary_exclusions"])
            candidate_ids = {
                cid for cid in candidate_ids
                if not banned.intersection(index.dietary.get(cid, []))
            }

        # --- NUMERIC RANGES ---
        if "cocoa_percentage" in filters:
            min_p, max_p = filters["cocoa_percentage"]
            # Robust filtering: Handle None or bad types
            filtered = set()
            for cid in candidate_ids:
                val = index.cocoa.get(cid)
                try:
                    if val is not None:
                        # Clean string if needed
                        val_clean = str(val).replace("%", "").strip()
                        if min_p <= float(val_clean) <= max_p:
                            filtered.add(cid)
                except (ValueError, TypeError):
                    continue
            candidate_ids = filtered
            
        if "price_range" in filters:
            min_p, max_p = filters["price_range"]
            filtered = set()
            for cid in candidate_ids:
                val = index.prices.get(cid)
                try:
                    if val is not None:
                        # SUPER ROBUST PRICE CLEANING
                        # Remove everything that is not a digit or a dot
                        val_clean = re.sub(r'[^\d.]', '', str(val))
                        if val_clean and min_p <= float(val_clean) <= max_p:
                            filtered.add(cid)
                except (ValueError, TypeError):
                    continue
            candidate_ids = filtered

        # --- FLAVOR KEYWORDS (Hard Filter) ---
        if "flavor_keywords" in filters:
            keywords = filters["flavor_keywords"]
            filtered = set()
            for cid in candidate_ids:
                blob = index.flavor_text.get(cid, "")
                # Product must contain AT LEAST ONE of the keywords? 
                # Or ALL? Let's go with ANY for now to be safe, or ALL if user asked "fruity AND nutty"?
                # Usually user queries are "fruity nutty chocolate" -> implication is intersection.
                # Let's enforce ALL keywords found in the parser.
                if all(k in blob for k in keywords):
                    filtered.add(cid)
            candidate_ids = filtered

        # --- PRICE MAX (Simpler Interface) ---
        if "price_max" in filters:
            max_p = filters["price_max"]
            filtered = set()
            for cid in candidate_ids:
                val = index.prices.get(cid)
                try:
                    if val is not None:
                        val_clean = re.sub(r'[^\d.]', '', str(val))
                        if val_clean and float(val_clean) <= max_p:
                            filtered.add(cid)
                except (ValueError, TypeError):
                    continue
            candidate_ids = filtered


        return sorted(candidate_ids)
    except Exception as e:
        print(f"Filter Error: {e}")
        # Safe Fallback: Return everything if filter logic explodes
        return sorted(list(index.cocoa.keys()))

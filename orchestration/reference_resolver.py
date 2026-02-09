def resolve_reference(query, products, forced_index=None):
    if not products: return "No products in memory.", None
    q = query.lower()
    index = forced_index
    
    if index is None:
        if q.isdigit():
            val = int(q)
            if 1 <= val <= len(products): index = val - 1
        elif "first" in q: index = 0
        elif "second" in q: index = 1
        elif "third" in q: index = 2
        
    if index is None: return "Please specify which chocolate.", None
    
    p = products[index]
    return f"**{p.get('name')}** is a {p.get('cocoa_percentage')}% cocoa bar from {p.get('maker_country')}.", index

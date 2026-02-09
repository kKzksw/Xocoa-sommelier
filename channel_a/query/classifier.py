"""
Intent classifier: Determines if query is Channel A-compatible.
"""

class QueryIntent:
    CHANNEL_A_COMPATIBLE = "channel_a"
    SEMANTIC_ONLY = "semantic"
    AMBIGUOUS = "ambiguous"

class IntentClassifier:
    """Classifies user queries for routing."""
    
    # Keywords that indicate factual constraints
    FACTUAL_INDICATORS = {
        'origin', 'country', 'from', 'made in', 'produced in',
        'cocoa', 'percent', '%', 'cacao',
        'milk', 'dark', 'white', 'ruby',
        'bean', 'variety', 'criollo', 'forastero', 'trinitario',
        'organic', 'fair trade', 'single origin',
        'craft', 'bean to bar', 'tree to bar',
        'limited edition', 'price', 'under', 'above',
        'brand', 'maker'
    }
    
    # Keywords that indicate semantic/taste queries
    SEMANTIC_INDICATORS = {
        'fruity', 'floral', 'nutty', 'earthy', 'smooth', 'bitter',
        'sweet', 'complex', 'bold', 'delicate', 'creamy',
        'pairing', 'pairs with', 'goes well',
        'mood', 'occasion', 'gift',
        'best', 'recommend', 'similar to', 'like'
    }
    
    @classmethod
    def classify(cls, query: str) -> str:
        """
        Classify query intent.
        
        Returns:
            QueryIntent constant
        """
        query_lower = query.lower()
        
        has_factual = any(indicator in query_lower 
                         for indicator in cls.FACTUAL_INDICATORS)
        has_semantic = any(indicator in query_lower 
                          for indicator in cls.SEMANTIC_INDICATORS)
        
        if has_factual and not has_semantic:
            return QueryIntent.CHANNEL_A_COMPATIBLE
        elif has_semantic and not has_factual:
            return QueryIntent.SEMANTIC_ONLY
        else:
            return QueryIntent.AMBIGUOUS  # Needs both channels
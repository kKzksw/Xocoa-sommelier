"""
Filter builder: Converts extracted entities to Channel A filter dict.
"""

from typing import Dict, Any

class FilterBuilder:
    """Builds Channel A filter dicts from extracted entities."""
    
    @staticmethod
    def build(entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert entities to Channel A filter format.
        
        Performs validation and normalization.
        """
        filters = {}
        
        # Direct mappings (no transformation needed)
        direct_fields = [
            'origin_country', 'maker_country', 'type', 
            'bean_variety', 'production_craft_level',
            'limited_edition', 'brand', 'maker_name'
        ]
        
        for field in direct_fields:
            if field in entities:
                filters[field] = entities[field]
        
        # Range mappings
        if 'cocoa_min' in entities:
            filters['cocoa_min'] = entities['cocoa_min']
        if 'cocoa_max' in entities:
            filters['cocoa_max'] = entities['cocoa_max']
        
        if 'price_max' in entities:
            filters['price_max'] = entities['price_max']
        
        return filters
    
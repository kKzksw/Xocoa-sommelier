"""
Entity extraction: Pulls factual constraints from text.
Uses rule-based patterns + optional LLM validation.
"""

import re
from typing import Dict, List, Optional, Any

class EntityExtractor:
    """Extracts Channel A entities from natural language."""
    
    # Country name normalization (expand as needed)
    COUNTRY_ALIASES = {
        'trinidad': 'trinidad and tobago',
        'venezuela': 'venezuela',
        'ecuador': 'ecuador',
        'peru': 'peru',
        'madagascar': 'madagascar',
        'swiss': 'switzerland',
        'switzerland': 'switzerland',
        'french': 'france',
        'france': 'france',
        'italian': 'italy',
        'italy': 'italy',
        'belgian': 'belgium',
        'belgium': 'belgium',
        'brazil': 'brazil',
        'colombia': 'colombia',
        'mexico': 'mexico',
        'ghana': 'ghana',
        'ivory coast': 'ivory coast',
        'costa rica': 'costa rica',
        'dominican republic': 'dominican republic',
        'jamaica': 'jamaica',
        'grenada': 'grenada',
        'belize': 'belize',
        'bolivia': 'bolivia',
        'nicaragua': 'nicaragua',
        'philippines': 'philippines',
        'vietnam': 'vietnam',
        'india': 'india',
        'papua new guinea': 'papua new guinea',
        'uganda': 'uganda',
        'tanzania': 'tanzania',
        'sao tome': 'sao tome and principe',
        'hawaii': 'united states',
        'usa': 'united states',
        'us': 'united states',
        'united states': 'united states',
        'uk': 'united kingdom',
        'britain': 'united kingdom',
        'united kingdom': 'united kingdom',
        'germany': 'germany',
        'austria': 'austria',
        'spain': 'spain',
        'japan': 'japan',
    }
    
    # Type normalization
    TYPE_ALIASES = {
        'milk': 'milk',
        'dark': 'dark',
        'white': 'white',
        'ruby': 'ruby',
        'blonde': 'blonde'
    }
    
    def extract(self, query: str) -> Dict[str, Any]:
        """
        Extract entities from query.
        
        Returns dict with possible keys:
        - origin_country
        - maker_country
        - type
        - cocoa_min, cocoa_max
        - bean_variety
        - production_craft_level
        - limited_edition
        - price_max
        """
        query_lower = query.lower()
        entities = {}
        
        # Extract cocoa percentage
        cocoa = self._extract_cocoa(query_lower)
        if cocoa:
            entities.update(cocoa)
        
        # Extract countries
        countries = self._extract_countries(query_lower)
        if countries:
            entities.update(countries)
        
        # Extract chocolate type
        choc_type = self._extract_type(query_lower)
        if choc_type:
            entities['type'] = choc_type
        
        # Extract bean variety
        bean = self._extract_bean_variety(query_lower)
        if bean:
            entities['bean_variety'] = bean
        
        # Extract craft level
        craft = self._extract_craft_level(query_lower)
        if craft:
            entities['production_craft_level'] = craft
        
        # Extract limited edition flag
        if 'limited edition' in query_lower or 'limited-edition' in query_lower:
            entities['limited_edition'] = True
        
        return entities
    
    def _extract_cocoa(self, query: str) -> Optional[Dict[str, int]]:
        """Extract cocoa percentage constraints."""
        result = {}
        
        # Pattern: "above/over/at least X%"
        match = re.search(r'(?:above|over|at least|minimum)\s*(\d+)\s*%?', query)
        if match:
            result['cocoa_min'] = int(match.group(1))
        
        # Pattern: "below/under/maximum X%"
        match = re.search(r'(?:below|under|maximum|max)\s*(\d+)\s*%?', query)
        if match:
            result['cocoa_max'] = int(match.group(1))
        
        # Pattern: "X% cocoa" or "X percent"
        match = re.search(r'(\d+)\s*(?:%|percent)', query)
        if match and not result:
            # Exact match - use as minimum
            result['cocoa_min'] = int(match.group(1))
        
        return result if result else None
    
    def _extract_countries(self, query: str) -> Optional[Dict[str, str]]:
        """Extract origin/maker country."""
        result = {}
        
        for alias, canonical in self.COUNTRY_ALIASES.items():
            # Pattern 1: Explicit origin markers
            if re.search(rf'\b{alias}\b.*(?:origin|bean|from)', query) or \
               re.search(rf'(?:origin|bean|from).*\b{alias}\b', query):
                result['origin_country'] = canonical
                continue
            
            # Pattern 2: "made in X" = maker country
            if re.search(rf'\bmade in\s+{alias}\b', query):
                result['maker_country'] = canonical
                continue
            
            # Pattern 3: Just "X chocolate" = assume origin
            if re.search(rf'\b{alias}\b\s+chocolate', query):
                result['origin_country'] = canonical
                continue
            
            # Pattern 4: "chocolate from X" = origin
            if re.search(rf'chocolate.*\b{alias}\b', query):
                result['origin_country'] = canonical
                continue
        
        return result if result else None
    
    def _extract_type(self, query: str) -> Optional[str]:
        """Extract chocolate type."""
        for alias, canonical in self.TYPE_ALIASES.items():
            if re.search(rf'\b{alias}\b', query):
                return canonical
        return None
    
    def _extract_bean_variety(self, query: str) -> Optional[str]:
        """Extract bean variety."""
        varieties = ['criollo', 'forastero', 'trinitario', 'nacional']
        for variety in varieties:
            if variety in query:
                return variety
        return None
    
    def _extract_craft_level(self, query: str) -> Optional[str]:
        """Extract production craft level."""
        if 'bean to bar' in query or 'bean-to-bar' in query:
            return 'bean-to-bar'
        if 'tree to bar' in query or 'tree-to-bar' in query:
            return 'tree-to-bar'
        if 'craft' in query:
            return 'craft'
        return None
        
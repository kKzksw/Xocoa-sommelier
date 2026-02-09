# channel_a/normalization/normalize.py
import re


def normalize_text(value):
    if not value:
        return None
    return value.strip().lower()


def normalize_type(value):
    return normalize_text(value)


def normalize_format(value):
    return normalize_text(value)


def normalize_cocoa_percentage(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def normalize_price(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def normalize_allergens(value):
    if not value:
        return []
    return [v.strip().lower() for v in value.split(",")]


def normalize_dietary(value):
    if not value:
        return []
    return [v.strip().lower() for v in value.split(",")]


def normalize_boolean(value):
    if value in ("", None):
        return False
    return bool(value)

COUNTRY_ALIASES = {
    "France": ["french", "français", "francaise", "française"],
    "Switzerland": ["swiss", "suisse", "schweiz", "switzerland"],
    "Belgium": ["belgian", "belgique", "belgium"],
    "Germany": ["german", "allemagne", "deutschland", "germany"],
    "Italy": ["italian", "italie", "italy"],
    "USA": ["american", "u.s.", "u.s.a.", "usa", "united states", "america", "united states of america"],
    "UK": ["british", "u.k.", "uk", "united kingdom", "great britain", "britain", "england", "english"],
    "Japan": ["japanese", "japan", "jp"],
    "Vietnam": ["vietnamese", "vietnam", "vn"],
    "Ecuador": ["ecuadorian", "ecuador"],
    "Peru": ["peruvian", "peru"],
    "Venezuela": ["venezuelan", "venezuela"],
    "Madagascar": ["madagascan", "madagascar"],
    "Spain": ["spanish", "spain", "españa"],
    "Austria": ["austrian", "austria", "österreich"],
    "India": ["indian", "india"],
    "Brazil": ["brazilian", "brazil", "brasil"],
    "Canada": ["canadian", "canada"],
    "Mexico": ["mexican", "mexico"],
    "Grenada": ["grenadian", "grenada"],
    "Trinidad": ["trinidadian", "trinidad", "trinidad and tobago", "tobago"],
    "Colombia": ["colombian", "colombia"],
    "Nicaragua": ["nicaraguan", "nicaragua"],
    "Guatemala": ["guatemalan", "guatemala"],
    "Bolivia": ["bolivian", "bolivia"],
    "Honduras": ["honduran", "honduras"],
    "Costa Rica": ["costa rican", "costa rica"],
    "Denmark": ["danish", "denmark"],
    "Sweden": ["swedish", "sweden"],
    "Norway": ["norwegian", "norway"],
    "Iceland": ["icelandic", "iceland"],
    "Netherlands": ["dutch", "netherlands", "holland"],
    "Poland": ["polish", "poland"],
    "Hungary": ["hungarian", "hungary"],
    "Lithuania": ["lithuanian", "lithuania"],
    "Australia": ["australian", "australia"],
    "New Zealand": ["nz", "new zealand", "kiwi"]
}

def normalize_country_for_index(value):
    """
    Standardizes a country string from the DB to a canonical name.
    e.g. "United States" -> "USA"
    """
    if not value or value.lower() in ["unknown", "not specified"]:
        return "Unknown"
    
    val_lower = value.lower().strip()
    
    # Reverse lookup in aliases
    for canonical, aliases in COUNTRY_ALIASES.items():
        if val_lower == canonical.lower() or val_lower in aliases:
            return canonical
            
    return value.title() # Default fallback (e.g. "Fiji" -> "Fiji")

def normalize_country_from_query(query: str):
    if not query:
        return None

    q = query.lower()
    
    # Match whole words to avoid false positives (e.g., "us" in "must")
    for canonical, aliases in COUNTRY_ALIASES.items():
        # also match the canonical name itself in lowercase
        candidates = [canonical.lower()] + [a.lower() for a in aliases]
        for token in candidates:
            # treat dots in abbreviations as optional punctuation
            token_re = re.escape(token).replace(r"\.", r"[\. ]?")
            if re.search(rf"\b{token_re}\b", q):
                return canonical
            
    return None
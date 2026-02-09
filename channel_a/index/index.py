# channel_a/index.py

import json
from channel_a.normalization.normalize import *


class ChannelAIndex:
    def __init__(self, chocolates):
        self.chocolates = chocolates
        self.by_type = {}
        self.by_format = {}
        self.prices = {}
        self.cocoa = {}
        self.allergens = {}
        self.dietary = {}
        self.currency = {}
        self.limited = {}
        self.maker_countries = {} # {Country: {id1, id2...}}
        self.origin_countries = {} # {Country: {id1, id2...}}

        self._build()

    def _build(self):
        for item in self.chocolates:
            cid = item["id"]
            name = item.get("name", "")

            # --- Data Quality Shield (Elite Operator Fix) ---
            # Skip items that look like books or noise
            if len(name) > 100 or " by " in name.lower() or "author" in name.lower():
                continue

            # --- Country Indexing ---
            mc = normalize_country_for_index(item.get("maker_country"))
            if mc:
                self.maker_countries.setdefault(mc, set()).add(cid)

            oc = normalize_country_for_index(item.get("origin_country"))
            if oc:
                self.origin_countries.setdefault(oc, set()).add(cid)

            # --- Type Inference (Data Intelligence Fix) ---
            raw_type = item.get("type")
            if not raw_type:
                # Infer from name
                name = item.get("name", "").lower()
                cocoa = normalize_cocoa_percentage(item.get("cocoa_percentage"))
                
                if any(word in name for word in ["milk", "lait", "leche"]):
                    raw_type = "milk"
                elif any(word in name for word in ["white", "blanc", "blanco"]):
                    raw_type = "white"
                elif cocoa and cocoa >= 60:
                    raw_type = "dark"
                else:
                    raw_type = "unknown"

            t = normalize_type(raw_type)
            if t:
                self.by_type.setdefault(t, set()).add(cid)

            f = normalize_format(item.get("format"))
            if f:
                self.by_format.setdefault(f, set()).add(cid)

            self.cocoa[cid] = normalize_cocoa_percentage(
                item.get("cocoa_percentage")
            )

            self.prices[cid] = normalize_price(
                item.get("price_retail")
            )

            self.currency[cid] = normalize_text(
                item.get("price_currency")
            )

            self.limited[cid] = normalize_boolean(
                item.get("limited_edition")
            )

            self.allergens[cid] = normalize_allergens(
                item.get("allergens")
            )

            self.dietary[cid] = normalize_dietary(
                item.get("dietary")
            )

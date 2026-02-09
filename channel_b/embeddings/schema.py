def rating_to_language(rating: float | None) -> str | None:
    if rating is None:
        return None
    if rating >= 4.5:
        return "exceptionally well rated"
    if rating >= 4.0:
        return "highly rated"
    if rating >= 3.5:
        return "well rated"
    if rating >= 3.0:
        return "moderately rated"
    return "low rated"


def build_embedding_text(product: dict) -> str:
    sections = []

    # ---------- SENSORY ----------
    sensory = []

    if product.get("flavor_notes_primary"):
        sensory.append(f"Primary flavors: {product['flavor_notes_primary']}")
    if product.get("flavor_notes_secondary"):
        sensory.append(f"Secondary flavors: {product['flavor_notes_secondary']}")
    if product.get("aroma_notes"):
        sensory.append(f"Aroma: {product['aroma_notes']}")

    textures = [
        product.get("texture_mouthfeel"),
        product.get("texture_melt"),
        product.get("texture_snap"),
        product.get("texture_grain"),
    ]
    textures = [t for t in textures if t]
    if textures:
        sensory.append("Texture: " + ", ".join(textures))

    finishes = [
        product.get("finish_length"),
        product.get("finish_character"),
        product.get("finish_aftertaste"),
    ]
    finishes = [f for f in finishes if f]
    if finishes:
        sensory.append("Finish: " + ", ".join(finishes))

    if sensory:
        sections.append("SENSORY PROFILE:\n" + "\n".join(sensory))

    # ---------- PROCESSING ----------
    processing = []

    if product.get("processing_fermentation_method"):
        processing.append(f"Fermentation: {product['processing_fermentation_method']}")
    if product.get("processing_drying_method"):
        processing.append(f"Drying: {product['processing_drying_method']}")
    if product.get("processing_roasting_profile"):
        processing.append(f"Roasting: {product['processing_roasting_profile']}")
    if product.get("processing_conching_type"):
        processing.append(f"Conching: {product['processing_conching_type']}")
    if product.get("processing_tempering"):
        processing.append(f"Tempering: {product['processing_tempering']}")
    if product.get("bean_variety"):
        processing.append(f"Bean variety: {product['bean_variety']}")
    if product.get("production_method") or product.get("production_craft_level"):
        processing.append(
            "Production style: "
            + ", ".join(v for v in [
                product.get("production_method"),
                product.get("production_craft_level")
            ] if v)
        )

    if processing:
        sections.append("PROCESSING & CRAFT:\n" + "\n".join(processing))

    # ---------- MAKER ----------
    maker = []

    if product.get("maker_philosophy"):
        maker.append(f"Maker philosophy: {product['maker_philosophy']}")
    if product.get("maker_specialties"):
        maker.append(f"Maker specialties: {product['maker_specialties']}")
    if product.get("maker_established"):
        maker.append("Maker background: established mid 20th century")
    maker.append("Maker country: unknown origin")

    if maker:
        sections.append("MAKER STYLE:\n" + "\n".join(maker))

    # ---------- QUALITY ----------
    quality = []

    rating_text = rating_to_language(product.get("rating"))
    if rating_text:
        quality.append(f"Overall quality: {rating_text}")
    if product.get("expert_review"):
        quality.append(f"Expert review: {product['expert_review']}")
    if product.get("quality_indicators_consistency"):
        quality.append(
            f"Quality indicators: {product['quality_indicators_consistency']}"
        )

    if quality:
        sections.append("QUALITY & RECOGNITION:\n" + "\n".join(quality))

    # ---------- SUSTAINABILITY ----------
    sustainability = []

    if product.get("sustainability_packaging"):
        sustainability.append(f"Packaging: {product['sustainability_packaging']}")
    if product.get("sustainability_carbon_neutral") is not None:
        sustainability.append(
            "Carbon neutral status: "
            + ("carbon neutral" if product["sustainability_carbon_neutral"] else "not carbon neutral")
        )

    if sustainability:
        sections.append("SUSTAINABILITY:\n" + "\n".join(sustainability))

    # ---------- PAIRING ----------
    pairings = [v for k, v in product.items() if k.startswith("pairings_") and v]
    serving = [v for k, v in product.items() if k.startswith("serving_") and v]

    if pairings or serving:
        block = []
        if pairings:
            block.append("Pairings: " + ", ".join(pairings))
        if serving:
            block.append("Serving suggestions: " + ", ".join(serving))
        sections.append("PAIRING & SERVING:\n" + "\n".join(block))

    return "\n\n".join(sections)

from orchestration.recommender import RecommenderService


class DummyChannelA:
    def __init__(self, chocolates):
        self.index = type("Index", (), {"chocolates": chocolates})()

    def run(self, query):
        return [int(p["id"]) for p in self.index.chocolates]


class DummyChannelB:
    def rank_with_scores(self, candidate_ids, semantic_query, top_k, min_score=0.35):
        scored = []
        for i, pid in enumerate(candidate_ids):
            scored.append((int(pid), 0.99 - (0.01 * i)))
        return scored[:top_k]


def test_diversity_reranking_limits_brand_and_origin():
    chocolates = [
        {"id": 1, "brand": "A", "origin_country": "Peru", "flavor_notes_primary": "fruit"},
        {"id": 2, "brand": "A", "origin_country": "Peru", "flavor_notes_primary": "berry"},
        {"id": 3, "brand": "A", "origin_country": "Peru", "flavor_notes_primary": "nut"},
        {"id": 4, "brand": "B", "origin_country": "Peru", "flavor_notes_primary": "nut"},
        {"id": 5, "brand": "C", "origin_country": "Ecuador", "flavor_notes_primary": "spice"},
        {"id": 6, "brand": "D", "origin_country": "Ecuador", "flavor_notes_primary": "caramel"},
    ]

    recommender = RecommenderService(DummyChannelA(chocolates), DummyChannelB())
    out = recommender.recommend("anything", top_k=5, segment=None, state={}, hard_filters={})

    ranked = out["ranked"]
    brands = {}
    origins = {}
    for pid in ranked:
        product = recommender.product_by_id[pid]
        b = product.get("brand", "").lower()
        o = product.get("origin_country", "").lower()
        brands[b] = brands.get(b, 0) + 1
        origins[o] = origins.get(o, 0) + 1

    assert all(count <= 2 for count in brands.values())
    assert all(count <= 2 for count in origins.values())

    profiles = {recommender._flavor_profile_from_product(recommender.product_by_id[pid]) for pid in ranked[:5]}
    assert len(profiles) >= 2


def test_missing_metadata_tolerance_uses_soft_relaxation_for_budget():
    chocolates = [
        {"id": 10, "brand": "X", "origin_country": "Peru", "price_retail": None, "flavor_notes_primary": "fruit"},
        {"id": 11, "brand": "Y", "origin_country": "Peru", "price_retail": "45.0", "flavor_notes_primary": "nut"},
    ]

    recommender = RecommenderService(DummyChannelA(chocolates), DummyChannelB())
    out = recommender.recommend(
        "budget chocolate",
        top_k=5,
        segment="Uninvolved",
        state={"budget": "under $10"},
        hard_filters={"budget": "under $10"},
    )

    assert out["ranked"] == [10]
    explanation = out.get("explanation_layer", {})
    assert "budget" in explanation.get("relaxed_preferences", [])
    assert explanation.get("tradeoff")


def test_origin_hard_filter_matches_maker_or_bean_origin_country():
    chocolates = [
        {"id": 20, "brand": "A", "maker_country": "France", "origin_country": "Peru", "flavor_notes_primary": "fruit"},
        {"id": 21, "brand": "B", "maker_country": "USA", "origin_country": "France", "flavor_notes_primary": "nut"},
        {"id": 22, "brand": "C", "maker_country": "USA", "origin_country": "Peru", "flavor_notes_primary": "spice"},
    ]

    recommender = RecommenderService(DummyChannelA(chocolates), DummyChannelB())
    out = recommender.recommend(
        "chocolate from france",
        top_k=5,
        segment=None,
        state={"origin": "France"},
        hard_filters={"origin": "France"},
    )

    assert out["ranked"] == [20, 21]
    explanation = out.get("explanation_layer", {})
    assert "origin" in explanation.get("matched_preferences", [])


def test_origin_scope_controls_country_matching_dimension():
    chocolates = [
        {"id": 40, "brand": "A", "maker_country": "France", "origin_country": "Peru", "flavor_notes_primary": "fruit"},
        {"id": 41, "brand": "B", "maker_country": "USA", "origin_country": "France", "flavor_notes_primary": "nut"},
    ]

    recommender = RecommenderService(DummyChannelA(chocolates), DummyChannelB())

    out_maker = recommender.recommend(
        "chocolate from france",
        top_k=5,
        segment=None,
        state={"origin": "France", "origin_scope": "maker_country"},
        hard_filters={"origin": "France", "origin_scope": "maker_country"},
    )
    assert out_maker["ranked"] == [40]

    out_origin = recommender.recommend(
        "chocolate from france",
        top_k=5,
        segment=None,
        state={"origin": "France", "origin_scope": "origin_country"},
        hard_filters={"origin": "France", "origin_scope": "origin_country"},
    )
    assert out_origin["ranked"] == [41]


def test_origin_unknown_metadata_is_soft_relaxed_instead_of_hard_drop():
    chocolates = [
        {"id": 30, "brand": "A", "maker_country": "", "origin_country": "", "flavor_notes_primary": "fruit"},
        {"id": 31, "brand": "B", "maker_country": "USA", "origin_country": "Peru", "flavor_notes_primary": "nut"},
    ]

    recommender = RecommenderService(DummyChannelA(chocolates), DummyChannelB())
    out = recommender.recommend(
        "chocolate from france",
        top_k=5,
        segment=None,
        state={"origin": "France"},
        hard_filters={"origin": "France"},
    )

    assert out["ranked"] == [30]
    explanation = out.get("explanation_layer", {})
    assert "origin" in explanation.get("relaxed_preferences", [])

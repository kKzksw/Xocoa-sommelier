from orchestration.conversation_policy import (
    describe_candidate_pool,
    generate_sommelier_question,
    select_next_best_attribute,
)


def _sample_pool():
    return [
        {
            "id": 1,
            "name": "Berry Noir",
            "brand": "Maison X",
            "maker_country": "France",
            "origin_country": "Peru",
            "cocoa_percentage": "72",
            "price_retail": "14",
            "flavor_notes_primary": "berry",
            "flavor_notes_secondary": "fig",
            "tasting_notes": "bright fruit",
            "type": "dark",
        },
        {
            "id": 2,
            "name": "Fig Atelier",
            "brand": "Maison X",
            "maker_country": "France",
            "origin_country": "Peru",
            "cocoa_percentage": "71",
            "price_retail": "13",
            "flavor_notes_primary": "fig",
            "flavor_notes_secondary": "raisin",
            "tasting_notes": "dried fruit",
            "type": "dark",
        },
        {
            "id": 3,
            "name": "Caramel Crest",
            "brand": "Maison X",
            "maker_country": "France",
            "origin_country": "Peru",
            "cocoa_percentage": "70",
            "price_retail": "15",
            "flavor_notes_primary": "caramel",
            "flavor_notes_secondary": "hazelnut",
            "tasting_notes": "toffee and nuts",
            "type": "dark",
        },
        {
            "id": 4,
            "name": "Nutty Reserve",
            "brand": "Maison X",
            "maker_country": "France",
            "origin_country": "Peru",
            "cocoa_percentage": "69",
            "price_retail": "16",
            "flavor_notes_primary": "hazelnut",
            "flavor_notes_secondary": "praline",
            "tasting_notes": "roasted nuts",
            "type": "dark",
        },
    ]


def test_describe_candidate_pool_mentions_count_and_filters():
    text = describe_candidate_pool(
        candidate_count=65,
        applied_filters={"chocolate_type": "dark", "flavor_direction": "fruity"},
    )
    assert "65" in text
    assert "fruity dark chocolates" in text.lower()
    assert "great choice" not in text.lower()


def test_describe_candidate_pool_avoids_duplicate_dark_dark_phrase():
    text = describe_candidate_pool(
        candidate_count=1068,
        applied_filters={"chocolate_type": "dark", "flavor_direction": "dark"},
    )
    assert "dark dark chocolates" not in text.lower()
    assert "dark chocolates" in text.lower()


def test_select_next_best_attribute_prefers_high_impact_split():
    attr = select_next_best_attribute(_sample_pool(), state={})
    assert attr == "flavor_direction"


def test_select_next_best_attribute_skips_already_asked_field():
    attr = select_next_best_attribute(
        _sample_pool(),
        state={"_asked_fields": "flavor_direction"},
    )
    assert attr != "flavor_direction"


def test_generate_sommelier_question_returns_single_question_with_options():
    out = generate_sommelier_question(
        attribute="intensity",
        state={"chocolate_type": "dark"},
        candidate_count=114,
        applied_filters={"chocolate_type": "dark"},
        user_message="dark chocolate",
    )
    assert "114" in out["question"]
    assert "intense" in out["question"].lower()
    assert out["answer_options"] == ["Bold / Intense", "Smooth / Creamy", "No preference"]


def test_generate_sommelier_question_handles_ambiguity_with_tasting_flight():
    out = generate_sommelier_question(
        attribute="flavor_direction",
        state={"chocolate_type": "dark"},
        candidate_count=80,
        applied_filters={"chocolate_type": "dark"},
        user_message="whatever",
    )
    assert "three directions" in out["question"].lower()
    assert "Show a tasting flight" in out["answer_options"]

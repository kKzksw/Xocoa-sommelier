from orchestration.agentic_sommelier_engine import (
    agent_step,
    build_agentic_filters,
    build_agentic_retrieval_query,
    normalize_state,
    set_ambiguity_helper,
    update_state_from_message,
)


def test_segment_is_mandatory_first_step():
    state = normalize_state({})
    out = agent_step("I want dark chocolate", state, candidate_count=200)
    assert out["action"] == "ASK"
    assert "When choosing chocolate" in out["question"]
    assert out["answer_options"] == ["A", "B", "C"]


def test_country_scope_is_asked_before_segment_when_country_is_explicit():
    state = normalize_state({})
    out = agent_step("I want chocolate from france", state, candidate_count=200)
    assert out["action"] == "ASK"
    assert "which one do you mean" in out["question"].lower()
    assert "Made in that country" in out["answer_options"]


def test_tiny_candidate_pool_skips_extra_questions_and_retrieves():
    state = normalize_state({})
    out = agent_step("I want chocolate from france", state, candidate_count=3, total_catalog_count=2000)
    assert out["action"] == "RETRIEVE"


def test_country_scope_answer_is_parsed_into_state():
    state = normalize_state({"origin": "France"})
    updated = update_state_from_message("Cocoa bean origin from that country", state)
    assert updated["origin_scope"] == "origin_country"
    assert updated["origin"] == "France"


def test_country_scope_option_one_text_is_parsed():
    state = normalize_state({"origin": "France"})
    updated = update_state_from_message("1) Made by brands/manufacturers in that country", state)
    assert updated["origin_scope"] == "maker_country"
    assert updated["origin"] == "France"


def test_country_scope_loop_is_prevented_after_unparsed_reply():
    state = normalize_state(
        {
            "origin": "France",
            "_clarification_turns": "1",
            "_asked_fields": "origin_scope",
            "_last_asked_field": "origin_scope",
        }
    )
    out = agent_step("the first interpretation", state, candidate_count=300)
    assert out["action"] == "ASK"
    assert "which one do you mean" not in out["question"].lower()
    assert "when choosing chocolate" in out["question"].lower()
    assert out["updated_state"]["origin_scope"] == "maker_country"


def test_missing_required_field_triggers_ask_with_budget_options():
    state = normalize_state({"segment": "Uninvolved"})
    out = agent_step("something nice", state, candidate_count=220)
    assert out["action"] == "ASK"
    assert "budget" in out["question"].lower()
    assert out["answer_options"]


def test_options_first_for_chocolate_type():
    state = normalize_state({"segment": "Impulsive-Involved"})
    out = agent_step("help", state, candidate_count=300)
    assert out["action"] == "ASK"
    assert "milk" in out["question"].lower()
    assert "Milk" in out["answer_options"]


def test_required_collected_still_asks_one_optional_on_first_turn():
    state = normalize_state({"segment": "Impulsive-Involved"})
    state = update_state_from_message("I prefer dark", state)
    out = agent_step("I prefer dark", state, candidate_count=999)
    assert out["action"] == "ASK"
    assert out["updated_state"]["_clarification_turns"] == "1"
    assert out["updated_state"]["_last_asked_field"] in {"flavor_direction", "intensity", "context"}


def test_after_one_optional_turn_scope_still_large_keeps_asking():
    state = normalize_state(
        {
            "segment": "Impulsive-Involved",
            "chocolate_type": "dark",
            "_clarification_turns": "1",
            "_asked_fields": "flavor_direction",
            "_last_asked_field": "flavor_direction",
        }
    )
    out = agent_step("nutty", state, candidate_count=500)
    assert out["action"] == "ASK"
    assert out["updated_state"]["_clarification_turns"] == "2"


def test_retrieve_when_optional_fields_are_exhausted():
    state = normalize_state(
        {
            "segment": "Impulsive-Involved",
            "chocolate_type": "dark",
            "_clarification_turns": "3",
            "_asked_fields": "context,flavor_direction,intensity",
            "_last_asked_field": "context",
        }
    )
    out = agent_step("still open", state, candidate_count=500)
    assert out["action"] == "RETRIEVE"


def test_stop_when_candidate_count_is_small_even_if_required_missing():
    state = normalize_state({"segment": "Rational Health-Conscious"})
    out = agent_step("not sure", state, candidate_count=50)
    assert out["action"] == "RETRIEVE"


def test_max_five_questions_forces_retrieve():
    state = normalize_state(
        {
            "segment": "Uninvolved",
            "_clarification_turns": "5",
        }
    )
    out = agent_step("anything", state, candidate_count=500)
    assert out["action"] == "RETRIEVE"


def test_ambiguous_any_response_triggers_tasting_flight_mode():
    state = normalize_state(
        {
            "segment": "Rational Health-Conscious",
            "certification": "organic",
            "dietary": "vegan",
            "cocoa_percentage": "70%",
            "context": "gift",
            "_clarification_turns": "2",
            "_ambiguous_turns": "1",
            "_asked_fields": "cocoa_percentage,context,dietary",
        }
    )
    out = agent_step("whatever", state, candidate_count=500)
    assert out["action"] == "RETRIEVE"
    assert out.get("fallback_mode") == "TASTING_FLIGHT"


def test_first_ambiguous_response_keeps_asking_detail_questions():
    state = normalize_state(
        {
            "segment": "Impulsive-Involved",
            "chocolate_type": "dark",
            "_clarification_turns": "1",
            "_asked_fields": "intensity",
            "_last_asked_field": "intensity",
            "_ambiguous_turns": "0",
        }
    )
    out = agent_step("whatever", state, candidate_count=500, total_catalog_count=2000)
    assert out["action"] == "ASK"
    assert out.get("fallback_mode") is None
    assert out["updated_state"]["_clarification_turns"] == "2"
    assert "which direction" not in out["question"].lower()


def test_llm_missing_fields_cannot_reask_already_asked_field():
    def helper(_message, _state, _fallback):
        return {"needs_more_info": True, "missing_fields": ["cocoa_percentage"]}

    set_ambiguity_helper(helper)
    try:
        state = normalize_state(
            {
                "segment": "Rational Health-Conscious",
                "certification": "organic",
                "_clarification_turns": "1",
                "_asked_fields": "cocoa_percentage",
                "_last_asked_field": "cocoa_percentage",
            }
        )
        out = agent_step("no", state, candidate_count=500, total_catalog_count=2000)
        assert out["action"] == "ASK"
        assert "cocoa percentage" not in out["question"].lower()
    finally:
        set_ambiguity_helper(None)


def test_dynamic_filter_payload_contains_hard_and_soft_fields():
    state = normalize_state(
        {
            "segment": "Impulsive-Involved",
            "origin": "France",
            "chocolate_type": "dark",
            "dietary": "vegan",
            "flavor_direction": "fruity",
            "_explicit_hard_fields": "origin",
        }
    )
    filters = build_agentic_filters(state)
    assert filters["explicit"]["origin"] == "France"
    assert filters["hard"]["origin"] == "France"
    assert filters["hard"]["chocolate_type"] == "dark"
    assert filters["hard"]["dietary"] == "vegan"
    assert filters["required"]["chocolate_type"] == "dark"
    assert filters["soft"]["flavor_direction"] == "fruity"


def test_origin_constraint_is_extracted_from_user_query():
    state = normalize_state({})
    updated = update_state_from_message("I want to buy chocolate from france", state)
    assert updated["origin"] == "France"
    assert "origin" in updated["_explicit_hard_fields"]


def test_retrieval_query_respects_priority_order():
    state = normalize_state(
        {
            "segment": "Impulsive-Involved",
            "origin": "France",
            "chocolate_type": "milk",
            "budget": "under $20",
            "flavor_direction": "sweet",
            "intensity": "smooth",
            "_explicit_hard_fields": "origin,budget",
        }
    )
    query = build_agentic_retrieval_query("show me options", state)
    parts = [chunk.strip() for chunk in query.split("|")]
    # Explicit constraints should be first among synthetic constraints.
    assert "origin: France" in parts[1]
    assert "budget: under $20" in parts[2]
    # Hard + required before soft preferences.
    assert parts.index("milk") < parts.index("flavor: sweet")
    assert parts.index("milk") < parts.index("intensity: smooth")


def test_probe_query_can_exclude_soft_preferences():
    state = normalize_state(
        {
            "segment": "Impulsive-Involved",
            "chocolate_type": "dark",
            "flavor_direction": "fruity",
            "intensity": "smooth",
            "_explicit_hard_fields": "chocolate_type",
        }
    )
    query = build_agentic_retrieval_query(
        "",
        state,
        include_soft_preferences=False,
        include_context=False,
    )
    assert "dark" in query
    assert "flavor: fruity" not in query
    assert "intensity: smooth" not in query


def test_no_answer_to_cocoa_question_does_not_erase_certification():
    state = normalize_state(
        {
            "segment": "Rational Health-Conscious",
            "certification": "organic",
            "_last_asked_field": "cocoa_percentage",
        }
    )
    updated = update_state_from_message("no", state)
    assert updated["certification"] == "organic"

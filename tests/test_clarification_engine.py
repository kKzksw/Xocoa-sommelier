from orchestration.clarification_engine import (
    check_clarification,
    detect_segment_from_clickbox,
    infer_segment_from_query,
    is_ambiguous_message,
    normalize_state,
    update_state_from_message,
)


def test_clickbox_segment_mapping():
    assert detect_segment_from_clickbox("A") == "Impulsive-Involved"
    assert detect_segment_from_clickbox("option b") == "Rational Health-Conscious"
    assert detect_segment_from_clickbox("C)") == "Uninvolved"


def test_missing_required_field_triggers_clarification():
    state = normalize_state({"segment": "Impulsive-Involved"})
    out = check_clarification("I want chocolate", state)
    assert out["needs_clarification"] is True
    assert any("flavor direction" in q.lower() for q in out["followup_questions"])


def test_required_collected_stops_clarification():
    state = normalize_state({"segment": "Uninvolved"})
    state = update_state_from_message("Under $15 please", state)
    out = check_clarification("Under $15 please", state)
    assert state["budget"]
    assert out["needs_clarification"] is False
    assert out["followup_questions"] == []


def test_max_three_questions_rule():
    state = normalize_state({"segment": "Rational Health-Conscious", "context": "gift"})
    out = check_clarification("help", state)
    assert out["needs_clarification"] is True
    assert len(out["followup_questions"]) <= 3


def test_gift_context_is_parsed():
    state = normalize_state({"segment": "Uninvolved"})
    updated = update_state_from_message("This is a birthday gift under $20", state)
    assert updated["context"] == "gift"
    assert updated["budget"]


def test_infer_segment_from_specific_query():
    assert infer_segment_from_query("I want organic fair trade chocolate") == "Rational Health-Conscious"
    assert infer_segment_from_query("Need something under $15 from familiar brands") == "Uninvolved"
    assert infer_segment_from_query("Show me fruity dark chocolate around 70%") == "Impulsive-Involved"


def test_ambiguity_detection():
    assert is_ambiguous_message("chocolate") is True
    assert is_ambiguous_message("i want good chocolate") is True
    assert is_ambiguous_message("i want dark chocolate") is False
    assert is_ambiguous_message("dark chocolate 70% under $10") is False


def test_numbered_uninvolved_reply_updates_required_fields():
    state = normalize_state({"segment": "Uninvolved"})
    updated = update_state_from_message("1. more expensive 2. open 3. for gift", state)
    assert updated["budget"] == "premium"
    assert updated["brand_preference"] == "open"
    assert updated["context"] == "gift"

    out = check_clarification("1. more expensive 2. open 3. for gift", updated)
    assert out["needs_clarification"] is False

from orchestration.agentic_runtime import (
    AGENT_ACTION_FINALIZE,
    AGENT_ACTION_RETRIEVE,
    AGENT_ACTION_VERIFY,
    VALID_AGENT_ACTIONS,
    is_question_action,
    normalize_agent_decision,
    read_agent_trace,
    run_post_retrieval_verification,
    run_pre_retrieval_agent_turn,
    run_retry_agent_turn,
)


class DummyRecommender:
    def __init__(self, count):
        self.count = int(count)

    def estimate_candidate_count(self, _query, hard_filters=None):
        return self.count


def test_normalize_agent_decision_invalid_action_falls_back_to_retrieve():
    out = normalize_agent_decision(
        {
            "action": "UNKNOWN",
            "question": "x",
            "answer_options": ["a"],
            "updated_state": {"segment": "Impulsive-Involved"},
        },
        fallback_state={},
    )
    assert out["action"] == AGENT_ACTION_RETRIEVE


def test_normalize_agent_decision_ask_without_question_falls_back_to_retrieve():
    out = normalize_agent_decision(
        {
            "action": "ASK",
            "question": "",
            "answer_options": ["A", "B"],
            "updated_state": {},
        },
        fallback_state={},
    )
    assert out["action"] == AGENT_ACTION_RETRIEVE
    assert is_question_action(out["action"]) is False


def test_run_pre_retrieval_agent_turn_returns_strict_schema():
    out = run_pre_retrieval_agent_turn(
        user_message="I want dark chocolate",
        state={},
        recommender=DummyRecommender(count=500),
        total_catalog_count=2000,
    )

    assert set(out.keys()) == {
        "decision",
        "conversation_state",
        "candidate_count",
        "probe_query",
        "filter_bundle",
    }
    assert out["candidate_count"] == 500
    assert out["conversation_state"]["chocolate_type"] == "dark"
    assert out["decision"]["action"] in VALID_AGENT_ACTIONS
    trace = read_agent_trace(out["conversation_state"])
    assert trace
    assert trace[-1]["stage"] == "pre_retrieval"


def test_run_retry_agent_turn_returns_normalized_action_payload():
    out = run_retry_agent_turn(
        user_message="recommend",
        state={"segment": "Impulsive-Involved", "chocolate_type": "dark", "_clarification_turns": "1"},
        candidate_count=200,
        total_catalog_count=2000,
    )
    assert set(out.keys()) == {
        "action",
        "question",
        "answer_options",
        "filters",
        "updated_state",
        "fallback_mode",
    }
    assert out["action"] in VALID_AGENT_ACTIONS
    trace = read_agent_trace(out["updated_state"])
    assert trace
    assert trace[-1]["stage"] == "retry"


def test_post_retrieval_verification_low_similarity_routes_to_verify():
    out = run_post_retrieval_verification(
        user_message="dark chocolate",
        state={
            "segment": "Impulsive-Involved",
            "chocolate_type": "dark",
            "_clarification_turns": "1",
        },
        retrieval_result={
            "max_similarity": 0.2,
            "similarity_variance": 0.01,
            "candidates": list(range(1, 200)),
            "semantic_scores": [{"id": 1, "score": 0.2}],
            "explanation_layer": {"matched_preferences": ["chocolate_type"]},
        },
        products=[
            {"id": 1, "name": "A", "brand": "B", "maker_country": "France", "origin_country": "Peru", "cocoa_percentage": "75"}
        ],
        total_catalog_count=2000,
    )
    assert out["action"] == AGENT_ACTION_VERIFY
    assert out["question"]
    assert out["reason"] == "low_similarity"
    assert out["evidence"]
    trace = read_agent_trace(out["updated_state"])
    assert trace
    assert trace[-1]["stage"] == "post_retrieval_verify"
    assert trace[-1]["action"] == AGENT_ACTION_VERIFY


def test_post_retrieval_verification_good_quality_finalizes():
    out = run_post_retrieval_verification(
        user_message="dark fruity chocolate",
        state={
            "segment": "Impulsive-Involved",
            "chocolate_type": "dark",
            "flavor_direction": "fruity",
            "_clarification_turns": "1",
        },
        retrieval_result={
            "max_similarity": 0.92,
            "similarity_variance": 0.02,
            "candidates": [1, 2, 3],
            "semantic_scores": [{"id": 1, "score": 0.92}, {"id": 2, "score": 0.88}],
            "explanation_layer": {"matched_preferences": ["chocolate_type", "flavor_direction"]},
        },
        products=[
            {"id": 1, "name": "A", "brand": "B", "maker_country": "France", "origin_country": "Peru", "cocoa_percentage": "75"},
            {"id": 2, "name": "C", "brand": "D", "maker_country": "Belgium", "origin_country": "Ghana", "cocoa_percentage": "70"},
        ],
        total_catalog_count=2000,
    )
    assert out["action"] == AGENT_ACTION_FINALIZE
    assert out["reason"] == "verified"
    assert len(out["evidence"]) == 2
    trace = read_agent_trace(out["updated_state"])
    assert trace
    assert trace[-1]["stage"] == "post_retrieval_verify"
    assert trace[-1]["action"] == AGENT_ACTION_FINALIZE

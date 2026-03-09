import os
import re

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


class _DummyChannelA:
    def __init__(self, ids):
        self._ids = list(ids)

    def run(self, _query):
        return list(self._ids)


class RichDummyRecommender:
    def __init__(self, count):
        self.count = int(count)
        self.product_by_id = {
            1: {
                "id": 1,
                "name": "Berry Noir",
                "brand": "Maison A",
                "maker_country": "France",
                "origin_country": "Peru",
                "cocoa_percentage": "72",
                "price_retail": "12",
                "flavor_notes_primary": "berry",
                "flavor_notes_secondary": "fig",
            },
            2: {
                "id": 2,
                "name": "Caramel Velvet",
                "brand": "Maison B",
                "maker_country": "Belgium",
                "origin_country": "Ghana",
                "cocoa_percentage": "68",
                "price_retail": "15",
                "flavor_notes_primary": "caramel",
                "flavor_notes_secondary": "hazelnut",
            },
            3: {
                "id": 3,
                "name": "Spice Peak",
                "brand": "Maison C",
                "maker_country": "Switzerland",
                "origin_country": "Ecuador",
                "cocoa_percentage": "85",
                "price_retail": "18",
                "flavor_notes_primary": "pepper",
                "flavor_notes_secondary": "smoke",
            },
        }
        # Add more catalog rows so conversation-depth logic can be exercised.
        for pid in range(4, 34):
            flavor = "berry" if pid % 3 == 0 else "caramel" if pid % 3 == 1 else "pepper"
            secondary = "fig" if pid % 3 == 0 else "hazelnut" if pid % 3 == 1 else "smoke"
            self.product_by_id[pid] = {
                "id": pid,
                "name": f"Sample Bar {pid}",
                "brand": f"Maison {chr(65 + (pid % 5))}",
                "maker_country": "France" if pid % 2 == 0 else "Belgium",
                "origin_country": "Peru" if pid % 2 == 0 else "Ghana",
                "cocoa_percentage": str(60 + (pid % 30)),
                "price_retail": str(8 + (pid % 12)),
                "flavor_notes_primary": flavor,
                "flavor_notes_secondary": secondary,
            }
        self.channel_a = _DummyChannelA(self.product_by_id.keys())

    def estimate_candidate_count(self, _query, hard_filters=None):
        return self.count

    def _apply_dynamic_hard_filters(self, candidate_ids, hard_filters):
        return list(candidate_ids), {}, {}

    def recommend(self, query, top_k=3, segment=None, state=None, hard_filters=None):
        ranked = list(self.product_by_id.keys())[: max(1, int(top_k))]
        scores = [{"id": pid, "score": 0.95 - (idx * 0.02)} for idx, pid in enumerate(ranked)]
        return {
            "ranked": ranked,
            "semantic_scores": scores,
            "max_similarity": 0.95,
            "similarity_variance": 0.02,
        }


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
        "display_candidate_count",
        "probe_query",
        "filter_bundle",
    }
    assert out["candidate_count"] == 500
    assert out["conversation_state"]["chocolate_type"] == "dark"
    assert out["decision"]["action"] in VALID_AGENT_ACTIONS
    trace = read_agent_trace(out["conversation_state"])
    assert trace
    assert trace[-1]["stage"] == "pre_retrieval"


def test_display_candidate_count_uses_soft_constraints_for_conversation():
    out = run_pre_retrieval_agent_turn(
        user_message="fruity",
        state={
            "segment": "Impulsive-Involved",
            "chocolate_type": "dark",
        },
        recommender=RichDummyRecommender(count=500),
        total_catalog_count=2000,
    )
    assert out["candidate_count"] == 500
    assert 0 < out["display_candidate_count"] < out["candidate_count"]
    question = out["decision"]["question"]
    m = re.search(r"currently have (\d+)", question.lower())
    assert m is not None
    assert int(m.group(1)) == out["display_candidate_count"]


def test_run_pre_retrieval_preserves_clickbox_segment_prompt():
    os.environ["SEGMENT_MODE"] = "clickbox"
    try:
        out = run_pre_retrieval_agent_turn(
            user_message="hello",
            state={},
            recommender=DummyRecommender(count=500),
            total_catalog_count=2000,
        )
        decision = out["decision"]
        assert decision["action"] == "ASK"
        assert "When choosing chocolate" in decision["question"]
        assert decision["answer_options"] == ["A", "B", "C"]
    finally:
        os.environ.pop("SEGMENT_MODE", None)


def test_run_pre_retrieval_small_pool_adds_preliminary_matches():
    out = run_pre_retrieval_agent_turn(
        user_message="recommend",
        state={
            "segment": "Impulsive-Involved",
            "chocolate_type": "dark",
            "_clarification_turns": "1",
        },
        recommender=RichDummyRecommender(count=25),
        total_catalog_count=2000,
    )
    decision = out["decision"]
    assert decision["action"] == "ASK"
    assert decision.get("preliminary_products")
    assert len(decision["preliminary_products"]) >= 2
    assert "strong matches" in decision["question"].lower()
    assert decision["answer_options"]


def test_runtime_does_not_force_low_impact_context_question_when_scope_is_broad():
    out = run_pre_retrieval_agent_turn(
        user_message="continue",
        state={
            "segment": "Impulsive-Involved",
            "chocolate_type": "dark",
            "flavor_direction": "fruity",
            "intensity": "intense",
            "_clarification_turns": "2",
            "_asked_fields": "flavor_direction,intensity",
            "_last_asked_field": "context",
        },
        recommender=RichDummyRecommender(count=700),
        total_catalog_count=2000,
    )
    decision = out["decision"]
    assert decision["action"] == "ASK"
    assert decision.get("selected_attribute") != "context"


def test_runtime_extends_conversation_when_pool_is_not_tiny():
    out = run_pre_retrieval_agent_turn(
        user_message="continue",
        state={
            "segment": "Impulsive-Involved",
            "chocolate_type": "dark",
            "_clarification_turns": "1",
            "_asked_fields": "chocolate_type",
            "_last_asked_field": "chocolate_type",
        },
        recommender=RichDummyRecommender(count=700),
        total_catalog_count=2000,
    )
    decision = out["decision"]
    assert decision["action"] == "ASK"
    assert out["display_candidate_count"] > 12


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

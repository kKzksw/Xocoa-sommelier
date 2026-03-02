from backend.main import (
    _extract_product_ids,
    _filter_unseen_products,
    _is_more_recommendations_request,
    _read_shown_product_ids,
    _write_shown_product_ids,
)


def test_detect_more_recommendations_request():
    assert _is_more_recommendations_request("another recommendation?") is True
    assert _is_more_recommendations_request("show me more options") is True
    assert _is_more_recommendations_request("recommend dark chocolate") is False


def test_filter_unseen_products_respects_seen_ids_and_limit():
    products = [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}]
    unseen = _filter_unseen_products(products, seen_ids=[1, 3], limit=2)
    assert [p["id"] for p in unseen] == [2, 4]


def test_shown_ids_roundtrip_is_deduped_and_sorted():
    state = {"_shown_product_ids": ""}
    updated = _write_shown_product_ids(state, [5, 3, 5, 1])
    assert updated["_shown_product_ids"] == "1,3,5"
    assert _read_shown_product_ids(updated) == [1, 3, 5]


def test_extract_product_ids_ignores_invalid_ids():
    ids = _extract_product_ids([{"id": "9"}, {"id": None}, {"id": "x"}, {"id": 2}])
    assert ids == [9, 2]

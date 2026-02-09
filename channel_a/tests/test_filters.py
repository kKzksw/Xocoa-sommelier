import json

from channel_a.index import ChannelAIndex
from channel_a.filter import filter_ids
from channel_a.query.parse import parse_query_to_filters


def test_query_parsing_and_filtering():
    with open("data/chocolates.json") as f:
        data = json.load(f)

    index = ChannelAIndex(data)

    query = "vegan dark chocolate under 10"
    filters = parse_query_to_filters(query)

    results = filter_ids(index, filters)

    assert isinstance(results, list)

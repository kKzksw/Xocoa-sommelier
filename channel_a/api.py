from channel_a.query.parse import parse_query_to_filters
from channel_a.filter import filter_ids
from channel_a.index import ChannelAIndex


class ChannelAService:
    def __init__(self, chocolates_data):
        self.index = ChannelAIndex(chocolates_data)

    def run(self, query: str) -> list[int]:
        filters = parse_query_to_filters(query)
        return filter_ids(self.index, filters)

from __future__ import annotations

import heapq


def merge_sorted_iterators(iterators):
    heap = []
    sources = [iter(source) for source in iterators]
    for index, iterator in enumerate(sources):
        try:
            value = next(iterator)
        except StopIteration:
            continue
        heapq.heappush(heap, (value, index))
    while heap:
        value, index = heapq.heappop(heap)
        yield value
        try:
            heapq.heappush(heap, (next(sources[index]), index))
        except StopIteration:
            pass

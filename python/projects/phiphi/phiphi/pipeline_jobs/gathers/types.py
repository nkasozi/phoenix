"""Gather pipelines types."""

import dataclasses


@dataclasses.dataclass
class ScrapeResponse:
    """Response from a scrape in a gather."""

    total_items: int
    total_batches: int
    total_cost: float
    is_cost_estimated: bool = False


@dataclasses.dataclass
class ScrapeCost:
    """Cost of scrape in a gather."""

    cost: float
    is_cost_estimated: bool = False

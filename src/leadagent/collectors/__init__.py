from .base import Collector, CollectorBlocked
from .facebook import FacebookCollector
from .linkedin import LinkedInCollector


def get_collectors(fixtures: str | None = None) -> dict[str, Collector]:
    """Fixture-backed collectors if `fixtures` is a directory, otherwise real Playwright ones."""
    return {"linkedin": LinkedInCollector(fixtures), "facebook": FacebookCollector(fixtures)}


__all__ = ["Collector", "CollectorBlocked", "LinkedInCollector", "FacebookCollector", "get_collectors"]

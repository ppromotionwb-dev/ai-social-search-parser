from .base import Collector
from .facebook import FacebookCollector
from .linkedin import LinkedInCollector


def get_collectors(fixtures: str | None = None) -> dict[str, Collector]:
    return {"linkedin": LinkedInCollector(fixtures), "facebook": FacebookCollector(fixtures)}


__all__ = ["Collector", "LinkedInCollector", "FacebookCollector", "get_collectors"]

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import timedelta
from pathlib import Path

from ..models import Post, utcnow
from ..queries import SavedQuery


class CollectorBlocked(RuntimeError):
    """The network asked for a login / checkpoint / CAPTCHA. We stop and tell the human; we never try to get past it."""


class Collector(ABC):
    """Fetches posts for a saved query from one network."""

    network: str

    @abstractmethod
    def collect(self, query: SavedQuery) -> list[Post]: ...

    def close(self) -> None:
        """Release resources (browser). Called once at the end of a run."""


def load_fixture_posts(path: Path, network: str, query: SavedQuery) -> list[Post]:
    """Load fictional posts from a JSON fixture. `days_ago` is resolved relative to now."""
    items = json.loads(path.read_text(encoding="utf-8"))
    now = utcnow()
    return [Post(
        network=network,
        url=i["url"],
        author=i.get("author", ""),
        author_headline=i.get("author_headline", ""),
        text=i["text"],
        posted_at=now - timedelta(days=i["days_ago"]) if "days_ago" in i else None,
        query=query.query,
        found_at=now,
    ) for i in items]

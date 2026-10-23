from __future__ import annotations

from pathlib import Path

from ..models import Post
from ..queries import SavedQuery
from .base import Collector, load_fixture_posts


class FacebookCollector(Collector):
    network = "facebook"

    def __init__(self, fixtures: str | Path | None = None):
        self.fixtures = Path(fixtures) if fixtures else None

    def collect(self, query: SavedQuery) -> list[Post]:
        if self.fixtures is None:
            raise NotImplementedError(
                "Real Facebook collection is not implemented yet. It will drive Playwright in the user's own "
                "logged-in session (see docs/collectors.md). Use --fixtures to run on sample data.")
        return load_fixture_posts(self.fixtures / "facebook.json", self.network, query)

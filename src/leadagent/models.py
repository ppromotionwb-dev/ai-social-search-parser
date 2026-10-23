from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

NETWORKS = ("linkedin", "facebook")
STATUSES = ("new", "contacted", "skip")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Post:
    network: str
    url: str
    author: str
    author_headline: str
    text: str
    posted_at: datetime | None
    query: str
    found_at: datetime = field(default_factory=utcnow)


@dataclass
class Verdict:
    is_lead: bool
    score: int
    reason: str
    language: str

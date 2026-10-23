from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .models import NETWORKS


@dataclass
class SavedQuery:
    network: str
    query: str
    max_age_days: int = 14
    language: str = "en"


@dataclass
class PrefilterConfig:
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)


def load_queries(path: str | Path) -> tuple[list[SavedQuery], PrefilterConfig]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    queries = []
    for i, item in enumerate(data.get("queries") or []):
        network = item.get("network")
        if network not in NETWORKS:
            raise ValueError(f"queries[{i}]: network must be one of {NETWORKS}, got {network!r}")
        if not item.get("query"):
            raise ValueError(f"queries[{i}]: 'query' is required")
        queries.append(SavedQuery(
            network=network,
            query=str(item["query"]),
            max_age_days=int(item.get("max_age_days", 14)),
            language=str(item.get("language", "en")),
        ))
    pf = data.get("prefilter") or {}
    return queries, PrefilterConfig(include=list(pf.get("include") or []), exclude=list(pf.get("exclude") or []))

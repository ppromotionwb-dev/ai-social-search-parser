from __future__ import annotations

from dataclasses import dataclass, field

from .collectors import Collector
from .judge import Judge
from .models import Verdict
from .prefilter import prefilter
from .queries import PrefilterConfig, SavedQuery
from .storage import Storage


@dataclass
class RunStats:
    collected: int = 0
    duplicates: int = 0
    prefiltered: int = 0
    judged: int = 0
    leads: int = 0
    errors: list[str] = field(default_factory=list)


def run_pipeline(queries: list[SavedQuery], cfg: PrefilterConfig, collectors: dict[str, Collector],
                 storage: Storage, judge: Judge) -> RunStats:
    stats = RunStats()
    for q in queries:
        try:
            posts = collectors[q.network].collect(q)
        except NotImplementedError:
            raise
        except Exception as e:  # one failing search must not kill the whole run
            stats.errors.append(f"{q.network} '{q.query}': {e}")
            continue
        stats.collected += len(posts)
        fresh = []
        for p in posts:
            if storage.has(p.url) or any(p.url == f.url for f in fresh):
                stats.duplicates += 1
            else:
                fresh.append(p)
        passed, rejected = prefilter(fresh, q, cfg)
        for p, reason in rejected:  # remember rejects so they are not re-processed next run
            storage.add_post(p, Verdict(False, 0, f"prefilter: {reason}", "und"))
        stats.prefiltered += len(rejected)
        if not passed:
            continue
        for p, v in zip(passed, judge.judge(passed)):
            storage.add_post(p, v)
            stats.judged += 1
            stats.leads += v.is_lead
    return stats

from pathlib import Path

from leadagent.collectors import Collector, CollectorBlocked
from leadagent.judge import Judge
from leadagent.pipeline import run_pipeline
from leadagent.queries import PrefilterConfig, SavedQuery
from leadagent.storage import Storage


class Blocking(Collector):
    network = "linkedin"
    calls = 0
    closed = False

    def collect(self, query):
        self.calls += 1
        raise CollectorBlocked("login wall")

    def close(self):
        self.closed = True


def test_blocked_network_stops_and_closes():
    c = Blocking()
    qs = [SavedQuery("linkedin", "a"), SavedQuery("linkedin", "b")]
    stats = run_pipeline(qs, PrefilterConfig(), {"linkedin": c}, Storage(), Judge(api_key=""))
    assert c.calls == 1 and c.closed and "login wall" in stats.errors[0]

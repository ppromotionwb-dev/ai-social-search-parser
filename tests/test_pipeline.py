from pathlib import Path

from leadagent.cli import main
from leadagent.collectors import get_collectors
from leadagent.judge import Judge
from leadagent.pipeline import run_pipeline
from leadagent.queries import load_queries
from leadagent.storage import Storage

ROOT = Path(__file__).parent.parent
FIX = str(ROOT / "tests" / "fixtures")


def test_pipeline_on_fixtures_is_idempotent():
    queries, cfg = load_queries(ROOT / "queries.yaml")
    s = Storage()
    first = run_pipeline(queries, cfg, get_collectors(FIX), s, Judge(api_key=""))
    assert first.leads >= 3 and first.prefiltered >= 3
    n = s.count()
    second = run_pipeline(queries, cfg, get_collectors(FIX), s, Judge(api_key=""))
    assert s.count() == n and second.judged == 0


def test_cli_run_creates_outputs(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    rc = main(["--db", str(tmp_path / "t.db"), "run", "--queries", str(ROOT / "queries.yaml"),
               "--fixtures", FIX, "--out-dir", str(tmp_path)])
    assert rc == 0
    assert "linkedin.com" in (tmp_path / "leads.csv").read_text()
    assert "<html" in (tmp_path / "dashboard.html").read_text()

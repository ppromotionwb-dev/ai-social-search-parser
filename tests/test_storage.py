from datetime import datetime, timezone

import pytest

from leadagent.models import Post, Verdict
from leadagent.storage import Storage, normalize_url


def make(url="https://x.com/p/1"):
    return Post("linkedin", url, "A", "H", "text", datetime.now(timezone.utc), "q")


def test_dedupe_by_url():
    s = Storage()
    assert s.add_post(make()) is True
    assert s.add_post(make()) is False
    assert s.count() == 1


def test_dedupe_normalizes_url():
    s = Storage()
    s.add_post(make("https://X.com/p/1/?utm_source=share#frag"))
    assert s.has("https://x.com/p/1")
    assert s.add_post(make("https://x.com/p/1/")) is False


def test_normalize_url():
    assert normalize_url(" https://A.com/b/?x=1 ") == "https://a.com/b"


def test_status_and_leads():
    s = Storage()
    s.add_post(make("https://x.com/a"), Verdict(True, 80, "r", "en"))
    s.add_post(make("https://x.com/b"), Verdict(False, 0, "r", "en"))
    assert [r["url"] for r in s.leads()] == ["https://x.com/a"]
    assert s.leads()[0]["status"] == "new"
    assert s.set_status("https://x.com/a", "contacted")
    assert s.leads(status="new") == []
    with pytest.raises(ValueError):
        s.set_status("https://x.com/a", "bogus")

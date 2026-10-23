from datetime import datetime, timedelta, timezone

from leadagent.models import Post
from leadagent.prefilter import check_post, detect_language, prefilter
from leadagent.queries import PrefilterConfig, SavedQuery

Q = SavedQuery("linkedin", "q", max_age_days=7, language="en")
CFG = PrefilterConfig(include=["amazon"], exclude=["hiring"])


def post(text, days=1):
    return Post("linkedin", "https://x.com/" + text[:5], "A", "", text,
                datetime.now(timezone.utc) - timedelta(days=days), "q")


def test_passes():
    assert check_post(post("Looking for an Amazon agency"), Q, CFG) is None


def test_age():
    assert "older" in check_post(post("Looking for an Amazon agency", days=10), Q, CFG)


def test_include_exclude():
    assert check_post(post("Need a plumber"), Q, CFG) == "no include keyword"
    assert "exclude" in check_post(post("Amazon agency is hiring"), Q, CFG)


def test_language():
    assert detect_language("Ищу агентство по Amazon") == "ru"
    assert detect_language("Looking for help") == "en"
    assert "language" in check_post(post("Ищу агентство по ведению Amazon"), Q, CFG)


def test_split():
    ok, bad = prefilter([post("Amazon help wanted"), post("nothing here")], Q, CFG)
    assert len(ok) == 1 and len(bad) == 1

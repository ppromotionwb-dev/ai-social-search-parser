import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from leadagent.collectors import FacebookCollector, LinkedInCollector
from leadagent.collectors.browser import looks_blocked, parse_relative_time
from leadagent.queries import SavedQuery

HTML = Path(__file__).parent / "fixtures" / "html"
NOW = datetime(2026, 1, 10, tzinfo=timezone.utc)
Q = SavedQuery("linkedin", "looking for amazon agency", max_age_days=7)


@pytest.mark.parametrize("text,delta", [
    ("2d •", timedelta(days=2)), ("3 hrs ago", timedelta(hours=3)), ("5m", timedelta(minutes=5)),
    ("1w", timedelta(weeks=1)), ("2mo", timedelta(days=60)), ("Yesterday", timedelta(days=1)),
    ("Just now", timedelta(0)), ("45 mins", timedelta(minutes=45)),
])
def test_parse_relative_time(text, delta):
    assert parse_relative_time(text, NOW) == NOW - delta


def test_parse_relative_time_unknown():
    assert parse_relative_time("Sponsored", NOW) is None and parse_relative_time("", NOW) is None


def test_looks_blocked():
    assert looks_blocked("https://www.linkedin.com/authwall?trk=x")
    assert looks_blocked("https://www.facebook.com/checkpoint/123")
    assert not looks_blocked("https://www.linkedin.com/search/results/content/?keywords=a")


def test_search_urls():
    assert "datePosted=%22past-week%22" in LinkedInCollector().search_url(Q)
    assert "keywords=looking%20for%20amazon%20agency" in LinkedInCollector().search_url(Q)
    assert FacebookCollector().search_url(Q).endswith("q=looking%20for%20amazon%20agency")


def test_to_posts_normalizes_and_skips_empty():
    raw = [{"url": "https://x/1", "text": " a \n b ", "author": " A ", "time_text": "1d"},
           {"url": "https://x/1", "text": "dup"}, {"url": "", "text": "no url"}, {"url": "https://x/2", "text": ""}]
    posts = LinkedInCollector().to_posts(raw, Q, NOW)
    assert len(posts) == 1 and posts[0].text == "a b" and posts[0].posted_at == NOW - timedelta(days=1)


def _page_or_skip():
    pw_mod = pytest.importorskip("playwright.sync_api")
    pw = pw_mod.sync_playwright().start()
    try:
        kw = {"executable_path": os.environ["LEADAGENT_CHROMIUM_PATH"]} if os.environ.get("LEADAGENT_CHROMIUM_PATH") else {}
        browser = pw.chromium.launch(args=["--no-sandbox"], **kw)
    except Exception:
        pw.stop()
        pytest.skip("Chromium not available")
    return pw, browser


@pytest.mark.parametrize("cls,file,expected", [
    (LinkedInCollector, "linkedin_search.html", 2),
    (FacebookCollector, "facebook_search.html", 2),
])
def test_extract_js_on_sample_markup(cls, file, expected):
    pw, browser = _page_or_skip()
    try:
        page = browser.new_page()
        page.set_content((HTML / file).read_text())
        c = cls()
        posts = c.to_posts(page.evaluate(c.extract_js), Q, NOW)
    finally:
        browser.close(); pw.stop()
    assert len(posts) == expected
    if cls is LinkedInCollector:
        assert posts[0].url == "https://www.linkedin.com/feed/update/urn:li:activity:7001/"
        assert posts[0].author == "Jane Doe (fictional)" and posts[0].posted_at == NOW - timedelta(days=2)
        assert posts[1].text.startswith("Need an Amazon")
    else:
        assert posts[0].url == "https://www.facebook.com/groups/example-fba/posts/9001/"
        assert posts[0].text.startswith("Can anyone") and posts[0].author.startswith("Chris")
        assert "story_fbid=555" in posts[1].url and posts[1].posted_at == NOW - timedelta(days=1)

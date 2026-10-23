"""Shared Playwright plumbing for the real collectors.

The browser uses a persistent profile directory that the *user* logs into by hand (`leadagent browser <network>`).
This module never types credentials and never tries to get around login walls, checkpoints or CAPTCHAs:
when one shows up the collector raises CollectorBlocked and the run for that network stops.
"""
from __future__ import annotations

import os
import random
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

from ..models import Post, utcnow
from ..queries import SavedQuery
from .base import Collector, CollectorBlocked, load_fixture_posts

BLOCK_URL_MARKERS = ("/login", "/authwall", "/checkpoint", "/uas/", "captcha", "/challenge", "recover")

_REL = re.compile(r"(?<![\w])(\d+)\s*(seconds?|secs?|minutes?|mins?|hours?|hrs?|days?|weeks?|wks?|months?|mos?|years?|yrs?|s|m|h|d|w|y)\b",
                  re.I)
_DAYS = {"d": 1, "w": 7, "mo": 30, "y": 365}


def parse_relative_time(text: str, now: datetime | None = None) -> datetime | None:
    """'2d', '3 hrs ago', '1w •', 'Yesterday', 'Just now' -> datetime; None if unrecognised."""
    now = now or utcnow()
    low = (text or "").lower()
    if "just now" in low:
        return now
    if "yesterday" in low:
        return now - timedelta(days=1)
    m = _REL.search(low)
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2)
    if unit.startswith("mo"):
        return now - timedelta(days=30 * n)
    if unit.startswith("min") or unit == "m":
        return now - timedelta(minutes=n)
    if unit.startswith("s"):
        return now - timedelta(seconds=n)
    if unit.startswith("h"):
        return now - timedelta(hours=n)
    return now - timedelta(days=_DAYS[unit[0]] * n)


def looks_blocked(url: str) -> bool:
    low = url.lower()
    return any(m in low for m in BLOCK_URL_MARKERS)


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default


def pause(lo: float, hi: float) -> None:
    time.sleep(random.uniform(lo, hi) * _env_float("LEADAGENT_DELAY_SCALE", 1.0))


def profile_dir() -> Path:
    return Path(os.environ.get("LEADAGENT_BROWSER_PROFILE", "data/browser-profile"))


def launch_context(headless: bool):
    """Return (playwright, context) using the persistent user profile."""
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    kwargs = {}
    if os.environ.get("LEADAGENT_CHROMIUM_PATH"):
        kwargs["executable_path"] = os.environ["LEADAGENT_CHROMIUM_PATH"]
    ctx = pw.chromium.launch_persistent_context(str(profile_dir()), headless=headless, **kwargs)
    return pw, ctx


class BrowserCollector(Collector):
    """Opens a search page in the user's logged-in profile, scrolls a little, extracts posts with in-page JS."""

    extract_js: str
    login_url: str

    def __init__(self, fixtures: str | Path | None = None, max_scrolls: int | None = None,
                 headless: bool | None = None):
        self.fixtures = Path(fixtures) if fixtures else None
        self.max_scrolls = max_scrolls if max_scrolls is not None else int(_env_float("LEADAGENT_MAX_SCROLLS", 5))
        self.headless = headless if headless is not None else os.environ.get("LEADAGENT_HEADLESS") == "1"
        self._pw = self._ctx = None

    def search_url(self, query: SavedQuery) -> str:
        raise NotImplementedError

    def collect(self, query: SavedQuery) -> list[Post]:
        if self.fixtures is not None:
            return load_fixture_posts(self.fixtures / f"{self.network}.json", self.network, query)
        page = self._page()
        page.goto(self.search_url(query), wait_until="domcontentloaded")
        pause(2, 4)
        self._check_blocked(page)
        for _ in range(self.max_scrolls):
            page.mouse.wheel(0, 2500)
            pause(1.5, 3.5)
            self._check_blocked(page)
        pause(5, 12)  # spacing between searches
        return self.to_posts(page.evaluate(self.extract_js), query)

    def _check_blocked(self, page) -> None:
        if looks_blocked(page.url):
            raise CollectorBlocked(
                f"{self.network} wants a login or verification (at {page.url}). Run `leadagent browser {self.network}`, "
                "sign in / complete the check yourself in that window, then re-run.")

    def _page(self):
        if self._ctx is None:
            profile_dir().mkdir(parents=True, exist_ok=True)
            self._pw, self._ctx = launch_context(self.headless)
        return self._ctx.pages[0] if self._ctx.pages else self._ctx.new_page()

    def close(self) -> None:
        if self._ctx is not None:
            self._ctx.close()
            self._pw.stop()
            self._ctx = self._pw = None

    def to_posts(self, raw: list[dict], query: SavedQuery, now: datetime | None = None) -> list[Post]:
        now = now or utcnow()
        posts, seen = [], set()
        for r in raw:
            url, text = (r.get("url") or "").strip(), " ".join((r.get("text") or "").split())
            if not url or not text or url in seen:
                continue
            seen.add(url)
            posts.append(Post(
                network=self.network, url=url, author=(r.get("author") or "").strip(),
                author_headline=" ".join((r.get("headline") or "").split()), text=text,
                posted_at=parse_relative_time(r.get("time_text") or "", now), query=query.query, found_at=now))
        return posts


def open_for_manual_login(collector: BrowserCollector) -> None:
    """Open the persistent profile in a visible window so the HUMAN can sign in. Nothing is typed or clicked for them."""
    profile_dir().mkdir(parents=True, exist_ok=True)
    pw, ctx = launch_context(headless=False)
    try:
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(collector.login_url)
        input("Sign in in the browser window (including any verification), then press Enter here to save the session... ")
    finally:
        ctx.close()
        pw.stop()

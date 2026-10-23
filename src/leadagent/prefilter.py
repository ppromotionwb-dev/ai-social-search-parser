from __future__ import annotations

from datetime import datetime, timedelta

from .models import Post, utcnow
from .queries import PrefilterConfig, SavedQuery


def detect_language(text: str) -> str:
    """Cheap script-based guess: 'ru' for mostly Cyrillic, 'en' for mostly Latin, else 'other'.

    Only used to drop obviously wrong-language posts; the LLM judge reports the real language.
    """
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return "other"
    cyr = sum("Ѐ" <= c <= "ӿ" for c in letters) / len(letters)
    lat = sum(c.isascii() for c in letters) / len(letters)
    if cyr > 0.3:
        return "ru"
    return "en" if lat > 0.7 else "other"


def check_post(post: Post, query: SavedQuery, cfg: PrefilterConfig, now: datetime | None = None) -> str | None:
    """Return None if the post passes, otherwise a short rejection reason."""
    now = now or utcnow()
    low = post.text.lower()
    if post.posted_at is not None and now - post.posted_at > timedelta(days=query.max_age_days):
        return f"older than {query.max_age_days} days"
    if cfg.include and not any(k.lower() in low for k in cfg.include):
        return "no include keyword"
    for k in cfg.exclude:
        if k.lower() in low:
            return f"exclude keyword: {k}"
    lang = detect_language(post.text)
    if lang != query.language:
        return f"language {lang} != {query.language}"
    return None


def prefilter(posts: list[Post], query: SavedQuery, cfg: PrefilterConfig,
              now: datetime | None = None) -> tuple[list[Post], list[tuple[Post, str]]]:
    passed, rejected = [], []
    for p in posts:
        reason = check_post(p, query, cfg, now)
        (rejected.append((p, reason)) if reason else passed.append(p))
    return passed, rejected

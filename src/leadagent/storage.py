from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from .models import STATUSES, Post, Verdict

SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    url TEXT PRIMARY KEY,
    network TEXT NOT NULL,
    author TEXT, author_headline TEXT, text TEXT,
    posted_at TEXT, found_at TEXT NOT NULL, query TEXT,
    status TEXT NOT NULL DEFAULT 'new',
    is_lead INTEGER, score INTEGER, reason TEXT, language TEXT,
    notified INTEGER NOT NULL DEFAULT 0
);
"""


def normalize_url(url: str) -> str:
    """Drop query string, fragment and trailing slash so the same post dedupes."""
    p = urlsplit(url.strip())
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/"), "", ""))


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


class Storage:
    def __init__(self, path: str | Path = ":memory:"):
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def add_post(self, post: Post, verdict: Verdict | None = None) -> bool:
        """Insert a post; return False if its URL is already stored."""
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO posts (url, network, author, author_headline, text, posted_at, found_at, query,"
            " is_lead, score, reason, language) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (normalize_url(post.url), post.network, post.author, post.author_headline, post.text,
             _iso(post.posted_at), _iso(post.found_at), post.query,
             None if verdict is None else int(verdict.is_lead),
             None if verdict is None else verdict.score,
             None if verdict is None else verdict.reason,
             None if verdict is None else verdict.language),
        )
        self.conn.commit()
        return cur.rowcount == 1

    def has(self, url: str) -> bool:
        return self.conn.execute("SELECT 1 FROM posts WHERE url=?", (normalize_url(url),)).fetchone() is not None

    def set_verdict(self, url: str, v: Verdict) -> None:
        self.conn.execute("UPDATE posts SET is_lead=?, score=?, reason=?, language=? WHERE url=?",
                          (int(v.is_lead), v.score, v.reason, v.language, normalize_url(url)))
        self.conn.commit()

    def set_status(self, url: str, status: str) -> bool:
        if status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}")
        cur = self.conn.execute("UPDATE posts SET status=? WHERE url=?", (status, normalize_url(url)))
        self.conn.commit()
        return cur.rowcount == 1

    def leads(self, status: str | None = None, only_unnotified: bool = False) -> list[sqlite3.Row]:
        sql, args = "SELECT * FROM posts WHERE is_lead=1", []
        if status:
            sql += " AND status=?"; args.append(status)
        if only_unnotified:
            sql += " AND notified=0"
        return self.conn.execute(sql + " ORDER BY score DESC, found_at DESC", args).fetchall()

    def mark_notified(self, urls: list[str]) -> None:
        self.conn.executemany("UPDATE posts SET notified=1 WHERE url=?", [(u,) for u in urls])
        self.conn.commit()

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]

from __future__ import annotations

import csv
from pathlib import Path

COLUMNS = ["found_at", "network", "url", "author", "author_headline", "text", "score", "reason", "status"]


def export_csv(leads, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        for r in leads:
            w.writerow([(r[c] or "")[:300] if c == "text" else r[c] for c in COLUMNS])
    return path

from __future__ import annotations

from html import escape
from pathlib import Path

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Leads</title>
<style>
body{{font:15px/1.4 system-ui,sans-serif;margin:2rem auto;max-width:960px;padding:0 1rem;color:#222}}
.lead{{border:1px solid #ddd;border-radius:8px;padding:.8rem 1rem;margin:.8rem 0}}
.meta{{color:#666;font-size:13px}} .score{{font-weight:700}} .status{{text-transform:uppercase;font-size:12px}}
.excerpt{{margin:.5rem 0}}
</style></head><body>
<h1>Leads ({count})</h1>
{items}
</body></html>"""


def _safe_href(url: str) -> str:
    return escape(url, quote=True) if url.startswith(("https://", "http://")) else "#"


def export_html(leads, path: str | Path) -> Path:
    items = []
    for r in leads:
        excerpt = (r["text"] or "")[:300]
        items.append(
            f'<div class="lead"><div class="meta">{escape(r["found_at"][:10])} · {escape(r["network"])} · '
            f'<span class="status">{escape(r["status"])}</span> · score <span class="score">{r["score"]}</span></div>'
            f'<div><a href="{_safe_href(r["url"])}" rel="noopener noreferrer" target="_blank">{escape(r["url"])}</a></div>'
            f'<div>{escape(r["author"] or "")} <span class="meta">{escape(r["author_headline"] or "")}</span></div>'
            f'<div class="excerpt">{escape(excerpt)}</div>'
            f'<div class="meta">{escape(r["reason"] or "")}</div></div>')
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(PAGE.format(count=len(items), items="\n".join(items) or "<p>No leads yet.</p>"), encoding="utf-8")
    return path

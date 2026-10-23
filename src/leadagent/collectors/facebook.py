from __future__ import annotations

from urllib.parse import quote

from ..queries import SavedQuery
from .browser import BrowserCollector

# Runs inside the page. Facebook markup is obfuscated and changes often; keep all selectors here.
EXTRACT_JS = r"""
() => {
  const out = [], seen = new Set();
  const permalink = /\/(posts|permalink|videos)\/|story_fbid|\/groups\/[^/]+\/posts\//;
  document.querySelectorAll('[role="article"]').forEach(el => {
    if (el.parentElement && el.parentElement.closest('[role="article"]')) return;  // comments
    const link = Array.from(el.querySelectorAll('a[href]')).find(a => permalink.test(a.href));
    if (!link) return;
    const u = new URL(link.href);
    const keep = u.searchParams.get('story_fbid');
    const url = u.origin + u.pathname + (keep ? '?story_fbid=' + keep + '&id=' + (u.searchParams.get('id') || '') : '');
    if (seen.has(url)) return;
    seen.add(url);
    const msg = el.querySelector('[data-ad-preview="message"], [data-ad-comet-preview="message"]');
    const text = msg ? msg.innerText.trim()
      : Array.from(el.querySelectorAll('div[dir="auto"]')).map(d => d.innerText.trim()).filter(Boolean).join('\n');
    const who = el.querySelector('h2 a, h3 a, h2, h3, strong a, strong');
    out.push({
      url, text,
      author: who ? who.innerText.trim() : '',
      headline: '',
      time_text: link.getAttribute('aria-label') || link.innerText.trim(),
    });
  });
  return out;
}
"""


class FacebookCollector(BrowserCollector):
    network = "facebook"
    login_url = "https://www.facebook.com/login"
    extract_js = EXTRACT_JS

    def search_url(self, query: SavedQuery) -> str:
        return "https://www.facebook.com/search/posts?q=" + quote(query.query)

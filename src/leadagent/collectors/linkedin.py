from __future__ import annotations

from urllib.parse import quote

from ..queries import SavedQuery
from .browser import BrowserCollector

# Runs inside the page. Selectors are the single place to update when LinkedIn changes its markup.
EXTRACT_JS = r"""
() => {
  const out = [], seen = new Set();
  document.querySelectorAll('[data-urn^="urn:li:activity"], [data-chameleon-result-urn^="urn:li:activity"]').forEach(el => {
    const urn = el.getAttribute('data-urn') || el.getAttribute('data-chameleon-result-urn');
    if (!urn || seen.has(urn)) return;
    seen.add(urn);
    const q = s => { const n = el.querySelector(s); return n ? n.innerText.trim() : ''; };
    out.push({
      url: 'https://www.linkedin.com/feed/update/' + urn + '/',
      author: q('.update-components-actor__title span[aria-hidden="true"]') || q('.update-components-actor__title'),
      headline: q('.update-components-actor__description'),
      text: q('.update-components-text') || q('.feed-shared-update-v2__description'),
      time_text: q('.update-components-actor__sub-description'),
    });
  });
  return out;
}
"""


class LinkedInCollector(BrowserCollector):
    network = "linkedin"
    login_url = "https://www.linkedin.com/login"
    extract_js = EXTRACT_JS

    def search_url(self, query: SavedQuery) -> str:
        window = "past-24h" if query.max_age_days <= 1 else "past-week" if query.max_age_days <= 7 else "past-month"
        return ("https://www.linkedin.com/search/results/content/?keywords=" + quote(query.query)
                + f'&datePosted=%22{window}%22&sortBy=%22date_posted%22')

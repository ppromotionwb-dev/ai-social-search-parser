# Collectors

`LinkedInCollector` and `FacebookCollector` (`src/leadagent/collectors/`) implement the `Collector` interface:
`collect(query: SavedQuery) -> list[Post]`.

**Current state:** stubs. With `fixtures=<dir>` they return the fictional posts from `tests/fixtures/{linkedin,facebook}.json`;
without it they raise `NotImplementedError`.

**Planned implementation:** Playwright driving a browser session that the **user logs into themselves**
(a persistent browser profile stored locally, never committed). The collector opens the post-search page for the
query, scrolls a few screens, and extracts only public post data (url, author, headline, text, date).

Deliberately out of scope, and not to be added:
- code that performs logins or stores credentials;
- CAPTCHA / bot-protection bypass, proxy rotation, fingerprint spoofing;
- harvesting private or non-public data.

Keep frequency low (1-2 runs a day, random delays) and respect each platform's Terms of Service.
Cookies / sessions must stay out of git (`.gitignore` already covers `*.session`, `cookies*.json`).

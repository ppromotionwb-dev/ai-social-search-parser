# Collectors

`LinkedInCollector` and `FacebookCollector` (`src/leadagent/collectors/`) implement `Collector.collect(query) -> list[Post]`.
Both extend `BrowserCollector` (`browser.py`), which drives Playwright in a **persistent browser profile that you log into yourself**.

## Setup

```bash
pip install -e ".[browser]"
playwright install chromium            # or set LEADAGENT_CHROMIUM_PATH to an existing Chromium
leadagent browser linkedin             # opens a visible window; sign in (and pass any verification) yourself, press Enter
leadagent browser facebook
leadagent run                          # real collectors; add --fixtures to use sample data instead
```

The profile lives in `data/browser-profile` (`LEADAGENT_BROWSER_PROFILE`), is git-ignored, and holds your session cookies:
never commit or share it.

## How a search works
1. open the network's post-search URL for the saved query (LinkedIn also gets a date window from `max_age_days`);
2. scroll `LEADAGENT_MAX_SCROLLS` times (default 5) with random pauses;
3. run a small in-page JS extractor (selectors are the single constant `EXTRACT_JS` per network) returning url / author / headline / text / relative time;
4. `to_posts` normalizes text and turns "2d", "3 hrs", "Yesterday" into datetimes (unknown -> `None`, which the age filter lets through).

Knobs: `LEADAGENT_HEADLESS=1`, `LEADAGENT_MAX_SCROLLS`, `LEADAGENT_DELAY_SCALE` (multiplies all random pauses; `0` in tests).

## Limits and stop conditions
- If the page lands on a login wall, checkpoint or CAPTCHA, the collector raises `CollectorBlocked`; the run **stops that network** and prints
  what to do. There is no retry, workaround or automated sign-in, and none will be added.
- Keep it to 1-2 runs a day with your own account, public posts only. Respect each platform's Terms of Service.
- The selectors are best-effort: both sites change markup often and Facebook obfuscates it. They are covered by tests on
  **synthetic** HTML (`tests/fixtures/html/`) only, not verified against live pages. If a live run returns 0 posts, update `EXTRACT_JS`.

`--fixtures` makes the same classes return fictional posts from `tests/fixtures/{linkedin,facebook}.json`.

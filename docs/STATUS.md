# Status / handoff

**Done (PR #1, branch `claude/busy-ramanujan-e6xsyi`):** full pipeline (queries -> collectors -> dedupe -> prefilter -> LLM judge -> CSV/Telegram/HTML),
CLI (`run`, `export`, `list`, `status`, `browser`), Playwright collectors with manual login and stop on login wall/CAPTCHA. 31 tests pass.

**Not verified:** collectors on live LinkedIn/Facebook. Selectors (`EXTRACT_JS` in `collectors/linkedin.py`, `facebook.py`) are tested only on synthetic HTML.
The real LLM judge was never called (no API key in the cloud session).

**Next steps:**
1. Run locally per `docs/collectors.md` (`leadagent browser <network>`, then `leadagent run`) and check the post counts.
2. Optionally add `leadagent debug-dump` (save search-page HTML, user redacts it) to tune selectors.
3. Run with `ANTHROPIC_API_KEY` and review judge quality on real posts.
4. Then: Google Sheets exporter, scheduler.

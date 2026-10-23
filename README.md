# ai-social-search-parser

A lead-finding agent for **LinkedIn** and **Facebook** posts.

People publicly post things like *"looking for an Amazon agency"*, *"need someone to manage our Amazon store"*, *"recommend an Amazon PPC specialist"*. If you type that into LinkedIn or Facebook search (filter: Posts), you see them. This project automates that routine: once or twice a day it runs a set of saved searches, collects the new posts, lets an LLM decide which ones are real leads, and writes links to a journal / dashboard.

## Core principle: scripts do the work, AI only thinks

A human does this by hand in a few minutes a day. Everything mechanical is a plain script; the LLM is called only for the part that needs judgment.

| Step | Done by |
|---|---|
| Run saved search queries on each network | script |
| Scroll, open results, extract post text, author, date, link | script |
| Drop duplicates and already-seen posts (local DB) | script |
| Cheap keyword / language / age pre-filter | script |
| **Is this a real buyer of the service? How relevant, how urgent, why?** | **LLM** |
| Write result to the journal (Google Sheet / Telegram / web dashboard) | script |
| Schedule (1-2 runs a day, with random delays) | script |

The LLM gets only a short batch of already-cleaned posts, so a run costs very little.

## Flow

```
queries.yaml  (saved searches: "looking for amazon agency", "need Amazon PPC", ...)
      |
      v
runner  --> LinkedIn collector / Facebook collector   (your own logged-in browser session)
      |
      v
extract + normalize --> dedupe (SQLite) --> keyword/age pre-filter
      |
      v
LLM judge: lead / not lead, score, reason, language   (only step using AI)
      |
      v
journal: Google Sheets / Telegram / static dashboard  (link to post, author, why it matches)
```

## Output (one row per lead)

date found, network, post link, author + headline, post text excerpt, score, one-line reason from the LLM, status (new / contacted / skip) for manual follow-up.

## Responsible use

LinkedIn and Facebook restrict automated access in their Terms of Service. Keep it light: low frequency (1-2 runs a day), your own account and session, public posts only, no bypassing logins or CAPTCHAs, no mass harvesting of private data. You are responsible for compliance with the platforms' terms and applicable law.

## Roadmap

- [ ] `queries.yaml` format and runner
- [ ] LinkedIn post-search collector
- [ ] Facebook post-search collector
- [ ] SQLite dedupe + pre-filter
- [ ] LLM judge (prompt, JSON output, cheap model)
- [ ] Journal exporters: Google Sheets, Telegram, static dashboard
- [ ] Scheduler (daily / twice daily)

## License

MIT

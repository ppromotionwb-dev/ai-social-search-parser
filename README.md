# ai-social-search-parser

AI-powered search parser for **LinkedIn** and **Facebook**: describe in plain language who or what you are looking for, and the tool finds matching public profiles, groups and posts, then ranks them with an LLM.

> Status: early draft / project skeleton. Contributions welcome.

## Idea

1. You write a query in natural language, e.g. *"founders of Amazon FBA brands who recently posted that they are looking for a marketing agency"*.
2. An LLM turns it into concrete search queries for each network.
3. A collector fetches public results (profiles, posts, group threads).
4. The LLM scores each result against your intent and extracts structured fields (name, role, company, post text, link, why it matches).
5. Output: JSON / CSV, or a push to Telegram / webhook.

## Planned architecture

```
query (natural language)
   -> query planner (LLM)
   -> collectors: linkedin / facebook
   -> normalizer
   -> relevance scorer + extractor (LLM)
   -> exporters: json, csv, telegram, webhook
```

## Responsible use

LinkedIn and Facebook restrict automated access in their Terms of Service. This project is intended for:

- official APIs and data you are authorized to access;
- public data, collected at a low rate, with your own account/session and consent;
- no bypassing of logins, CAPTCHAs, or rate limits; no mass harvesting of private data.

You are responsible for complying with the platforms' terms and applicable law (including GDPR/CCPA) in your use.

## Roadmap

- [ ] Query planner (LLM -> per-network search queries)
- [ ] LinkedIn collector
- [ ] Facebook collector (public groups/pages)
- [ ] Relevance scoring and structured extraction
- [ ] Exporters (JSON, CSV, Telegram)
- [ ] Deduplication and run history
- [ ] Docs and examples

## License

MIT

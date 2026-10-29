# Agent handoff

Read README.md and CHANGELOG.md before changing code. Preserve existing behavior, user decisions, secrets and private customer data. Do not deploy, publish marketplace replies, alter production data or run installers as part of a source review.

Use the repository as the source of truth. Record local-only findings separately from live verification. API/provider compatibility identifiers in executable code are intentional; changing them requires an explicit migration and behavior checks. Never commit local .env/config credentials, databases, outboxes or browser profiles.

This branch preserves the new browser-skill implementation. The default main is only a repository scaffold. The older Python implementation remains available in the historical branch; an additional neutral legacy/python-parser alias will point to the same commit.

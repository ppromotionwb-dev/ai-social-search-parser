from __future__ import annotations

import json
import os
import urllib.request


def format_message(r) -> str:
    return (f"[{r['network']}] score {r['score']}\n{r['author'] or ''} — {r['author_headline'] or ''}\n"
            f"{r['reason'] or ''}\n{r['url']}")


def send_telegram(leads, token: str | None = None, chat_id: str | None = None) -> list[str]:
    """Send one message per lead; return URLs that were sent successfully."""
    token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to use the Telegram exporter.")
    sent = []
    for r in leads:
        body = json.dumps({"chat_id": chat_id, "text": format_message(r),
                           "disable_web_page_preview": True}).encode()
        req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=20):
            sent.append(r["url"])
    return sent

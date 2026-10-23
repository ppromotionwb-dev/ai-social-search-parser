"""LLM judge: the only step that uses AI. Takes cleaned posts, returns one Verdict per post."""
from __future__ import annotations

import json
import os
import re

from .models import Post, Verdict

DEFAULT_MODEL = "claude-haiku-5-5"
BATCH_SIZE = 10
MAX_TEXT_CHARS = 1500

SYSTEM_PROMPT = """You screen public social-media posts for a company that sells Amazon services \
(agency, PPC management, listing optimization, account management) to Western Amazon sellers.
A post is a LEAD only if the author is a potential BUYER: they are looking for, asking to recommend, \
or need to hire such a service for their own Amazon business. Not leads: people offering these services, \
job ads, general discussion, news, courses, complaints without a request for help.
You get a JSON list of posts, each with an integer "id". Reply with ONLY a JSON array, one object per post:
{"id": <int>, "is_lead": <bool>, "score": <0-100 relevance and urgency>, "reason": "<one short line>", \
"language": "<ISO 639-1 code of the post>"}"""


def _clean_verdict(item: dict) -> Verdict:
    try:
        score = int(round(float(item.get("score", 0))))
    except (TypeError, ValueError):
        score = 0
    reason = " ".join(str(item.get("reason", "")).split())[:300]
    return Verdict(
        is_lead=item.get("is_lead") is True or str(item.get("is_lead")).lower() == "true",
        score=max(0, min(100, score)),
        reason=reason,
        language=str(item.get("language", "") or "und").lower()[:8],
    )


def parse_judge_response(raw: str, n: int) -> list[Verdict]:
    """Parse the model reply into exactly `n` verdicts (index = post id). Never raises:
    garbage or missing entries become a non-lead verdict so one bad reply can't break a run."""
    missing = Verdict(False, 0, "no verdict returned by judge", "und")
    verdicts = [missing] * n
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\[.*\]", text, re.S)
        try:
            data = json.loads(m.group(0)) if m else None
        except json.JSONDecodeError:
            data = None
    if isinstance(data, dict):
        data = data.get("results") or data.get("verdicts") or [data]
    if not isinstance(data, list):
        return [Verdict(False, 0, "unparseable judge response", "und")] * n
    for pos, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        idx = item.get("id", pos)
        if isinstance(idx, int) and 0 <= idx < n:
            verdicts[idx] = _clean_verdict(item)
    return verdicts


_BUY_INTENT = re.compile(r"looking for|need (an?|help|someone)|recommend|can anyone|anyone know|searching for", re.I)


class Judge:
    def __init__(self, api_key: str | None = None, model: str | None = None, client=None):
        self.api_key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY")
        self.model = model or os.environ.get("LEADAGENT_MODEL") or DEFAULT_MODEL
        self._client = client

    @property
    def is_stub(self) -> bool:
        return not self.api_key and self._client is None

    def judge(self, posts: list[Post]) -> list[Verdict]:
        out: list[Verdict] = []
        for i in range(0, len(posts), BATCH_SIZE):
            out.extend(self._judge_batch(posts[i:i + BATCH_SIZE]))
        return out

    def _judge_batch(self, batch: list[Post]) -> list[Verdict]:
        if self.is_stub:
            return [self._stub(p) for p in batch]
        payload = json.dumps([
            {"id": i, "network": p.network, "author": p.author, "headline": p.author_headline,
             "text": p.text[:MAX_TEXT_CHARS]} for i, p in enumerate(batch)
        ], ensure_ascii=False)
        client = self._client
        if client is None:
            import anthropic
            client = self._client = anthropic.Anthropic(api_key=self.api_key)
        resp = client.messages.create(
            model=self.model, max_tokens=200 * len(batch) + 200, system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": payload}],
        )
        raw = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        return parse_judge_response(raw, len(batch))

    @staticmethod
    def _stub(post: Post) -> Verdict:
        hit = bool(_BUY_INTENT.search(post.text))
        return Verdict(hit, 50 if hit else 0, "stub judge (no ANTHROPIC_API_KEY): keyword guess", "en")

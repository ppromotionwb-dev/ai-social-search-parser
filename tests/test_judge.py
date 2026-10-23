from datetime import datetime, timezone
from types import SimpleNamespace

from leadagent.judge import Judge, parse_judge_response
from leadagent.models import Post


def test_parse_plain_json():
    raw = '[{"id":0,"is_lead":true,"score":85,"reason":"asks for agency","language":"en"},' \
          '{"id":1,"is_lead":false,"score":5,"reason":"job ad","language":"EN"}]'
    v = parse_judge_response(raw, 2)
    assert v[0].is_lead and v[0].score == 85 and v[1].language == "en" and not v[1].is_lead


def test_parse_fenced_and_clamped():
    raw = 'Here:\n```json\n[{"id":0,"is_lead":true,"score":250,"reason":"a\\nb","language":"en"}]\n```'
    v = parse_judge_response(raw, 1)[0]
    assert v.score == 100 and v.reason == "a b"


def test_parse_missing_and_garbage():
    v = parse_judge_response('[{"id":1,"is_lead":true,"score":70,"reason":"r","language":"en"}]', 2)
    assert not v[0].is_lead and v[1].is_lead
    g = parse_judge_response("sorry, I can't", 2)
    assert len(g) == 2 and not any(x.is_lead for x in g)


def _post(text):
    return Post("linkedin", "https://x.com/" + text[:4], "A", "", text, datetime.now(timezone.utc), "q")


def test_stub_mode_without_key():
    j = Judge(api_key="")
    assert j.is_stub
    v = j.judge([_post("Looking for an Amazon agency"), _post("Great weather")])
    assert v[0].is_lead and not v[1].is_lead


def test_llm_call_with_fake_client():
    reply = '[{"id":0,"is_lead":true,"score":90,"reason":"r","language":"en"}]'
    calls = []

    class Fake:
        class messages:
            @staticmethod
            def create(**kw):
                calls.append(kw)
                return SimpleNamespace(content=[SimpleNamespace(type="text", text=reply)])

    j = Judge(api_key="k", model="m", client=Fake)
    assert j.judge([_post("hello")])[0].score == 90
    assert calls[0]["model"] == "m"

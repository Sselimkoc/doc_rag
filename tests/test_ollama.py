import json

from app import ollama


def fake_post(monkeypatch, response):
    sent = []
    monkeypatch.setattr(ollama, "post", lambda path, body, timeout=300: sent.append((path, body)) or response)
    return sent


def test_chat_json_parses_reply_and_sends_fixed_options(monkeypatch):
    sent = fake_post(monkeypatch, {"done_reason": "stop", "message": {"content": json.dumps({"answerable": True})}})
    schema = {"type": "object"}
    assert ollama.chat_json("sys", "user", schema) == {"answerable": True}
    path, body = sent[0]
    assert path == "/api/chat" and body["format"] == schema and body["stream"] is False
    assert body["options"] == {"temperature": 0, "num_ctx": 8192, "num_predict": 512}
    assert [m["role"] for m in body["messages"]] == ["system", "user"]


def test_chat_json_treats_truncated_reply_as_empty(monkeypatch):
    # Döngüye girip sınıra çarpan cevap yarım JSON'dur (Vaka 44).
    fake_post(monkeypatch, {"done_reason": "length", "message": {"content": '{"answerable": true, "answer": "[240] [241'}})
    assert ollama.chat_json("sys", "user", {}) == {}

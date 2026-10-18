import json

from app import embedding, main, ollama


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
    assert body["keep_alive"] == "10m"


def test_chat_json_treats_truncated_reply_as_empty(monkeypatch):
    # Döngüye girip sınıra çarpan cevap yarım JSON'dur (Vaka 44).
    fake_post(monkeypatch, {"done_reason": "length", "message": {"content": '{"answerable": true, "answer": "[240] [241'}})
    assert ollama.chat_json("sys", "user", {}) == {}


def test_chat_json_treats_invalid_json_as_empty(monkeypatch, caplog):
    # acme-01: model cevabın içine "<source>1</source>" yazıp JSON'u kapatmadan bitirdi (Vaka 64).
    fake_post(monkeypatch, {"done_reason": "stop", "message": {"content": '{"answerable": true, "answer": "x <source>1</source>}'}})
    assert ollama.chat_json("sys", "user", {}) == {}
    assert "geçersiz JSON" in caplog.text


def test_warm_up_loads_llm_with_the_same_options_as_answers(monkeypatch):
    # num_ctx farklı olursa Ollama modeli ilk soruda yeniden yükler; ısınma boşa gider.
    sent = fake_post(monkeypatch, {"embeddings": [[1.0, 0.0]]})
    monkeypatch.setattr(embedding, "post", ollama.post)
    main.warm_up()
    (chat_path, chat_body), (embed_path, embed_body) = sent
    assert embed_path == "/api/embed" and embed_body["options"] == {"num_gpu": 0}
    assert chat_path == "/api/chat" and chat_body["messages"] == []
    assert chat_body["options"] == ollama.CHAT_OPTIONS and chat_body["keep_alive"] == embed_body["keep_alive"] == "10m"


def test_warm_up_without_ollama_only_logs(monkeypatch, caplog):
    import urllib.error

    def unreachable(*args, **kwargs):
        raise urllib.error.URLError("bağlantı reddedildi")

    monkeypatch.setattr(ollama, "post", unreachable)
    main.warm_up()
    assert "önceden yüklenemedi" in caplog.text

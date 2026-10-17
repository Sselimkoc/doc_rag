import json
import urllib.request

from app.config import LLM_MODEL, OLLAMA_URL


def post(path: str, body: dict, timeout: int = 300) -> dict:
    request = urllib.request.Request(
        f"{OLLAMA_URL}{path}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def chat_json(system: str, user: str, schema: dict) -> dict:
    response = post(
        "/api/chat",
        {
            "model": LLM_MODEL,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "format": schema,
            "stream": False,
            "options": {"temperature": 0, "num_ctx": 8192, "num_predict": 512}, #aynı girdiye aynı yanıtı almak için 
        },
    )
    # Sınıra çarpan (döngüye giren) cevap yarım JSON'dur; boş cevap sayılır.
    if response.get("done_reason") == "length":
        return {}
    return json.loads(response["message"]["content"])

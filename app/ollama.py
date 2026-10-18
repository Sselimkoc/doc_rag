import json
import logging
import urllib.request

from app.config import LLM_MODEL, OLLAMA_URL

logger = logging.getLogger(__name__)

# Ollama boşta kalan modeli bu süre sonra bellekten atar (varsayılan 5 dk).
KEEP_ALIVE = "10m"
# Yükleme de aynı ayarlarla yapılmalı; num_ctx farklıysa model ilk soruda yeniden yüklenir.
CHAT_OPTIONS = {"temperature": 0, "num_ctx": 8192, "num_predict": 512}


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
            "options": CHAT_OPTIONS,
            "keep_alive": KEEP_ALIVE,
        },
    )
    # Sınıra çarpan (döngüye giren) cevap yarım JSON'dur; boş cevap sayılır.
    if response.get("done_reason") == "length":
        return {}
    try:
        return json.loads(response["message"]["content"])
    except json.JSONDecodeError:
        # Şemaya rağmen bozuk JSON gelebiliyor; cevap okunamazsa reddedilir.
        logger.warning("Model geçersiz JSON döndürdü: %.200s", response["message"]["content"])
        return {}


def load_llm() -> None:
    """Modeli soru beklemeden belleğe yükler; boş mesaj listesi yalnızca yükleme yapar."""
    post("/api/chat", {"model": LLM_MODEL, "messages": [], "options": CHAT_OPTIONS, "keep_alive": KEEP_ALIVE})

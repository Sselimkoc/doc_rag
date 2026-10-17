import os
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def load_env_file(path: Path = ENV_FILE) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


load_env_file()

# Boş bırakılan değer de varsayılanı kullanır.
DATA_DIR = Path(os.environ.get("DOC_RAG_DATA") or "data")
OLLAMA_URL = os.environ.get("OLLAMA_URL") or "http://localhost:11434"
EMBED_MODEL = os.environ.get("EMBED_MODEL") or "bge-m3"
LLM_MODEL = os.environ.get("LLM_MODEL") or "qwen2.5:14b-instruct-q4_K_M"
TESSERACT_CMD = os.environ.get("TESSERACT_CMD") or None 

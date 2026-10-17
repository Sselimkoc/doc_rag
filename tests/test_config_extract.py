import os

from app.config import load_env_file
from app.extract import table_to_markdown


def test_env_file_fills_missing_values_without_overriding_environment(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("# yorum\nDOC_RAG_T1=dosyadan\nDOC_RAG_T2 = \"tırnaklı\"\nDOC_RAG_T3=dosyadan\nbozuk satır\n", encoding="utf-8")
    monkeypatch.delenv("DOC_RAG_T1", raising=False)
    monkeypatch.delenv("DOC_RAG_T2", raising=False)
    monkeypatch.setenv("DOC_RAG_T3", "ortamdan")
    load_env_file(env)
    assert (os.environ["DOC_RAG_T1"], os.environ["DOC_RAG_T2"], os.environ["DOC_RAG_T3"]) == ("dosyadan", "tırnaklı", "ortamdan")
    for key in ("DOC_RAG_T1", "DOC_RAG_T2"):
        monkeypatch.delenv(key)


def test_missing_env_file_is_ignored(tmp_path):
    load_env_file(tmp_path / "yok.env")


def test_table_to_markdown_drops_empty_columns_and_escapes_pipes():
    rows = [["Ad", None, "Değer"], ["a|b", "", "1\n2"]]
    assert table_to_markdown(rows) == "| Ad | Değer |\n| --- | --- |\n| a\\|b | 1 2 |"

"""Arama değerlendirmesi: questions.json'daki sorular için kanıt sayfası ilk k sonuçta mı?

Test belgeleri (testdata/) ayrı bir veri klasöründe indekslenir; uygulamanın data/ klasörüne dokunulmaz.
Kullanım: python eval/retrieval.py [--testdata testdata] [--data eval/.index]
"""

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KS = (1, 3, 5, 10)
CONTENT_TYPES = {".pdf": "application/pdf", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--testdata", type=Path, default=ROOT / "testdata")
    parser.add_argument("--data", type=Path, default=ROOT / "eval" / ".index")
    args = parser.parse_args()

    # app.db veri klasörünü import sırasında okur.
    os.environ["DOC_RAG_DATA"] = str(args.data)
    sys.path.insert(0, str(ROOT))
    from sqlmodel import Session, select

    from app.db import engine, init_db
    from app.embedding import EMBED_MODEL
    from app.models import Document
    from app.processing import process_document
    from app.search import search

    init_db()
    index_documents(args.testdata, Session, engine, select, Document, process_document)

    questions = json.loads((ROOT / "eval" / "questions.json").read_text(encoding="utf-8"))
    with Session(engine) as session:
        filenames = dict(session.exec(select(Document.id, Document.filename)).all())
        rows = []
        for q in questions:
            results = search(session, q["question"], k=max(KS))
            pages = [(filenames[c.document_id], c.page) for c, _ in results]
            wanted = {(e["document"], e["page"]) for e in q["evidence"]}
            rank = next((i for i, p in enumerate(pages, start=1) if p in wanted), None)
            rows.append({"q": q, "rank": rank, "top_score": results[0][1] if results else None, "top": pages[0] if pages else None})

    report(rows, EMBED_MODEL)


def index_documents(testdata, Session, engine, select, Document, process_document):
    """testdata'daki belgeleri indeksler; aynı ad ve boyutta hazır belge varsa atlar."""
    with Session(engine) as session:
        existing = {(d.filename, d.size): d for d in session.exec(select(Document)).all()}
        to_process = []
        for path in sorted(testdata.iterdir()):
            content_type = CONTENT_TYPES.get(path.suffix.lower())
            if content_type is None:
                continue
            document = existing.get((path.name, path.stat().st_size))
            if document is not None and document.status == "ready":
                continue
            if document is None:
                document = Document(filename=path.name, content_type=content_type, size=path.stat().st_size, path=str(path))
                session.add(document)
                session.commit()
                session.refresh(document)
            to_process.append((document.id, path.name))
    for document_id, name in to_process:
        start = time.time()
        process_document(document_id)
        print(f"indekslendi: {name} ({time.time() - start:.1f} s)")


def report(rows, model):
    scored = [r for r in rows if r["q"]["evidence"]]
    print(f"\nModel: {model} | kanıtlı soru: {len(scored)} / {len(rows)}\n")

    def metrics(group):
        hits = {k: sum(1 for r in group if r["rank"] and r["rank"] <= k) for k in KS}
        mrr = sum(1 / r["rank"] for r in group if r["rank"]) / len(group)
        return " ".join(f"{hits[k]:>2}/{len(group):<2}" for k in KS) + f"  {mrr:.3f}"

    header = "  ".join(f"Hit@{k:<2}" for k in KS)
    print(f"{'Grup':<22}{header}  MRR")
    print(f"{'Hepsi':<22}{metrics(scored)}")
    by_type = defaultdict(list)
    for r in scored:
        by_type[r["q"]["type"]].append(r)
    for type_, group in sorted(by_type.items()):
        print(f"{type_:<22}{metrics(group)}")

    print(f"\n{'Soru':<13}{'Tür':<15}{'Sıra':>5}{'Skor':>7}  İlk sonuç")
    for r in rows:
        q = r["q"]
        rank = "-" if not q["evidence"] else (str(r["rank"]) if r["rank"] else ">10")
        score = f"{r['top_score']:.3f}" if r["top_score"] is not None else "-"
        top = f"{r['top'][0]} s.{r['top'][1]}" if r["top"] else "-"
        print(f"{q['id']:<13}{q['type']:<15}{rank:>5}{score:>7}  {top}")


if __name__ == "__main__":
    main()

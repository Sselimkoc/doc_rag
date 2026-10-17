"""Cevap değerlendirmesi: questions.json'daki her soru /answer mantığından geçirilir.

Doğru sayılır: cevaplanabilen soruda cevap verilmiş ve bütün anahtar sözcükler (listeyse biri) cevapta geçiyor;
cevaplanamayan soruda cevap verilmemiş. Kanıt: doğrulanmış alıntılardan biri kanıt sayfasında. Bağlam: kanıt sayfası modele verilen kaynaklarda.
Kullanım: python eval/answers.py [--testdata testdata] [--data eval/.index] [--only id1,id2]
"""

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--testdata", type=Path, default=ROOT / "testdata")
    parser.add_argument("--data", type=Path, default=ROOT / "eval" / ".index")
    parser.add_argument("--only", default="")
    args = parser.parse_args()

    os.environ["DOC_RAG_DATA"] = str(args.data)
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "eval"))
    from sqlmodel import Session, select

    from app.answer import answer_question, normalize
    from app.config import LLM_MODEL
    from app.db import engine, init_db
    from app.models import Document
    from app.processing import process_document
    from retrieval import index_documents

    init_db()
    index_documents(args.testdata, Session, engine, select, Document, process_document)

    questions = json.loads((ROOT / "eval" / "questions.json").read_text(encoding="utf-8"))
    if args.only:
        questions = [q for q in questions if q["id"] in args.only.split(",")]

    rows = []
    with Session(engine) as session:
        for q in questions:
            start = time.time()
            r = answer_question(session, q["question"])
            seconds = time.time() - start
            if q["answerable"]:
                # Liste olan anahtar sözcükte seçeneklerden biri yeterli (ör. "45" / "kırkbeş").
                answer = normalize(r.answer)
                correct = r.answered and all(
                    any(normalize(a) in answer for a in (k if isinstance(k, list) else [k])) for k in q["keywords"]
                )
            else:
                correct = not r.answered
            wanted = {(e["document"], e["page"]) for e in q["evidence"]}
            cited = any((c.filename, c.page) in wanted for c in r.citations)
            # Kanıt sayfası modele verilen kaynaklarda mı: yanlış cevabı arama ve üretim hatası olarak ayırır.
            in_context = any((s.filename, s.page) in wanted for s in r.sources)
            rows.append({"id": q["id"], "type": q["type"], "answerable": q["answerable"], "correct": correct,
                         "cited_evidence": cited, "in_context": in_context, "seconds": round(seconds, 1), "response": r.model_dump()})
            print(f"{q['id']:<13}{'✓' if correct else '✗'}  {seconds:5.1f} s  {r.refusal or ''}", flush=True)

    out = args.data / "answers.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    report(rows, LLM_MODEL, out)


def report(rows, model, out):
    print(f"\nModel: {model} | soru: {len(rows)}\n")
    groups = defaultdict(list)
    for r in rows:
        groups["Hepsi"].append(r)
        groups["cevaplanabilen" if r["answerable"] else "cevaplanamayan"].append(r)
        groups[r["type"]].append(r)
    print(f"{'Grup':<18}{'Doğru':>8}{'Kanıtlı':>9}{'Bağlamda':>10}")
    types = sorted({r["type"] for r in rows})
    for name in ("Hepsi", "cevaplanabilen", "cevaplanamayan", *types):
        group = groups[name]
        if not group:
            continue
        correct = sum(r["correct"] for r in group)
        answered = [r for r in group if r["response"]["answered"]]
        cited = sum(r["cited_evidence"] for r in answered)
        scored = [r for r in group if r["answerable"]]
        in_context = sum(r["in_context"] for r in scored)
        print(f"{name:<18}{correct:>4}/{len(group):<3}{cited:>5}/{len(answered):<3}{in_context:>6}/{len(scored):<3}")
    wrong = [r for r in rows if r["answerable"] and not r["correct"]]
    missed = sum(not r["in_context"] for r in wrong)
    print(f"\nYanlış cevaplanabilen: {len(wrong)} (arama hatası {missed}, kanıt bağlamdaydı {len(wrong) - missed})")
    seconds = sorted(r["seconds"] for r in rows)
    print(f"\nSüre: medyan {seconds[len(seconds) // 2]} s, en uzun {seconds[-1]} s")
    print(f"\n{'Soru':<13}{'Tür':<15}{'Sonuç':<7}{'Kanıt':<7}{'Bağlam':<8}{'Ret':<16}Cevap")
    for r in rows:
        resp = r["response"]
        print(f"{r['id']:<13}{r['type']:<15}{'doğru' if r['correct'] else 'YANLIŞ':<7}"
              f"{('evet' if r['cited_evidence'] else 'hayır') if resp['answered'] else '-':<7}"
              f"{('evet' if r['in_context'] else 'hayır') if r['answerable'] else '-':<8}"
              f"{resp['refusal'] or '':<16}{resp['answer'][:70]}")
    print(f"\nAyrıntı: {out}")


if __name__ == "__main__":
    main()

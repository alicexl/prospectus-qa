"""自测评估：python -X utf8 evaluate.py --answers A --labels L [--dump-template Q]
指标：数值准确率(±0.5%)、列表条目P/R/F1、引用正确率(独立重验)、拒答P/R、延迟与成本。"""
import argparse
import json
import re
import sqlite3
import statistics
import sys
from pathlib import Path

_DB = Path(__file__).parent / "data" / "knowledge.db"

# ---------- 数值题 ----------
_FAC = {"元": 1.0, "万元": 1e4, "亿元": 1e8}


def numeric_correct(pred: dict, gold: dict, tol: float = 0.005) -> bool:
    if pred.get("answer_type") != "number":
        return False
    pv, gv = pred.get("value") or {}, gold.get("value") or {}
    if pv.get("number") is None or gv.get("number") is None:
        return False
    v, pu, gu = pv["number"], pv.get("unit"), gv.get("unit")
    if pu != gu and pu in _FAC and gu in _FAC:
        v = v * _FAC[pu] / _FAC[gu]
    return abs(v - gv["number"]) / max(abs(gv["number"]), 1e-9) <= tol


# ---------- 列表题 ----------
def _item_match(a: str, b: str) -> bool:
    a, b = a.strip(), b.strip()
    if a == b:
        return True
    return len(a) >= 4 and len(b) >= 4 and (a in b or b in a)


def list_prf(pred: dict, gold: dict) -> tuple[float, float, float]:
    ps = [i.strip() for i in pred.get("items") or []]
    gs = [i.strip() for i in gold.get("items") or []]
    used, tp = set(), 0
    for g in gs:
        for j, p in enumerate(ps):
            if j not in used and _item_match(p, g):
                used.add(j)
                tp += 1
                break
    prec = tp / len(ps) if ps else 0.0
    rec = tp / len(gs) if gs else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return prec, rec, f1


# ---------- 引用正确率（独立重验，不信 run 自报） ----------
def _norm(s: str) -> str:
    t = str.maketrans("０１２３４５６７８９（）　：，。", "0123456789() :，.")
    return re.sub(r"\s+", "", s.translate(t))


def citation_acc(pred: dict, pages_conn: sqlite3.Connection | None) -> float:
    cites = pred.get("citations") or []
    if pred.get("answer_type") != "refusal" and not cites:
        return 0.0
    if not cites:
        return 1.0  # 拒答题无引用视为合规
    if pages_conn is None:
        return 0.0
    ok = 0
    for c in cites:
        row = pages_conn.execute(
            "SELECT text FROM pages WHERE doc_id=? AND pdf_page=?",
            (c.get("doc_id"), c.get("pdf_page"))).fetchone()
        if row and _norm(c.get("quote", "")) in _norm(row[0]):
            ok += 1
    return ok / len(cites)


# ---------- 拒答 ----------
def refusal_pr(preds: list[dict], golds: dict) -> tuple[float, float]:
    tp = fp = fn = 0
    for p in preds:
        pr = p["refused"]
        g = golds.get(p["q"])
        if g is None:
            continue
        if pr and g:
            tp += 1
        elif pr and not g:
            fp += 1
        elif not pr and g:
            fn += 1
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    return prec, rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--dump-template")
    args = ap.parse_args()

    if args.dump_template:
        for line in open(args.dump_template, encoding="utf-8"):
            if not line.strip():
                continue
            item = json.loads(line)
            print(json.dumps({"q": item["question_id"], "question": item["question"],
                              "answer_type": None, "value": None, "items": None,
                              "expect_refusal": None, "citations_expected": None},
                             ensure_ascii=False))
        return

    answers = [json.loads(l) for l in open(args.answers, encoding="utf-8") if l.strip()]
    labels = {x["q"]: x for x in (json.loads(l) for l in open(args.labels, encoding="utf-8")
                                  if l.strip())}
    pages_conn = (sqlite3.connect(f"file:{_DB}?mode=ro", uri=True)
                  if _DB.exists() else None)

    nums = [(a, labels[a["question_id"]]) for a in answers
            if labels.get(a["question_id"], {}).get("answer_type") == "number"]
    lists_ = [(a, labels[a["question_id"]]) for a in answers
              if labels.get(a["question_id"], {}).get("answer_type") == "list"]
    scorable = nums + lists_

    prf = [list_prf(a, g) for a, g in lists_]
    lat = sorted(a.get("latency_ms", 0) for a in answers)
    toks = [a.get("tokens", {}) for a in answers]
    cost = [(t.get("input", 0), t.get("output", 0)) for t in toks]

    metrics = {
        "数值题准确率(±0.5%)": (sum(numeric_correct(a, g) for a, g in nums) / len(nums))
        if nums else None,
        "列表P/R/F1": [[round(x, 4) for x in p] for p in prf] or None,
        "引用正确率(独立重验)": (sum(citation_acc(a, pages_conn) for a, g in scorable)
                              / len(scorable)) if scorable else None,
        "拒答P/R": list(refusal_pr(
            [{"q": a["question_id"], "refused": a["answer_type"] == "refusal"} for a in answers],
            {q: l["expect_refusal"] for q, l in labels.items()
             if l.get("expect_refusal") is not None})),
        "延迟avg/P95_ms": [int(statistics.mean(lat)), lat[int(0.95 * (len(lat) - 1))]] if lat else None,
        "单题平均tokens(in/out)": [int(statistics.mean(c[0] for c in cost)),
                                int(statistics.mean(c[1] for c in cost))] if cost else None,
    }
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    Path("results").mkdir(exist_ok=True)
    json.dump(metrics, open("results/metrics.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    if pages_conn is not None:
        pages_conn.close()


if __name__ == "__main__":
    main()

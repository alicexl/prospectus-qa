"""合并试点+批量标注 → labels_full.jsonl（1000题终稿）+ 总统计。
CLI: python -X utf8 merge_labels.py
"""
import json
from collections import Counter
from pathlib import Path

SOURCES = ["labels_pilot.jsonl", "labels_batch_0.jsonl",
           "labels_batch_1.jsonl", "labels_batch_2.jsonl"]
OUT = "labels_full.jsonl"


def main():
    rows = []
    seen = set()
    for src in SOURCES:
        p = Path(src)
        if not p.exists():
            print(f"[warn] 缺 {src}")
            continue
        for line in p.open(encoding="utf-8"):
            if not line.strip():
                continue
            r = json.loads(line)
            if r["id"] in seen:
                continue
            seen.add(r["id"])
            rows.append(r)
    with open(OUT, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    n = len(rows)
    auto = [r for r in rows if r["verification_status"] == "auto_verified"]
    rev = [r for r in rows if r["verification_status"] == "needs_review"]
    print(f"合计 {n} 题（去重后）")
    print("状态:", dict(Counter(r["verification_status"] for r in rows)))
    print("题型:", dict(Counter(str(r["qtype"]) for r in rows)))
    print("answer_type:", dict(Counter(str(r["answer_type"]) for r in rows)))
    print(f"auto {len(auto)} / review {len(rev)}（{len(auto)*100//max(n,1)}%）")
    print("复核原因:", dict(Counter(x for r in rev for x in r["review_reasons"])))


if __name__ == "__main__":
    main()

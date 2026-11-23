"""rankings/날짜.json(원본) → data/날짜.json(공유 페이지용: 전일 대비, 14일 추이, 이탈 목록).

GitHub Actions(매일 자동 수집)와 Mac의 publish.py가 함께 사용합니다.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RANK = HERE / "rankings"
OUT = HERE / "data"


def load(d):
    return json.loads((RANK / f"{d}.json").read_text(encoding="utf-8"))


def view(ds, idx):
    d = ds[idx]
    prev = ds[idx - 1] if idx > 0 else None
    hist_dates = ds[max(0, idx - 13): idx + 1]
    hist = {hd: {i["goodsNo"]: i["rank"] for i in load(hd)} for hd in hist_dates}
    prev_map = hist.get(prev, {}) if prev else {}
    items = []
    for it in load(d):
        no = it["goodsNo"]
        pr = prev_map.get(no) if prev else None
        cat = (it.get("category") or "").split(">")
        items.append(it | {
            "prevRank": pr,
            "change": (pr - it["rank"]) if pr else None,
            "isNew": bool(prev) and pr is None,
            "cat1": cat[1].strip() if len(cat) > 1 else "",
            "history": [hist[hd].get(no) for hd in hist_dates],
        })
    dropped = []
    if prev:
        cur = {i["goodsNo"] for i in items}
        dropped = [{"rank": r["rank"], "brand": r["brand"], "name": r["name"]}
                   for r in load(prev) if r["goodsNo"] not in cur]
    return {"date": d, "prev": prev, "dates": ds, "histDates": hist_dates,
            "items": items, "dropped": dropped}


def main():
    OUT.mkdir(exist_ok=True)
    ds = sorted(f.stem for f in RANK.glob("*.json"))
    for i, d in enumerate(ds):
        (OUT / f"{d}.json").write_text(json.dumps(view(ds, i), ensure_ascii=False), encoding="utf-8")
    (OUT / "latest.json").write_text(json.dumps({"date": ds[-1] if ds else None}), encoding="utf-8")
    print(f"공유 페이지 데이터 {len(ds)}일치 생성")


if __name__ == "__main__":
    main()

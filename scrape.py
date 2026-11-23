"""GitHub Actions에서 매일 올리브영 랭킹 수집 → rankings/오늘날짜.json (한국 날짜 기준).

수집 방식은 Mac의 ranking.py와 같습니다 (실제 Chrome을 창 모드로 실행, 서버에선 가상 화면 사용).
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
URL = "https://www.oliveyoung.co.kr/store/main/getBestList.do"

EXTRACT_JS = """
() => [...document.querySelectorAll('ul.cate_prd_list > li .prd_info')].map(el => {
  const a = el.querySelector('a.prd_thumb');
  const num = s => s ? parseInt(s.replace(/[^0-9]/g, ''), 10) : null;
  const zzim = el.querySelector('.btn_zzim');
  return {
    rank: num(el.querySelector('.thumb_flag')?.textContent),
    goodsNo: a?.dataset.refGoodsno,
    brand: el.querySelector('.tx_brand')?.textContent.trim(),
    name: el.querySelector('.tx_name')?.textContent.trim(),
    category: zzim?.dataset.refGoodscategory || null,
    priceOrg: num(el.querySelector('.tx_org .tx_num')?.textContent),
    priceCur: num(el.querySelector('.tx_cur .tx_num')?.textContent),
    flags: [...el.querySelectorAll('.prd_flag .icon_flag')].map(f => f.textContent.trim()),
    thumb: el.querySelector('a.prd_thumb img')?.src,
    url: a ? 'https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=' + a.dataset.refGoodsno : null,
  };
})
"""


def main():
    today = datetime.now(timezone(timedelta(hours=9))).date().isoformat()
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir="/tmp/oy_profile", channel="chrome", headless=False,
            locale="ko-KR", timezone_id="Asia/Seoul", viewport={"width": 1280, "height": 900},
        )
        page = ctx.new_page()
        resp = page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        print(f"접속 상태 {resp.status if resp else '?'}")
        try:
            page.wait_for_selector("ul.cate_prd_list .prd_info", timeout=60000)
        except Exception:
            print("페이지 제목:", page.title())
            print(page.content()[:1500])
            raise
        items = [i for i in page.evaluate(EXTRACT_JS) if i.get("goodsNo")]
        ctx.close()
    print(f"상품 {len(items)}개 수집")
    if len(items) < 50:
        sys.exit("수집 결과가 너무 적습니다. 차단됐거나 페이지 구조가 바뀌었을 수 있습니다.")
    (HERE / "rankings").mkdir(exist_ok=True)
    (HERE / "rankings" / f"{today}.json").write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"저장: rankings/{today}.json")


if __name__ == "__main__":
    main()

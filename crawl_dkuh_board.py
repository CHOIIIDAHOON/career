#!/usr/bin/env python3
import html
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://www.dkuh.co.kr"
LIST_URL = f"{BASE_URL}/board5/bbs/board"


def _fetch_page(keyword: str, page: int) -> str:
    query = urlencode(
        {
            "bo_table": "01_03_05",
            "sca": "",
            "sop": "and",
            "sfl": "wr_subject",
            "stx": keyword,
            "page": str(page),
        }
    )
    req = Request(
        f"{LIST_URL}?{query}",
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
        },
    )
    with urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _extract_last_page(page_html: str) -> int:
    pages = [int(x) for x in re.findall(r"[?&]page=(\d+)", page_html)]
    return max(pages) if pages else 1


def _strip_tags(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip()


def _parse_rows(page_html: str, only_in_progress: bool = True):
    tbody_m = re.search(r"<tbody>(.*?)</tbody>", page_html, re.S | re.I)
    if not tbody_m:
        return []

    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", tbody_m.group(1), re.S | re.I):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)
        # 예상 컬럼: 번호, 채용분야, 제목, 채용기간, 진행상황, 조회
        if len(tds) < 6:
            continue

        title_td = tds[2]
        a_m = re.search(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', title_td, re.S | re.I)
        if not a_m:
            continue

        href = html.unescape(a_m.group(1)).strip()
        title = _strip_tags(a_m.group(2))
        period = _strip_tags(tds[3])
        status = _strip_tags(tds[4])

        if only_in_progress and status != "진행중":
            continue

        date_text = ""
        # 채용기간이 YYYY-MM-DD~YYYY-MM-DD 형태이므로 시작일을 일자로 사용
        m_date = re.match(r"(\d{4}-\d{2}-\d{2})~", period)
        if m_date:
            date_text = m_date.group(1)

        full_link = href if href.startswith("http") else f"{BASE_URL}{href if href.startswith('/') else '/' + href}"
        rows.append({"제목": title, "링크": full_link, "일자": date_text, "상태": status})

    return rows


def crawl_dkuh(keyword: str = "전산"):
    first_html = _fetch_page(keyword=keyword, page=1)
    last_page = _extract_last_page(first_html)

    results = _parse_rows(first_html, only_in_progress=True)
    for p in range(2, last_page + 1):
        html_text = _fetch_page(keyword=keyword, page=p)
        results.extend(_parse_rows(html_text, only_in_progress=True))

    # 응답 스키마는 공통(제목/링크/일자) 유지
    return [{"제목": r["제목"], "링크": r["링크"], "일자": r["일자"]} for r in results]

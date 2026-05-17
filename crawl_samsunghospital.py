#!/usr/bin/env python3
import html
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://www.samsunghospital.com"
LIST_URL = f"{BASE_URL}/home/recruit/recruitInfo/recruitNotice.do"


def _fetch_page(cpage: int) -> str:
    url = LIST_URL if cpage == 1 else f"{LIST_URL}?{urlencode({'cPage': f'{cpage:02d}'})}"
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
        },
    )
    with urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _extract_last_page(page_html: str) -> int:
    pages = [int(x) for x in re.findall(r"recruitNotice\.do\?cPage=(\d+)", page_html)]
    return max(pages) if pages else 1


def _strip_tags(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip()


def _contains_keywords(title: str, keywords: list[str]) -> bool:
    title_upper = title.upper()
    for kw in keywords:
        if kw.upper() == "IT":
            if "IT" in title_upper:
                return True
            continue
        if kw in title:
            return True
    return False


def _parse_rows(page_html: str, keywords: list[str]):
    tbody_m = re.search(r"<tbody>(.*?)</tbody>", page_html, re.S | re.I)
    if not tbody_m:
        return []

    results = []
    for tr in re.findall(r"<tr>(.*?)</tr>", tbody_m.group(1), re.S | re.I):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)
        # 번호,구분,직종,제목,접수기간,마감일,접수형태/진행상황
        if len(tds) < 7:
            continue

        a_m = re.search(r'<a\s+href="([^"]+)"[^>]*>(.*?)</a>', tds[3], re.S | re.I)
        if not a_m:
            continue

        href = html.unescape(a_m.group(1)).strip()
        title = _strip_tags(a_m.group(2))

        status_text = _strip_tags(tds[6])
        if "진행중" not in status_text:
            continue

        if not _contains_keywords(title, keywords):
            continue

        period_text = _strip_tags(tds[4])
        date_text = ""
        m = re.search(r"(\d{4}\.\d{2}\.\d{2})", period_text)
        if m:
            date_text = m.group(1).replace(".", "-")

        full_link = href if href.startswith("http") else f"{BASE_URL}{href if href.startswith('/') else '/' + href}"
        results.append({"제목": title, "링크": full_link, "일자": date_text})

    return results


def crawl_samsunghospital(keyword: str = "전산|IT"):
    keywords = [k.strip() for k in keyword.split("|") if k.strip()]
    if not keywords:
        keywords = ["전산", "IT"]

    first_html = _fetch_page(1)
    last_page = _extract_last_page(first_html)

    rows = _parse_rows(first_html, keywords)
    for p in range(2, last_page + 1):
        page_html = _fetch_page(p)
        rows.extend(_parse_rows(page_html, keywords))

    return rows

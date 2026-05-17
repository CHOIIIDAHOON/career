#!/usr/bin/env python3
import html
import re
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

BASE_URL = "https://recruit.hallym.or.kr"
LIST_PATH = "/hrt_p10_list.jsp"
LIST_URL = f"{BASE_URL}{LIST_PATH}"


def _fetch_page(move_page: int, tabdet: str = "3", search_text: str = "") -> str:
    query = urlencode(
        {
            "inggbn": "ing",
            "movePage": str(move_page),
            "search_text": search_text,
            "tabdet": tabdet,
        }
    )
    url = f"{LIST_URL}?{query}"
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


def _extract_max_page(page_html: str) -> int:
    page_nums = [int(x) for x in re.findall(r"movePage=(\d+)", page_html)]
    return max(page_nums) if page_nums else 1


def _parse_ing_list(page_html: str):
    section_m = re.search(
        r'<div class="cen_rct_list"[^>]*id="rct_list_ing"[^>]*>(.*?)</div>\s*<div class="cen_rct_list"',
        page_html,
        re.S | re.I,
    )
    if not section_m:
        return []

    section = section_m.group(1)
    items = []
    blocks = re.findall(r"<a\s+href\s*=\s*\"([^\"]+)\"\s*>\s*<li>(.*?)</li>\s*</a>", section, re.S | re.I)

    for href, li_html in blocks:
        p_m = re.search(r"<p>(.*?)</p>", li_html, re.S | re.I)
        if not p_m:
            continue

        p_html = p_m.group(1)
        dates = re.findall(r"<span>([^<]+)</span>", p_html, re.S | re.I)
        raw_date = dates[-1].strip() if dates else ""

        title_html = re.sub(r"<span>[^<]*</span>\s*$", "", p_html, flags=re.S | re.I)
        title_text = re.sub(r"<[^>]+>", "", title_html)
        title_text = re.sub(r"\s+", " ", html.unescape(title_text)).strip()

        items.append(
            {
                "제목": title_text,
                "링크": urljoin(BASE_URL, href),
                "일자": raw_date.replace(".", "-") if raw_date else "",
            }
        )

    return items


def crawl_hallym_ilsong(keyword: str = "전산"):
    first = _fetch_page(move_page=1, tabdet="3", search_text="")
    max_page = _extract_max_page(first)

    rows = _parse_ing_list(first)
    for page in range(2, max_page + 1):
        html_text = _fetch_page(move_page=page, tabdet="3", search_text="")
        rows.extend(_parse_ing_list(html_text))

    keyword_norm = keyword.strip()
    if keyword_norm:
        rows = [r for r in rows if keyword_norm in r["제목"]]

    return rows

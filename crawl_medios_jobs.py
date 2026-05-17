#!/usr/bin/env python3
import argparse
import html
import json
import re
from http.cookiejar import CookieJar
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener

BASE_URL = "https://www.medios.or.kr"
LIST_URL = f"{BASE_URL}/front/ea/e3/0100/getInitPage.do"
DETAIL_URL = f"{BASE_URL}/front/ea/e3/0100/getBbsDetailPage.do"


class MediosCrawler:
    def __init__(self):
        cj = CookieJar()
        self.opener = build_opener(HTTPCookieProcessor(cj))
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
        }

    def _request(self, url: str, data: dict | None = None) -> str:
        body = urlencode(data).encode("utf-8") if data else None
        req = Request(url, data=body, headers=self.headers)
        with self.opener.open(req, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="replace")

    def init_session(self):
        self._request(LIST_URL)

    def fetch_page(self, keyword: str, page_index: int) -> str:
        data = {
            "PAGE_INDEX": str(page_index),
            "PAGE_UNIT": "10",
            "MENUID": "",
            "BBS_SEQ": "",
            "S_SEARCH_KND": "A",
            "S_SEARCH_VAL": keyword,
        }
        return self._request(LIST_URL, data=data)


def strip_tags(text: str) -> str:
    no_tag = re.sub(r"<[^>]+>", "", text)
    return html.unescape(no_tag).strip()


def extract_last_page(page_html: str) -> int:
    m = re.search(r'class="icon lastBtn"[^>]*onclick="[^"]*fn_gFormSubmit\((\d+)\)', page_html)
    return int(m.group(1)) if m else 1


def parse_rows(page_html: str):
    tbody_m = re.search(r"<tbody>(.*?)</tbody>", page_html, re.S | re.I)
    if not tbody_m:
        return []

    rows = []
    tbody = tbody_m.group(1)
    tr_blocks = re.findall(r"<tr[^>]*>(.*?)</tr>", tbody, re.S | re.I)

    for tr in tr_blocks:
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)
        if len(tds) < 6:
            continue

        title_html = tds[1]
        bbs_m = re.search(r"fn_goDetail\('?(\d+)'?\)", title_html)
        bbs_seq = bbs_m.group(1) if bbs_m else ""

        title_span_m = re.search(r"<span[^>]*>(.*?)</span>", title_html, re.S | re.I)
        title = strip_tags(title_span_m.group(1) if title_span_m else title_html)

        rows.append(
            {
                "제목": re.sub(r"\s+", " ", title),
                "링크": f"{DETAIL_URL}?BBS_SEQ={bbs_seq}" if bbs_seq else DETAIL_URL,
                "일자": strip_tags(tds[3]),
            }
        )

    return rows


def crawl_medios(keyword: str = "전산"):
    crawler = MediosCrawler()
    crawler.init_session()

    first_page = crawler.fetch_page(keyword, 1)
    last_page = extract_last_page(first_page)

    all_rows = parse_rows(first_page)
    for page in range(2, last_page + 1):
        html_text = crawler.fetch_page(keyword, page)
        all_rows.extend(parse_rows(html_text))

    return all_rows


def main():
    parser = argparse.ArgumentParser(description="전국지방의료원연합회 채용정보 크롤러")
    parser.add_argument("--keyword", default="전산", help="제목 검색어")
    args = parser.parse_args()

    result = crawl_medios(args.keyword)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

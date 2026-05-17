#!/usr/bin/env python3
import json
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_URL = "https://api.ninehire.com/identity-access/homepage/recruitments"
COMPANY_ID = "1efc6e10-b492-11f0-a324-9d3a091a4147"
BASE_URL = "https://kbsmcrecruit.ninehire.site"


def _fetch_page(page: int, count_per_page: int = 20):
    query = urlencode(
        {
            "companyId": COMPANY_ID,
            "page": str(page),
            "countPerPage": str(count_per_page),
        }
    )
    req = Request(
        f"{API_URL}?{query}",
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
        },
    )
    with urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


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


def crawl_kbsmc_ninehire(keyword: str = "전산|IT"):
    # keyword 예: "전산|IT" 또는 "전산"
    keywords = [k.strip() for k in keyword.split("|") if k.strip()]
    if not keywords:
        keywords = ["전산", "IT"]

    page = 1
    count_per_page = 20
    matched = []

    while True:
        data = _fetch_page(page=page, count_per_page=count_per_page)
        results = data.get("results", [])
        if not results:
            break

        for item in results:
            title = (item.get("externalTitle") or item.get("title") or "").strip()
            if not title:
                continue
            if not _contains_keywords(title, keywords):
                continue

            address_key = item.get("addressKey")
            link = f"{BASE_URL}/job_posting/{address_key}" if address_key else BASE_URL
            deadline = (item.get("deadlineValue") or "")[:10]

            matched.append(
                {
                    "제목": title,
                    "링크": link,
                    "일자": deadline,
                }
            )

        if len(results) < count_per_page:
            break
        page += 1

    return matched

#!/usr/bin/env python3
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://nhimc.recruiter.co.kr"
LIST_API = f"{BASE_URL}/app/jobnotice/list.json"
VIEW_URL = f"{BASE_URL}/app/jobnotice/view"


def _fetch_page(keyword: str, page: int, page_size: int = 10):
    data = {
        "recruitClassSn": "",
        "recruitClassName": "",
        "jobnoticeStateCode": "10",
        "pageSize": str(page_size),
        "searchByNameOnly": "true",
        "currentPage": str(page),
        "keyword": keyword,
    }
    body = urlencode(data).encode("utf-8")
    req = Request(
        LIST_API,
        data=body,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        },
    )
    with urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def crawl_nhimc(keyword: str = "정규직"):
    page = 1
    page_size = 10
    rows = []

    while True:
        data = _fetch_page(keyword=keyword, page=page, page_size=page_size)
        page_util = data.get("pageUtil", {})
        items = data.get("list", [])

        for obj in items:
            title = (obj.get("jobnoticeName") or "").strip()
            jobnotice_sn = obj.get("jobnoticeSn")
            system_kind_code = obj.get("systemKindCode")
            link = f"{VIEW_URL}?systemKindCode={system_kind_code}&jobnoticeSn={jobnotice_sn}"

            end_dt = obj.get("applyEndDate") or {}
            year = end_dt.get("year")
            month = end_dt.get("month")
            day = end_dt.get("date")
            date_text = ""
            if isinstance(year, int) and isinstance(month, int) and isinstance(day, int):
                date_text = f"{year + 1900:04d}-{month + 1:02d}-{day:02d}"

            rows.append({"제목": title, "링크": link, "일자": date_text})

        last_page = int(page_util.get("lastPage") or 1)
        if page >= last_page:
            break
        page += 1

    return rows

#!/usr/bin/env python3
import argparse
import json
import os

from crawl_medios_jobs import crawl_medios
from crawl_hallym_ilsong import crawl_hallym_ilsong
from crawl_kbsmc_ninehire import crawl_kbsmc_ninehire
from crawl_nhimc_recruiter import crawl_nhimc
from crawl_dkuh_board import crawl_dkuh
from crawl_samsunghospital import crawl_samsunghospital
from crawl_job_portals import crawl_job_portals, crawl_job_portals_by_role

DEFAULT_TECH_TITLE_TERMS = ["전산", "개발", "it", "백앤드", "프론트앤드", "백엔드", "프론트엔드", "emr"]
DEV_EXCLUDE_TERMS = ["사업개발", "재개발"]


def get_tech_title_terms() -> list[str]:
    """
    환경변수 TECH_TITLE_TERMS가 있으면 그 값을 사용한다.
    예) TECH_TITLE_TERMS="전산,개발,it,emr,백엔드,프론트엔드"
    """
    raw = os.getenv("TECH_TITLE_TERMS", "").strip()
    if not raw:
        return DEFAULT_TECH_TITLE_TERMS
    items = [x.strip().lower() for x in raw.split(",") if x.strip()]
    return items or DEFAULT_TECH_TITLE_TERMS


def _is_tech_title(title: str) -> bool:
    t = title.lower()
    # 개발은 비IT 문맥(사업개발/재개발) 제외
    if "개발" in t:
        if not any(ex in t for ex in DEV_EXCLUDE_TERMS):
            return True
    return any(term in t for term in get_tech_title_terms())

# 다른 공기업 크롤러를 계속 추가할 리스트
CRAWLER_LIST = [
    {
        "code": "medios",
        "name": "전국지방의료원연합회",
        "runner": crawl_medios,
        "default_keyword": "전산",
    },
    {
        "code": "hallym_ilsong",
        "name": "일송학원(한림대학교의료원)",
        "runner": crawl_hallym_ilsong,
        "default_keyword": "전산",
    },
    {
        "code": "kbsmc",
        "name": "강북삼성병원",
        "runner": crawl_kbsmc_ninehire,
        "default_keyword": "전산|IT",
    },
    {
        "code": "nhimc",
        "name": "국민건강보험공단 일산병원",
        "runner": crawl_nhimc,
        "default_keyword": "정규직",
    },
    {
        "code": "dkuh",
        "name": "단국대학교병원",
        "runner": crawl_dkuh,
        "default_keyword": "전산",
    },
    {
        "code": "ssmc",
        "name": "삼성서울병원",
        "runner": crawl_samsunghospital,
        "default_keyword": "전산|IT",
    },
    {
        "code": "job_portal",
        "name": "잡코리아+사람인(공통)",
        "runner": crawl_job_portals,
        "default_keyword": "GC메디아이",
    },
    {
        "code": "job_portal_role",
        "name": "잡코리아+사람인(직무검색)",
        "runner": crawl_job_portals_by_role,
        "default_keyword": "emr",
    },
]


def run_crawler(code: str, keyword: str | None = None, job_category: str | None = None):
    for crawler in CRAWLER_LIST:
        if crawler["code"] == code:
            use_keyword = keyword if keyword is not None else crawler["default_keyword"]
            if code in ("job_portal", "job_portal_role"):
                rows = crawler["runner"](use_keyword, job_category or "")
            else:
                rows = crawler["runner"](use_keyword)
            return {
                "기관": crawler["name"],
                "검색어": use_keyword,
                "직무카테고리": job_category if code in ("job_portal", "job_portal_role") else None,
                "결과": rows,
            }
    raise ValueError(f"unknown crawler code: {code}")


def run_all_crawlers(keyword: str | None = None):
    results = []
    for crawler in CRAWLER_LIST:
        use_keyword = keyword if keyword is not None else crawler["default_keyword"]
        results.append(
            {
                "code": crawler["code"],
                "기관": crawler["name"],
                "검색어": use_keyword,
                "결과": crawler["runner"](use_keyword),
            }
        )
    return {"조회대상수": len(CRAWLER_LIST), "목록": results}


def run_combined_search(keyword: str):
    if not keyword:
        raise ValueError("combined search requires --keyword")

    merged = []
    for crawler in CRAWLER_LIST:
        rows = crawler["runner"](keyword)
        for row in rows:
            item = dict(row)
            item["출처기관"] = crawler["name"]
            item["출처코드"] = crawler["code"]
            merged.append(item)

    # combined는 입력 키워드 포함 + 제목 내 기술직무 키워드 포함 조건을 동시에 만족해야 한다.
    filtered = []
    seen = set()
    k = keyword.lower().strip()
    for item in merged:
        title = f"{item.get('제목', '')}".lower()
        text = f"{title} {item.get('회사', '')} {item.get('직무분류', '')}".lower()
        if k and k not in text:
            continue
        if not _is_tech_title(title):
            continue

        key = item.get("링크") or (
            item.get("플랫폼", ""),
            item.get("회사", ""),
            item.get("제목", ""),
            item.get("일자", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        filtered.append(item)

    return {
        "기관": "통합검색",
        "검색어": keyword,
        "결과": filtered,
    }


def main():
    parser = argparse.ArgumentParser(description="공기업 채용 크롤러 메인")
    parser.add_argument(
        "--code",
        default="all",
        help="크롤러 코드 (all: 전체 조회, combined: 단일 배열 통합검색)",
    )
    parser.add_argument("--keyword", default=None, help="검색어 (미입력 시 기본 검색어 사용)")
    parser.add_argument("--job-category", default=None, help="직무카테고리 필터 (job_portal/job_portal_role 전용)")
    args = parser.parse_args()

    if args.code == "all":
        result = run_all_crawlers(args.keyword)
    elif args.code == "combined":
        result = run_combined_search(args.keyword or "")
    else:
        result = run_crawler(args.code, args.keyword, args.job_category)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

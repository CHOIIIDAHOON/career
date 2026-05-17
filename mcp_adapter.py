#!/usr/bin/env python3
import argparse
import json
from typing import Any

from main import CRAWLER_LIST, run_all_crawlers, run_crawler, run_combined_search


def _ok(tool: str, input_data: dict[str, Any], data: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "tool": tool,
        "input": input_data,
        "data": data,
        "error": None,
    }


def _err(tool: str, input_data: dict[str, Any], message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "tool": tool,
        "input": input_data,
        "data": None,
        "error": message,
    }


def cmd_list_sources() -> dict[str, Any]:
    rows = []
    for c in CRAWLER_LIST:
        rows.append(
            {
                "code": c["code"],
                "name": c["name"],
                "default_keyword": c["default_keyword"],
                "supports_job_category": c["code"] in ("job_portal", "job_portal_role"),
            }
        )
    return _ok("list_sources", {}, {"sources": rows, "count": len(rows)})


def cmd_search_source(code: str, keyword: str | None, job_category: str | None) -> dict[str, Any]:
    input_data = {"code": code, "keyword": keyword, "job_category": job_category}
    try:
        data = run_crawler(code, keyword, job_category)
        return _ok("search_source", input_data, data)
    except Exception as e:  # noqa: BLE001
        return _err("search_source", input_data, str(e))


def cmd_search_all(keyword: str | None) -> dict[str, Any]:
    input_data = {"keyword": keyword}
    try:
        data = run_all_crawlers(keyword)
        return _ok("search_all", input_data, data)
    except Exception as e:  # noqa: BLE001
        return _err("search_all", input_data, str(e))


def cmd_search_combined(keyword: str) -> dict[str, Any]:
    input_data = {"keyword": keyword}
    try:
        data = run_combined_search(keyword)
        return _ok("search_combined", input_data, data)
    except Exception as e:  # noqa: BLE001
        return _err("search_combined", input_data, str(e))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="MCP-friendly adapter for job crawler")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("list_sources", help="List available crawler sources")

    p_source = sub.add_parser("search_source", help="Search one source by code")
    p_source.add_argument("--code", required=True)
    p_source.add_argument("--keyword", default=None)
    p_source.add_argument("--job-category", default=None)

    p_all = sub.add_parser("search_all", help="Search all sources (grouped output)")
    p_all.add_argument("--keyword", default=None)

    p_combined = sub.add_parser("search_combined", help="Search all sources (single merged output)")
    p_combined.add_argument("--keyword", required=True)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "list_sources":
        out = cmd_list_sources()
    elif args.command == "search_source":
        out = cmd_search_source(args.code, args.keyword, args.job_category)
    elif args.command == "search_all":
        out = cmd_search_all(args.keyword)
    else:  # search_combined
        out = cmd_search_combined(args.keyword)

    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

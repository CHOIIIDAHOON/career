#!/usr/bin/env python3
import json
import subprocess
import re
from pathlib import Path
from shutil import which
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR / "job-search-mcp-main"
CLI_JS = PROJECT_DIR / "dist" / "cli.js"


def _ensure_built() -> None:
    if CLI_JS.exists():
        return
    if which("pnpm"):
        subprocess.run(["pnpm", "install"], cwd=str(PROJECT_DIR), check=True)
        subprocess.run(["pnpm", "build"], cwd=str(PROJECT_DIR), check=True)
        return
    subprocess.run(["npm", "install"], cwd=str(PROJECT_DIR), check=True)
    subprocess.run(["npm", "run", "build"], cwd=str(PROJECT_DIR), check=True)


def _run_job_portal(query: str, search_type: str, job_category: str = ""):
    _ensure_built()

    cmd = [
        "node",
        str(CLI_JS),
        query,
        "--platform",
        "all",
        "--page",
        "1",
        "--search-type",
        search_type,
    ]
    if job_category.strip():
        cmd.extend(["--job-category", job_category.strip()])
    proc = subprocess.run(cmd, cwd=str(PROJECT_DIR), check=True, capture_output=True, text=True)
    data = json.loads(proc.stdout)

    rows = []
    now_year = datetime.now().year

    def normalize_deadline(raw: str) -> str:
        s = (raw or "").strip()
        if not s:
            return ""

        # 2026. 5. 22. -> 2026.05.22
        m_full = re.search(r"(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.", s)
        if m_full:
            y, mm, dd = m_full.groups()
            return f"{int(y):04d}.{int(mm):02d}.{int(dd):02d}"

        # ~ 05/22(금) -> 2026.05.22 (current year)
        m_md = re.search(r"(\d{1,2})/(\d{1,2})", s)
        if m_md:
            mm, dd = m_md.groups()
            return f"{now_year:04d}.{int(mm):02d}.{int(dd):02d}"

        # Keep values like "채용시", "상시채용" as-is
        return s

    for job in data.get("jobs", []):
        rows.append(
            {
                "제목": job.get("title", ""),
                "링크": job.get("url", ""),
                "일자": normalize_deadline(job.get("deadline", "")),
                "직무분류": job.get("jobCategory", ""),
                "플랫폼": job.get("platform", ""),
                "회사": job.get("companyName", ""),
            }
        )
    return rows


def _dedupe_rows(rows: list[dict]) -> list[dict]:
    seen = set()
    deduped = []
    for row in rows:
        key = row.get("링크") or (
            row.get("플랫폼", ""),
            row.get("회사", ""),
            row.get("제목", ""),
            row.get("일자", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def crawl_job_portals(company_name: str = "GC메디아이", job_category: str = ""):
    return _dedupe_rows(_run_job_portal(company_name, "company", job_category))


def crawl_job_portals_by_role(role_keyword: str = "emr", job_category: str = ""):
    return _dedupe_rows(_run_job_portal(role_keyword, "job", job_category))

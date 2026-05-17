# MCP_TOOLS.md

## 목표
AI 에이전트가 이 저장소를 **툴처럼 호출**할 수 있도록 기능을 명확히 분리한 인터페이스를 제공한다.

핵심 엔트리는 `mcp_adapter.py` 이다.

---

## 1) 기본 실행
프로젝트 루트에서 실행:

```bash
python3 mcp_adapter.py <command> [options]
```

---

## 2) 명령(툴) 목록

### `list_sources`
사용 가능한 소스 코드 목록을 반환.

```bash
python3 mcp_adapter.py list_sources
```

### `search_source`
단일 소스를 조회.

```bash
python3 mcp_adapter.py search_source --code <code> [--keyword <kw>] [--job-category <category>]
```

예:
```bash
python3 mcp_adapter.py search_source --code job_portal --keyword "GC메디아이"
python3 mcp_adapter.py search_source --code job_portal_role --keyword "emr" --job-category "IT"
python3 mcp_adapter.py search_source --code dkuh --keyword "전산"
```

### `search_all`
모든 소스를 조회하고 소스별로 묶어서 반환 (`main.py --code all`과 동일).

```bash
python3 mcp_adapter.py search_all [--keyword <kw>]
```

### `search_combined`
모든 소스를 조회하고 단일 배열로 병합 반환 (`main.py --code combined`과 동일).

```bash
python3 mcp_adapter.py search_combined --keyword <kw>
```

예:
```bash
python3 mcp_adapter.py search_combined --keyword "LG"
python3 mcp_adapter.py search_combined --keyword "emr"
```

---

## 3) JSON 응답 표준
모든 명령은 동일한 envelope를 반환:

```json
{
  "ok": true,
  "tool": "search_source",
  "input": {"code": "job_portal", "keyword": "GC메디아이", "job_category": null},
  "data": {"기관": "...", "검색어": "...", "결과": []},
  "error": null
}
```

실패 시:

```json
{
  "ok": false,
  "tool": "search_source",
  "input": {...},
  "data": null,
  "error": "error message"
}
```

---

## 4) 설정 가능한 항목

### A. 기술직무 키워드(Combined 필터)
`search_combined`는 키워드 포함 + 기술직무 제목 조건을 적용한다.
기본 키워드:
- 전산, 개발, it, emr, 백앤드, 프론트앤드, 백엔드, 프론트엔드

환경변수로 오버라이드 가능:

```bash
export TECH_TITLE_TERMS="전산,개발,it,emr,백엔드,프론트엔드"
python3 mcp_adapter.py search_combined --keyword "삼성"
```

### B. `job_category` 필터
`--job-category`는 `job_portal`, `job_portal_role`에서만 의미가 있다.
`직무분류` 문자열 포함 기준으로 필터링한다.

---

## 5) 소스 코드 리스트
`list_sources` 기준 코드:
- `medios`
- `hallym_ilsong`
- `kbsmc`
- `nhimc`
- `dkuh`
- `ssmc`
- `job_portal` (회사명 중심)
- `job_portal_role` (직무/키워드 중심)

---

## 6) AI 통합 가이드
AI가 툴 호출할 때 권장 순서:

1. `list_sources`로 지원 코드 확인
2. 사용자 요청이 특정 기관이면 `search_source`
3. 사용자 요청이 전체면 `search_all` 또는 `search_combined`
4. 직무 필터 요청이 있으면 `--job-category` 사용
5. `ok=false`면 `error`를 그대로 전달

---

## 7) Linux/경로 가변성
- 절대경로 하드코딩 금지
- 항상 프로젝트 루트에서 실행

```bash
cd /path/to/project
python3 mcp_adapter.py list_sources
```

---

## 8) 빠른 테스트

```bash
python3 mcp_adapter.py list_sources
python3 mcp_adapter.py search_source --code job_portal --keyword "GC메디아이"
python3 mcp_adapter.py search_source --code job_portal_role --keyword "emr" --job-category "IT"
python3 mcp_adapter.py search_combined --keyword "LG"
```

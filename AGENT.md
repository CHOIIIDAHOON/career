# AGENT.md

## 목적
여러 공기업/의료기관 채용 사이트를 동일한 인터페이스로 크롤링한다.
출력 형식은 JSON이며 각 공고 항목은 아래 키를 사용한다.
- 제목
- 링크
- 일자

## 실행 방법
`main.py`에서 통합 실행한다.

### 1) 전체 조회
```bash
python3 main.py --code all
python3 main.py --code combined --keyword "GC메디아이"
```

### 2) 특정 기관만 조회
```bash
python3 main.py --code medios
python3 main.py --code hallym_ilsong
python3 main.py --code kbsmc
python3 main.py --code nhimc
python3 main.py --code dkuh
python3 main.py --code ssmc
python3 main.py --code job_portal
```

### 3) 검색어 강제 지정
전체 또는 특정 기관에 동일 검색어를 강제로 넣고 싶을 때 사용.
```bash
python3 main.py --code all --keyword 전산
python3 main.py --code kbsmc --keyword "전산|IT"
python3 main.py --code job_portal --keyword "GC메디아이"
```

## 현재 등록된 크롤러 코드
- `medios`: 전국지방의료원연합회
- `hallym_ilsong`: 일송학원(한림대학교의료원)
- `kbsmc`: 강북삼성병원
- `nhimc`: 국민건강보험공단 일산병원
- `dkuh`: 단국대학교병원
- `ssmc`: 삼성서울병원
- `job_portal`: 잡코리아+사람인(공통 회사명 검색)
- `combined`: 모든 소스를 같은 키워드로 조회 후 단일 배열로 병합

## 새 기관 추가 규칙
1. `crawl_<기관>.py` 파일 생성
2. 함수 시그니처는 아래를 따른다.
```python
def crawl_xxx(keyword: str = "기본키워드"):
    return [
        {"제목": "...", "링크": "...", "일자": "YYYY-MM-DD"}
    ]
```
3. `main.py`의 `CRAWLER_LIST`에 항목 추가
```python
{
    "code": "기관코드",
    "name": "기관명",
    "runner": crawl_xxx,
    "default_keyword": "전산",
}
```

## 주의 사항
- 사이트 차단(403) 회피를 위해 User-Agent 헤더를 사용한다.
- 외부 라이브러리 없는 표준 라이브러리 우선 구현을 유지한다.
- 날짜 형식은 가능하면 `YYYY-MM-DD`로 맞춘다.

# W-002 · 디지털포용법 후속 데이터 분석

- 상태: 완료
- 최근 갱신: 2026-10-03
- 관련 문서: [docs/README.md](../README.md), [docs/digital-inclusion-analysis.md](../digital-inclusion-analysis.md), [docs/10-digital-inclusion-api-guide.md](../10-digital-inclusion-api-guide.md), [analyses/digital-inclusion/plan.json](../../analyses/digital-inclusion/plan.json)

## 현재 상황

조달청·행안부 키의 실제 인증과 가능한 추가 분석을 완료했다. 행안부 고유 기록 5,803건과 조달청 등록 397행·납품요구 상세 1,494행을 수집·검증하고, 현재 기능 현황과 동일 기간 조달 순증을 분석했다. 결과는 [docs/digital-inclusion-analysis.md](../digital-inclusion-analysis.md)에 있다. KOSIS와 추가 이력 확보는 [docs/work/W-003-main-additional-data.md](W-003-main-additional-data.md)에서 이어간다.

- 완료 조건: 인증 데이터의 실제 범위·필드·시점·품질을 확인하고 재현 가능한 수집·분석 결과와 해석 한계를 기록한다. 인과효과 추정은 필요한 조건이 충족되는 경우에만 진행한다.
- 사람이 판단할 사항: 이번 두 API 분석 범위에는 없음. KOSIS 키·추가 이력 확보는 후속 작업이다.

## 진행과 판단

### 배경과 범위

이 문서는 기존 초기 분석을 이어갈 다음 작업이다. 문서 구조 적용 시점에 코드와 보고서의 현재 상태를 정리했으며, 과거 작업의 상세 실행 로그를 새로 작성한 것은 아니다.

### 중요한 시도와 결정

- 2026-10-03 — 두 키가 URL 인코딩된 형태로 입력돼 있어, 공통 수집기에서 한 번 디코딩한 뒤 요청 인코딩을 적용한다. 사용자 `.env`는 수정하지 않는다. 키·인증 URL·응답 내 인증정보를 출력하거나 산출물에 저장하지 않는다. Context7에 해당 API 문서가 없어 공식 공공데이터포털 명세를 재확인했다.
- 2026-10-03 — 행안부 일반 페이지 수집에서 35개 반복행을 발견했다. [analyses/digital-inclusion/mois_collect.py](../../analyses/digital-inclusion/mois_collect.py)에 기관·시각 분할 조회를 추가해 231개 최종 구간 합계·고유키·무필터 총건수 5,803을 일치시켰다. 부분 수집을 중복 제거만으로 완전하다고 처리하지 않았다.
- 2026-10-03 — [analyses/digital-inclusion/mois_analyze.py](../../analyses/digital-inclusion/mois_analyze.py)는 사용 기재 5,800건을 분모로 기능별 제공·미제공·미상을 집계한다. 지역 표시명은 원주소 첫 토큰에서 얻고 공식 코드표 검증과 구분했다. 휠체어 조작 불가능 표시는 562건이며 실제 작동·법적 적합성 판정으로 해석하지 않는다.
- 2026-10-03 — [analyses/digital-inclusion/pps_collect.py](../../analyses/digital-inclusion/pps_collect.py)에서 월별 완결 조회를 하고 [analyses/digital-inclusion/pps_analyze.py](../../analyses/digital-inclusion/pps_analyze.py)로 변경·취소의 부호를 보존한 납품요구 순증을 계산했다. 주 분석은 증명발급기·무인안내시스템으로 제한했다. 2~9월 872→597대(-31.5%), 법정일과 같은 1/22~9/30 930→716대(-23.0%)를 함께 표시했다.
- 2026-10-03 — 초기 분석은 [analyses/digital-inclusion/analyze.py](../../analyses/digital-inclusion/analyze.py)에서 실제 초기 입력만 해시로 기록하도록 범위를 좁혔다. 후속 API 파일이 기존 기준선 입력 목록에 섞이지 않으며 숫자는 유지됐다.
- 2026-10-03 — API 데이터로 현재 상태와 조달 흐름은 확인했지만 설치·기능 변경 이력, 시행 당시 기업규모와 미등록 제조사 모집단은 확보하지 못했다. 인과효과 추정은 진행하지 않고 필요한 자료를 후속 작업으로 남겼다.
- 2026-10-02 — [docs/digital-inclusion-analysis.md](../digital-inclusion-analysis.md)와 [analyses/digital-inclusion/analyze.py](../../analyses/digital-inclusion/analyze.py)에서 초기 분석의 입력·계산·한계를 확인했다. 2025년 조사치는 시행 전 기준선이며 검증 목록은 신규 재수집이 아닌 과거 집계다.
- 2026-10-02 — [docs/10-digital-inclusion-api-guide.md](../10-digital-inclusion-api-guide.md)에 조달청·행안부·KOSIS를 우선 확인할 API로 정리한 상태다. NIA 위치 API의 인증 방식·실제 시점 필드는 미확인으로 유지한다.
- 2026-10-02 — 행안부 공개 명세에는 접근성 기능 8종이 있으나 설치일은 없다. 인증 첫 수집은 현재 상태 점검으로 시작하고, 시행 전후 분석은 과거 스냅샷·변경 이력 여부를 따로 확인한다.
- 2026-10-02 — 사용자가 키 저장 위치와 특정 API를 식별할 수 있는 이름을 요청했다. 저장소 루트 `.env`를 입력 위치로 정하고 [.env.example](../../.env.example)에 `PPS_SHOPPING_MALL_SERVICE_KEY`·`MOIS_KIOSK_INFO_SERVICE_KEY`·`KOSIS_DIGITAL_DIVIDE_API_KEY`를 분리했다. [docs/specs.md](../specs.md)와 API 안내·카탈로그를 같은 이름으로 맞춘다. 키 발급 여부나 인증 성공은 이번 변경으로 확인되지 않는다.
- 2026-10-02 — 기존 `.env`가 없음을 확인해 세 항목이 빈 로컬 파일을 생성했다. 실제 키 값은 입력·조회하지 않았다. API 수집기에서 사용할 이름은 확정했고, 로딩 구현은 후속 작업에 남긴다.

### 검증

- 기존 분석의 검증 근거 — [analyses/digital-inclusion/README.md](../../analyses/digital-inclusion/README.md)에 출력 재현과 공식 원문 해시 확인 기록이 있다.
- 인증 후 실데이터 수집·검증 — 통과. 행안부 `resultCode=0`, 조달청 `00`과 실제 데이터 수신을 확인했다. 값 없는 근거는 [analyses/digital-inclusion/data/authentication_check_2026-10-03.json](../../analyses/digital-inclusion/data/authentication_check_2026-10-03.json)에 있다.
- 키 설정 양식·문서·API 카탈로그의 세 이름 일치와 기존 공통 이름 제거 — 통과. `.env`가 Git에서 제외되는 것도 확인했다.
- `python3 analyses/digital-inclusion/analyze.py` — 통과, Python 3.14.2. 분석 수치는 동일하며 `summary.json`의 API 카탈로그 입력 해시만 변경됐다. `git diff --check`와 수정 문서의 상대경로 확인도 통과했다.
- 2026-10-03 원자료 독립 검토 — 통과. 행안부 분할 원본 232개와 조달청 등록 21요청·납품 26요청의 해시·페이지·조건·CSV 내용, 전국·지역·기간별 수치를 대조했다.
- `python3 -m unittest discover -s analyses/digital-inclusion/tests -v` — 6개 통과. 가짜 키로 Encoding 키의 `+` 보존, 오류 시 URL·키 비노출, 응답의 키 반사 차단 등을 검증했다.
- `python3 analyses/digital-inclusion/pps_analyze.py --self-test` — 변경·취소·옵션·결측 처리 통과.
- 두 API 오프라인 분석 재실행 — 통과. 기존 결과 파일의 SHA256이 모두 동일하다. 초기 분석도 입력 해시 범위 외 수치가 유지됐다.
- 산출물·소스·로컬 원응답 텍스트 468개에서 실제 두 키와 인코딩 변형을 검사 — 노출 없음. `.env`·`raw/` Git 제외와 `git diff --check`도 통과.

### 세션 메모

- 2026-10-02 · Codex — 문서 구조 적용 시점에 후속 작업을 등록했다. 재개 시 첫 행동은 키·서비스별 승인 상태를 확인하고 실제 응답을 검증할 수집기를 작성하는 것이다.
- 2026-10-02 · Codex — 기관·서비스별 키 이름과 입력 위치를 정리하고 빈 `.env`를 준비했다. 보류 상태는 유지하며, 다음 행동은 사용자가 값을 입력한 뒤 서비스별 승인과 실제 응답을 확인하는 것이다.
- 2026-10-03 · Codex — 인증·수집·분석 후 중단된 작업을 저장된 원본으로 재개했다. 추가 API 호출 없이 지역 집계·기간 민감도·보고서·실행 문서와 최종 검증을 마무리했다. 다음 행동은 후속 자료 작업의 준비 조건 확인이다.

## 남은 일

- [x] 초기 분석·출처·계산 코드와 API 안내를 연결한다.
- [x] 키 입력 위치와 기관·서비스별 환경변수 이름을 정하고 양식을 준비한다.
- [x] 두 API의 실제 인증과 데이터 수신을 확인한다. 실제 키 값은 문서에 적지 않는다.
- [x] 인증 수집기를 구현하고 응답의 오류·페이지·필드·고유키·결측값을 검증한다.
- [x] 과거 기간 조회·갱신·기업구분의 실제 범위를 점검하고 미확인 이력을 기록한다.
- [x] 수집일·조회조건·원본 해시를 보존하고 분석 가능한 관측 단위를 확정한다.
- [x] 현재 상태와 조달 흐름 분석을 진행하고 판단 근거·미확인 사항을 보고서에 반영한다.
- [x] 결과에 맞춰 공통 문서·작업 목록을 갱신한다.

재개에 필요한 코드 상태: 작성 당시 브랜치 `main`, HEAD `c29288ed8116fc374559f24143e7fc72031718b0`. 초기 분석과 문서 적용 변경은 미커밋 상태다. 재개 시 현재 코드·변경 상태를 먼저 대조한다.

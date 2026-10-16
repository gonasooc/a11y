# 기술 명세

> 초기 작성: 2026-10-02 · 인증 수집·검증 반영: 2026-10-03 · 웹 사이트 추가: 2026-10-06 · 영상 접근성 자료 보강: 2026-10-17.

기술 구성, 구현·검증 규칙과 실행 방법을 다룬다. 폴더 책임과 의존 관계는 [docs/architecture.md](architecture.md)에 있다.

## 기술 구성

| 항목 | 확인한 내용 | 근거와 미정 사항 |
|---|---|---|
| 분석 언어 | Python, 표준 라이브러리 사용 | 초기 기준선과 MOIS·PPS·KOSIS 수집/분석 코드 |
| Python 버전 | 이번 환경에서 Python 3.14.2 확인. 장애인방송 분석은 2026-10-13 macOS 기본 Python 3.9.6에서 확인. 2026-10-17 영상 접근성 보강분(KOSIS 등록 통계, 2012~2016 실적)은 3.9.6과 3.11.5에서 확인 | 기존 [analyses/digital-inclusion/README.md](../analyses/digital-inclusion/README.md)는 3.10 이상을 안내한다. 버전 고정 설정·지원 버전별 검증 정책은 미정 |
| 입력·출력 형식 | UTF-8 CSV·JSON, 문서는 Markdown | 코드의 읽기·쓰기와 입력 파일 |
| 계산 | Decimal 차이 계산, 구성비는 소수점 첫째 자리 ROUND_HALF_UP | [analyses/digital-inclusion/analyze.py](../analyses/digital-inclusion/analyze.py)의 `rounded` |
| 의존성 관리 | 현재 분석에는 외부 패키지가 필요 없다 | 패키지·잠금·Python 프로젝트 설정 파일은 현재 저장소에서 확인되지 않는다 |
| 웹 사이트 | 빌드 도구 없는 정적 HTML·CSS·JavaScript. 브라우저 스크립트는 모듈이 아닌 일반 스크립트라 파일로 열어도 동작한다 | [site/README.md](../site/README.md). 근거: [docs/work/W-006-main-pages-site.md](work/W-006-main-pages-site.md) |
| 웹 의존성 | 설치할 패키지가 없다. 글꼴은 Pretendard(jsDelivr CDN, OFL), 눈금 계산은 d3-array 3.2.4에서 옮긴 함수(ISC) | 차트 라이브러리는 쓰지 않고 [site/assets/js/chart/](../site/assets/js/chart/)에 직접 구현했다 |
| 보고서 데이터 생성 | Node 20 이상, 외부 패키지 없음 | [site/scripts/generate.mjs](../site/scripts/generate.mjs) |
| API 인증·HTTP | 표준 라이브러리 urllib, 환경변수 또는 `.env` | [analyses/digital-inclusion/api_common.py](../analyses/digital-inclusion/api_common.py). 영상 접근성의 KOSIS·열린재정 수집기도 이 모듈을 쓴다 |
| 배포·CI | GitHub Actions가 생성 구역 검사 후 `site/`를 그대로 GitHub Pages에 올린다. PR에서는 검사만 한다 | [.github/workflows/pages.yml](../.github/workflows/pages.yml). 데이터베이스·웹 인증은 미정 |

## 지켜야 할 구현 규칙

현재 분석 코드에서 확인한 검증 동작은 다음과 같다. 향후 분석에 확장할 규칙은 해당 작업에서 결정한다.

- 중복 관측, 잘못된 시점, 음수·비정상 값, 목록 합계 불일치 등을 발견하면 오류로 중단한다.
- 출처 URL·원문 위치·검증 상태를 입력에 기록한다. 현재 요약에는 입력 파일 SHA256을 포함한다.
- 인접한 조사연도만 1년 차이로 계산하며, 시행 전 통계에 시행 후 관측을 섞지 않는다.
- 기술통계와 인과효과를 구분하고, 자료 부족을 0값으로 대체하지 않는다. 분석별 판정 조건은 [analyses/digital-inclusion/plan.json](../analyses/digital-inclusion/plan.json)에 있다.
- 현재 분석 코드는 사전 등록 여부와 원자료 재수집 상태를 확인한다. 새 원자료나 새로운 추정 방법을 적용할 때는 계획과 코드 조건을 함께 검토한다.
- 인증 수집기는 키가 들어간 URL·오류 메시지를 출력하지 않는다. 인증키는 허용된 공식 HTTPS 호스트에만 전송하고 예상치 못한 리다이렉트는 중단한다.
- 현재 행안부 분석은 고유키 수·수신 행수·API 총건수 일치를 강제한다. 조달청 분석은 변경·취소의 부호와 품목 단위를 보존한다. 세부 기준은 [docs/digital-inclusion/analysis.md](digital-inclusion/analysis.md)에 있다.
- KOSIS는 메타데이터의 수록연도·항목·분류 조합과 실제 셀을 대조한다. `PRD_SE=Y`로 요청한 연간 자료가 응답에서 `A`로 표기되는 것을 확인했고 원값을 보존한다. `jsonVD=Y`로 정상 JSON을 요청한다.
- 웹 보고서의 표·차트 데이터는 생성 스크립트가 분석 출력에서 계산해 HTML의 생성 구역에 넣는다. 본문 숫자는 `data-check`로 그 값과 대조하고, 다르면 스크립트가 실패한다. 수집 원자료(`raw/`)는 읽지 않는다. 조사 문서([docs/digital-inclusion/environment.md](digital-inclusion/environment.md)·[docs/digital-inclusion/law.md](digital-inclusion/law.md))에서 가져온 숫자는 `analyses/digital-inclusion/data/context_facts_2026-09-29.csv`에 출처·위치·등급과 함께 두고, 생성 스크립트가 A·B 등급만 받아 같은 방식으로 대조한다. 다른 등급이 있으면 생성이 실패한다. 방법은 [site/README.md](../site/README.md)에 있다.
- 웹 페이지 사이 링크와 자산은 상대경로로 쓰고, 페이지 링크는 `index.html`까지 적는다. 파일로 열어도 이동하고 `/<저장소>/` 하위 경로에서도 맞는다.
- 웹에서 자료를 받기 전에 robots.txt와 이용약관을 확인한다. 약관이 자동 수집을 금지하면 robots.txt가 허용해도 수집하지 않는다. 근거: [docs/work/W-009-main-media-access.md](work/W-009-main-media-access.md)(티빙 약관 확인).
- 공식 보도자료의 집계와 원자료 계산이 다르면 오류로 멈추지 않고 양쪽 값과 대조 결과를 남긴다. 원자료 자체의 합계·행 수가 어긋나면 멈춘다. 예: [analyses/media-access/outputs/broadcast_official_check.csv](../analyses/media-access/outputs/broadcast_official_check.csv).
- 공표 구조 때문에 원자료 합계가 맞지 않는 경우는 그 구조일 때만 차이를 따로 남기고, 그 밖의 불일치는 멈춘다. 예: KOSIS 연령별 등록장애인 표는 2007~2014년에 100세 이상 구간과 '해당없음'을 공표하지 않아 구간 합이 합계보다 작다. 근거: [docs/work/W-011-main-media-access-supplement.md](work/W-011-main-media-access-supplement.md).
- KOSIS와 보고서가 다르면 원문을 재확인하고 양쪽 값을 남긴다. 2016년 지표·고령층 기준 변경 이전 자료는 장기 주 비교에서 분리한다. 기준은 [analyses/digital-inclusion/kosis_analysis_plan.json](../analyses/digital-inclusion/kosis_analysis_plan.json)에 있다.

문서 작성·갱신은 [AGENTS.md](../AGENTS.md)를 따른다. Context7에 관한 기존 지침도 보존돼 있다.

## 실행과 검증

| 목적 | 명령 또는 확인 방법 | 필요한 조건 |
|---|---|---|
| 준비 | `python3 --version` | Python 설치. 현재 분석에 별도 패키지나 API 키는 필요 없다 |
| 분석 실행 | `python3 analyses/digital-inclusion/analyze.py` | 저장소 루트에서 실행. 입력 데이터와 `plan.json` 필요 |
| 행안부 분석 | `python3 analyses/digital-inclusion/mois_analyze.py --snapshot 2026-10-03` | CSV·수집 명세·지역 표시명 파일. 키 불필요 |
| 조달청 분석 | `python3 analyses/digital-inclusion/pps_analyze.py` | 등록·납품요구 CSV와 수집 명세. 키 불필요 |
| 기관·제품별 후속 분석 | `python3 analyses/digital-inclusion/followup_analyze.py` | 기존 조달 CSV·명세와 2026-10-03 행안부 자료. 키 불필요 |
| KOSIS 분석 | `python3 analyses/digital-inclusion/kosis_analyze.py --snapshot 2026-10-03` | CSV·메타데이터·수집 명세·기존 보고서 기준선. 키 불필요 |
| 계산 결과 재현 | 실행 전후 `outputs/` 3개 파일의 SHA256 비교 | 같은 입력·코드로 재실행하고 해시가 동일한지 확인 |
| 문서 검증 | 상대경로 링크 대상 존재 확인, `git diff --check` | 문서 변경 시 수행. 코드블록의 예시와 실제 링크를 구분 |
| 인증 처리 테스트 | `python3 -m unittest discover -s analyses/digital-inclusion/tests -v` | 가짜 키·모의 응답만 사용, 네트워크 불필요 |
| 장애인방송 실적 분석 | `python3 analyses/media-access/broadcast_analyze.py` | 저장된 CSV만 읽는다. 키·네트워크 불필요 |
| 장애인방송 원본 수집·해석 | `python3 analyses/media-access/kcmf_collect.py --snapshot YYYY-MM-DD` 다음 `python3 analyses/media-access/kcmf_parse.py` | `kcmf.or.kr` 접속 필요, 키 불필요. 원본은 `raw/`에 두고 Git 제외 |
| 등록 장애인 통계 분석 | `python3 analyses/media-access/registry_analyze.py --snapshot 2026-10-17` | 저장된 CSV·수집 명세만 읽는다. 키·네트워크 불필요 |
| 등록 장애인 통계 수집 | `python3 analyses/media-access/kosis_registry_collect.py --snapshot YYYY-MM-DD` | `KOSIS_DISABILITY_API_KEY`·네트워크 필요. 원응답은 `raw/`에 두고 Git 제외 |
| 2012~2016 장애인방송 실적 분석 | `python3 analyses/media-access/broadcast_early_analyze.py` | 저장된 CSV만 읽는다. 키·네트워크 불필요. 2017~2025 출력과 따로 둔다 |
| 2012~2016 원본 수집·해석 | `python3 analyses/media-access/kmcc_collect.py --snapshot YYYY-MM-DD` 다음 `python3 analyses/media-access/kmcc_parse.py` | `www.kmcc.go.kr` 접속 필요(게시물을 먼저 열어 세션을 받는다), 키 불필요. 원본 HWP는 `raw/`에 두고 Git 제외 |
| 열린재정 세부사업 예산 조회 | `python3 analyses/media-access/openfiscal_collect.py --snapshot YYYY-MM-DD` | `OPENFISCAL_BUDGET_API_KEY`·네트워크 필요. 원응답은 `raw/`에 두고 Git 제외 |
| 영상 접근성 테스트 | `python3 -m unittest discover -s analyses/media-access/tests -v` | 합성 HWPX, 손으로 만든 HWP 레코드, 합성 KOSIS·열린재정 응답으로 해석·판정을 확인(28개). 키·네트워크 불필요 |
| 조달 계산 경계 검증 | `python3 analyses/digital-inclusion/pps_analyze.py --self-test` | 변경·취소·단위·결측 처리, 네트워크 불필요 |
| KOSIS 수집 경계 검증 | `python3 analyses/digital-inclusion/kosis_collect.py --self-test` | 기호·0·누락·중복·연간 주기 검증, 키·네트워크 불필요 |
| 정적 검사 | `git diff --check` | 린터는 미정 |
| 사이트 보기 | `site/index.html`을 브라우저로 연다. 또는 `python3 -m http.server 8000 -d site` | 빌드·설치가 필요 없다. 글꼴은 인터넷 연결 시 적용된다 |
| 보고서 생성 구역 갱신 | `node site/scripts/generate.mjs` | 분석 출력이 바뀌었을 때 실행한다. 본문 숫자·출력 사이 합계가 다르면 실패한다 |
| 생성 구역 최신 여부 검사 | `node site/scripts/generate.mjs --check` | 파일을 바꾸지 않는다. CI가 쓴다 |
| 웹 접근성 확인 | axe-core, 키보드 탐색, 320px 화면, 운영체제 어두운 모드에서도 밝은 화면 유지 | 기준은 [docs/design.md](design.md). CI 자동 검사는 없다 |
| 웹 배포 | `main`에 `site/`·`analyses/` 변경이 반영되면 GitHub Actions가 검사 후 배포 | 저장소 Pages의 Source는 GitHub Actions로 설정돼 있다(2026-10-06). 공개 주소는 `https://gonasooc.github.io/a11y/` |
| 인증 API 수집 | 서비스별 실행 명령은 [analyses/digital-inclusion/README.md](../analyses/digital-inclusion/README.md) 참고 | 서비스별 키·승인·네트워크 필요. 저장된 자료 재분석에는 수집 불필요 |

개별 작업에서 실행한 환경·명령·통과 범위는 작업 문서에 기록한다. 이번 문서 적용에서 수행한 검증은 [docs/work/W-001-main-docs-starter.md](work/W-001-main-docs-starter.md)에 있다.

### 환경 변수

[.env.example](../.env.example)에 아래 이름이 있다. [.gitignore](../.gitignore)는 실제 `.env` 파일을 제외한다. **수집기는 프로세스 환경변수를 우선 사용하고 없으면 `.env`를 읽으며, 오프라인 분석은 키를 읽지 않는다.** 공공데이터포털 키는 Encoding·Decoding 형태를 모두 처리한다.

| 이름 | 용도 |
|---|---|
| `PPS_SHOPPING_MALL_SERVICE_KEY` | 조달청 나라장터쇼핑몰 품목정보 서비스(15129471)의 Decoding 인증키 |
| `MOIS_KIOSK_INFO_SERVICE_KEY` | 행안부 무인민원발급기정보 조회서비스(15154774)의 Decoding 인증키 |
| `KOSIS_DIGITAL_DIVIDE_API_KEY` | KOSIS 디지털정보격차 통계표·메타데이터 조회용 공유서비스 인증키 |
| `KOSIS_DISABILITY_API_KEY` | KOSIS 보건복지부 「장애인현황」(등록장애인) 통계표 조회용 공유서비스 인증키. KOSIS 키는 사용자 단위라 `KOSIS_DIGITAL_DIVIDE_API_KEY`와 같은 값을 넣는다 |
| `OPENFISCAL_BUDGET_API_KEY` | 열린재정 Open API(세부사업 예산 `TotalExpenditure5` 등) 인증키. 공공데이터포털이 아니라 열린재정에서 본인인증 후 발급한다 |

입력 위치는 저장소 루트 `.env`다. 서비스별로 이름을 나누며, 두 공공데이터포털 서비스에서 같은 키를 사용한다면 각 변수에 같은 값을 넣는다. 명명 결정은 [docs/work/W-002-main-digital-inclusion-api.md](work/W-002-main-digital-inclusion-api.md)에 기록한다. `KOSIS_DISABILITY_API_KEY`는 같은 규칙으로 2026-10-17에 더했다([docs/work/W-011-main-media-access-supplement.md](work/W-011-main-media-access-supplement.md)).

실제 비밀값은 문서에 기록하지 않는다. NIA 위치 API는 인증 방식을 확정한 뒤 설정을 결정한다. API 명세·발급 안내는 [docs/digital-inclusion/analysis.md](digital-inclusion/analysis.md#부록-b-디지털포용법-분석에-필요한-api)에 있다.

공통 HTTP 처리의 인증 매개변수는 공공데이터포털 `serviceKey`, KOSIS `apiKey`, 열린재정 `Key`다. KOSIS 키는 공식 `kosis.kr/openapi/` 경로로만 전송한다.

## 알려진 기술 제약

- 현재 스크립트의 분석일·기준연도와 검증 조건은 초기 분석 자료에 맞춰져 있다. 새로운 조사연도·등록 이력을 넣으면 기존 조건을 먼저 검토해야 한다.
- CSV만으로 숫자 계산을 재현할 수 있으나, 원문 추출·전사는 자동화되지 않았다. 원문 확인과 코드 재현은 검증 범위가 다르다.
- Python 3.14.2에서 실행을 확인했다. 다른 OS·Python 버전의 실제 동작은 미확인이다.
- 생성 스크립트 검사는 macOS·Node 20.19.0과 GitHub Actions(ubuntu-24.04·Node 24.21.0)에서 통과했다(2026-10-06). 그 밖의 OS·Node 버전은 미확인이다.
- `raw/` 원본·`.env`·가상환경 등은 Git에서 제외한다. 분석 출력은 현재 저장소 파일로 관리하며, 향후 대용량 데이터 보관 방식은 미정이다.

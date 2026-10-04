# 기술 명세

> 초기 작성: 2026-10-02 · 인증 수집·검증 반영: 2026-10-03. 웹 기술 스택은 미정이다.

기술 구성, 구현·검증 규칙과 실행 방법을 다룬다. 폴더 책임과 의존 관계는 [docs/architecture.md](architecture.md)에 있다.

## 기술 구성

| 항목 | 확인한 내용 | 근거와 미정 사항 |
|---|---|---|
| 분석 언어 | Python, 표준 라이브러리 사용 | 초기 기준선과 MOIS·PPS·KOSIS 수집/분석 코드 |
| Python 버전 | 이번 환경에서 Python 3.14.2 확인 | 기존 [analyses/digital-inclusion/README.md](../analyses/digital-inclusion/README.md)는 3.10 이상을 안내한다. 버전 고정 설정·지원 버전별 검증 정책은 미정 |
| 입력·출력 형식 | UTF-8 CSV·JSON, 문서는 Markdown | 코드의 읽기·쓰기와 입력 파일 |
| 계산 | Decimal 차이 계산, 구성비는 소수점 첫째 자리 ROUND_HALF_UP | [analyses/digital-inclusion/analyze.py](../analyses/digital-inclusion/analyze.py)의 `rounded` |
| 의존성 관리 | 현재 분석에는 외부 패키지가 필요 없다 | 패키지·잠금·Python 프로젝트 설정 파일은 현재 저장소에서 확인되지 않는다 |
| 웹 언어·프레임워크·패키지 관리자 | 미정 | 웹 구현과 관련 설정 파일이 없다 |
| API 인증·HTTP | 표준 라이브러리 urllib, 환경변수 또는 `.env` | [analyses/digital-inclusion/api_common.py](../analyses/digital-inclusion/api_common.py) |
| 데이터베이스·웹 인증·배포·CI | 미정 | 관련 구현·설정 파일이 없다 |

## 지켜야 할 구현 규칙

현재 분석 코드에서 확인한 검증 동작은 다음과 같다. 향후 분석에 확장할 규칙은 해당 작업에서 결정한다.

- 중복 관측, 잘못된 시점, 음수·비정상 값, 목록 합계 불일치 등을 발견하면 오류로 중단한다.
- 출처 URL·원문 위치·검증 상태를 입력에 기록한다. 현재 요약에는 입력 파일 SHA256을 포함한다.
- 인접한 조사연도만 1년 차이로 계산하며, 시행 전 통계에 시행 후 관측을 섞지 않는다.
- 기술통계와 인과효과를 구분하고, 자료 부족을 0값으로 대체하지 않는다. 분석별 판정 조건은 [analyses/digital-inclusion/plan.json](../analyses/digital-inclusion/plan.json)에 있다.
- 현재 분석 코드는 사전 등록 여부와 원자료 재수집 상태를 확인한다. 새 원자료나 새로운 추정 방법을 적용할 때는 계획과 코드 조건을 함께 검토한다.
- 인증 수집기는 키가 들어간 URL·오류 메시지를 출력하지 않는다. 인증키는 허용된 공식 HTTPS 호스트에만 전송하고 예상치 못한 리다이렉트는 중단한다.
- 현재 행안부 분석은 고유키 수·수신 행수·API 총건수 일치를 강제한다. 조달청 분석은 변경·취소의 부호와 품목 단위를 보존한다. 세부 기준은 [docs/digital-inclusion-analysis.md](digital-inclusion-analysis.md)에 있다.
- KOSIS는 메타데이터의 수록연도·항목·분류 조합과 실제 셀을 대조한다. `PRD_SE=Y`로 요청한 연간 자료가 응답에서 `A`로 표기되는 것을 확인했고 원값을 보존한다. `jsonVD=Y`로 정상 JSON을 요청한다.
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
| 조달 계산 경계 검증 | `python3 analyses/digital-inclusion/pps_analyze.py --self-test` | 변경·취소·단위·결측 처리, 네트워크 불필요 |
| KOSIS 수집 경계 검증 | `python3 analyses/digital-inclusion/kosis_collect.py --self-test` | 기호·0·누락·중복·연간 주기 검증, 키·네트워크 불필요 |
| 정적 검사·빌드 | `git diff --check` 외 전용 설정 없음 | 린터·빌드 도구는 미정 |
| 웹 실행·배포 | 미정 | 웹 스택과 배포 방식 결정 필요 |
| 인증 API 수집 | 서비스별 실행 명령은 [analyses/digital-inclusion/README.md](../analyses/digital-inclusion/README.md) 참고 | 서비스별 키·승인·네트워크 필요. 저장된 자료 재분석에는 수집 불필요 |

개별 작업에서 실행한 환경·명령·통과 범위는 작업 문서에 기록한다. 이번 문서 적용에서 수행한 검증은 [docs/work/W-001-main-docs-starter.md](work/W-001-main-docs-starter.md)에 있다.

### 환경 변수

[.env.example](../.env.example)에 아래 이름이 있다. [.gitignore](../.gitignore)는 실제 `.env` 파일을 제외한다. **수집기는 프로세스 환경변수를 우선 사용하고 없으면 `.env`를 읽으며, 오프라인 분석은 키를 읽지 않는다.** 공공데이터포털 키는 Encoding·Decoding 형태를 모두 처리한다.

| 이름 | 용도 |
|---|---|
| `PPS_SHOPPING_MALL_SERVICE_KEY` | 조달청 나라장터쇼핑몰 품목정보 서비스(15129471)의 Decoding 인증키 |
| `MOIS_KIOSK_INFO_SERVICE_KEY` | 행안부 무인민원발급기정보 조회서비스(15154774)의 Decoding 인증키 |
| `KOSIS_DIGITAL_DIVIDE_API_KEY` | KOSIS 디지털정보격차 통계표·메타데이터 조회용 공유서비스 인증키 |

입력 위치는 저장소 루트 `.env`다. 서비스별로 이름을 나누며, 두 공공데이터포털 서비스에서 같은 키를 사용한다면 각 변수에 같은 값을 넣는다. 명명 결정은 [docs/work/W-002-main-digital-inclusion-api.md](work/W-002-main-digital-inclusion-api.md)에 기록한다.

실제 비밀값은 문서에 기록하지 않는다. NIA 위치 API는 인증 방식을 확정한 뒤 설정을 결정한다. API 명세·발급 안내는 [docs/10-digital-inclusion-api-guide.md](10-digital-inclusion-api-guide.md)에 있다.

공통 HTTP 처리의 인증 매개변수는 공공데이터포털 `serviceKey`, KOSIS `apiKey`다. KOSIS 키는 공식 `kosis.kr/openapi/` 경로로만 전송한다.

## 알려진 기술 제약

- 현재 스크립트의 분석일·기준연도와 검증 조건은 초기 분석 자료에 맞춰져 있다. 새로운 조사연도·등록 이력을 넣으면 기존 조건을 먼저 검토해야 한다.
- CSV만으로 숫자 계산을 재현할 수 있으나, 원문 추출·전사는 자동화되지 않았다. 원문 확인과 코드 재현은 검증 범위가 다르다.
- Python 3.14.2에서 실행을 확인했다. 다른 OS·Python 버전의 실제 동작은 미확인이다.
- `raw/` 원본·`.env`·가상환경 등은 Git에서 제외한다. 분석 출력은 현재 저장소 파일로 관리하며, 향후 대용량 데이터 보관 방식은 미정이다.

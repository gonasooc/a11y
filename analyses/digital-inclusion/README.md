# 디지털포용법 분석 재현

**2026-10-02 기준 탐색 분석**이다. [docs/digital-inclusion-analysis.md](../../docs/digital-inclusion-analysis.md)와 [API 안내](../../docs/10-digital-inclusion-api-guide.md)를 함께 읽는다. 법의 인과효과는 현재 자료로 식별하지 못했다.

2026-10-03에는 조달청·행안부 인증 수집과 추가 분석을 수행했다. 결과는 [docs/digital-inclusion-analysis.md](../../docs/digital-inclusion-analysis.md)에 있다. 아래 첫 실행법은 초기 기준선이며, API 분석 명령은 뒤에 별도로 안내한다.

같은 날 KOSIS 네 통계표에서 2014~2025년 240개 관측을 확보했다. 2016년 이후 추세와 기존 보고서 대조 결과는 [docs/digital-inclusion-analysis.md](../../docs/digital-inclusion-analysis.md#digital-baseline)에 있다.

## 실행

Python 3.10 이상이면 외부 패키지나 API 키 없이 실행한다. 저장소 루트에서:

```sh
python3 analyses/digital-inclusion/analyze.py
```

확인한 공식 보고서의 집계값과 기존 문서의 집계값을 읽고 `outputs/` 세 파일을 재생성한다. 외부 사이트에 접속하지 않으며 `.env`를 읽지 않는다. `summary.json`의 입력 SHA256으로 계산에 사용한 파일을 식별한다.

| 파일 | 내용 |
|---|---|
| [plan.json](plan.json) | 탐색적 분석 범위, 기존 데이터 노출, 후속 추정의 조건 |
| [baseline_indicators.csv](data/baseline_indicators.csv) | 이번에 원문 확인한 107개 관측값. 디지털정보화 100행, 웹 평균 7행 |
| [source_manifest_baseline.json](data/source_manifest_baseline.json) | 원본 다운로드 URL·해시·쪽수·모집단·측정 한계 |
| [archived_registry_counts.csv](data/archived_registry_counts.csv) | 기존 05 문서에서 옮긴 14개 집계. 신규 수집 원자료가 아님 |
| [archived_registry_metadata.json](data/archived_registry_metadata.json) | 05 문서의 Git 리비전·관측일, 이번 재수집 실패 기록 |
| [policy_events.csv](data/policy_events.csv) | 시행일, 경쟁 정책, 신청 마감, 계도기간 구분 |
| [api_catalog.json](data/api_catalog.json) | 인증 후 수집할 API의 실제 공개 명세 확인 결과 |
| [summary.json](outputs/summary.json) | 향후 분석 페이지가 사용할 요약·차이·판정·입력 해시 |
| [baseline_changes.csv](outputs/baseline_changes.csv) | 동일 지표·집단의 인접 조사연도 차이. 모두 시행 전 |
| [registry_composition.csv](outputs/registry_composition.csv) | 771개 모델 내 구성비. 나머지 제품분류 170건은 합계에서 계산 |

## 재현 범위와 검증

숫자 계산은 저장된 CSV만으로 재현한다. 공식 PDF·ODT는 `raw/`에 로컬 보존하고 Git에서 제외했다. 다른 환경에서는 출처 명세의 `download_url`에서 내려받아 SHA256을 비교하면 원문을 다시 확인할 수 있다. 추출·전사는 수동이며 새로운 보고서로 자동 갱신하는 파이프라인은 아직 없다.

코드는 중복 관측, 단위, 출처, 시점, 음수, 목록 합계 불일치를 오류로 처리한다. 여러 해가 빠진 자료를 1년 변화로 계산하지 않는다. 현재 목록의 등록번호 연도는 최초 발급 이력으로 가정하지 않는다. 조회 실패와 미상 값은 0으로 채우지 않는다.

이번 실행에서 공식 원본 4개의 해시와 로컬 문서 링크를 확인했다. 중복 관측·시행 후 값을 기준선에 넣은 경우·목록 합계 불일치가 각각 오류로 거부되는 것을 확인했고, 재실행한 출력 3개의 해시도 동일했다.

`plan.json`은 사전 등록이 아니다. 기존 집계를 이미 보았고 현재는 비교 가능성 점검 단계다. 원자료·모집단·시점 조건을 만족하지 않아 이중차분 추정, 신뢰구간, p값, 설치율은 산출하지 않는다.

## 인증 API 분석 재현

저장된 CSV·출처 명세로 계산을 재현하는 명령이다. 네트워크와 키가 필요 없다.

```sh
python3 analyses/digital-inclusion/mois_analyze.py --snapshot 2026-10-03
python3 analyses/digital-inclusion/pps_analyze.py
```

| 입력·출력 | 내용 |
|---|---|
| [analyses/digital-inclusion/data/authentication_check_2026-10-03.json](data/authentication_check_2026-10-03.json) | 실제 값 없는 인증 성공 기록과 근거 |
| [analyses/digital-inclusion/data/mois_devices_2026-10-03.csv](data/mois_devices_2026-10-03.csv) | 행안부 고유 기록 5,803개. 상세 주소와 연락처는 제외 |
| [analyses/digital-inclusion/data/mois_manifest_2026-10-03.json](data/mois_manifest_2026-10-03.json) | 기관·시각 분할 조회, 총건수·고유키 대조, 원문 해시 |
| [analyses/digital-inclusion/data/mois_region_labels_2026-10-03.json](data/mois_region_labels_2026-10-03.json) | 원주소 첫 토큰 기반 표시명. 공식 코드표로 간주하지 않음 |
| [analyses/digital-inclusion/outputs/mois_summary_2026-10-03.json](outputs/mois_summary_2026-10-03.json) | 기능별 현황·분모·결측·원문 검증 상태 |
| [analyses/digital-inclusion/outputs/mois_region_comparison_2026-10-03.csv](outputs/mois_region_comparison_2026-10-03.csv) | 지역별 휠체어·촉각 기능과 분모 |
| [analyses/digital-inclusion/data/pps_registrations.csv](data/pps_registrations.csv) | 계약·물품 등록 397행 |
| [analyses/digital-inclusion/data/pps_deliveries.csv](data/pps_deliveries.csv) | 납품요구·변경 상세 1,494행 |
| [analyses/digital-inclusion/data/pps_registrations_manifest.json](data/pps_registrations_manifest.json), [analyses/digital-inclusion/data/pps_deliveries_manifest.json](data/pps_deliveries_manifest.json) | 월별 조건·페이지·조회시각·해시 |
| [analyses/digital-inclusion/outputs/pps_summary.json](outputs/pps_summary.json) | 조달 순증의 동일 월·동일 날짜 범위 비교와 한계 |
| [analyses/digital-inclusion/outputs/pps_monthly.csv](outputs/pps_monthly.csv) | 월별 납품요구 순증 수량·금액 |

행안부 원본이 로컬에 있으면 해시·필터·CSV 행을 추가 대조한다. 다른 체크아웃에 원본이 없으면 저장된 CSV·명세로 계산은 재현하지만 원문 재검증은 미실행으로 표시한다. 지역 표시명 파일을 새로 만들거나 출처가 바뀌었다면 전체 원본을 확보한 상태에서 `mois_analyze.py --snapshot YYYY-MM-DD --refresh-region-labels`를 실행한다.

## 인증 수집

프로세스 환경변수를 우선 읽고, 없으면 저장소 루트 `.env`에서 읽는다. `PPS_SHOPPING_MALL_SERVICE_KEY`는 조달청, `MOIS_KIOSK_INFO_SERVICE_KEY`는 행안부다. Encoding 키는 한 번 디코딩한 뒤 요청을 인코딩한다. 키를 명령 인자로 전달하지 않는다.

행안부를 새로 수집할 때는 실제 수집일을 스냅샷 이름으로 사용한다. 아래 날짜는 이번 수집 예시이며 **API의 과거 상태 조회 조건이 아니다.** 같은 날짜의 캐시를 재사용하므로 다른 날의 스냅샷을 만들 때는 수집일을 바꾼다.

```sh
python3 analyses/digital-inclusion/mois_collect.py --snapshot 2026-10-03
```

조달청은 조회조건을 제한해 월별 수집한다. 다음은 이번에 검증한 조건이다.

```sh
python3 analyses/digital-inclusion/pps_collect.py --kind registrations --field prdctClsfcNoNm --term 컴퓨터키오스크 --start 2025-01-01 --end 2026-09-30 --monthly
python3 analyses/digital-inclusion/pps_collect.py --kind deliveries --field prdctClsfcNoNm --term 컴퓨터키오스크 --start 2025-01-01 --end 2026-09-30
```

두 명령은 `.env`와 네트워크가 필요하다. 같은 조건의 로컬 원응답을 재사용한다. 조달청의 `--refresh`는 재요청하며 변경된 이전 바이트를 해시가 붙은 파일로 보존한다. 현재 정규화 CSV·명세는 마지막으로 수집한 조건으로 갱신되므로, 별도 실험에 쓰기 전에 이전 분석의 입력·명세를 함께 보존한다. 원본 응답은 `raw/`에서 Git 제외 상태로 유지한다.

## 검증 명령

```sh
python3 -m unittest discover -s analyses/digital-inclusion/tests -v
python3 analyses/digital-inclusion/pps_analyze.py --self-test
git diff --check
```

인증 테스트는 가짜 키·모의 응답으로 인코딩·오류 처리·키 노출 방지를 검증한다. 조달 검증은 증액·취소·옵션 제외·결측값의 0 대체 방지를 확인한다. 데이터 분석 명령 자체도 입력 해시·수집 범위·중복·분모를 확인한다.

## KOSIS 장기 기준선

저장된 CSV·메타데이터로 계산하는 명령이다. 키와 네트워크가 필요 없다.

```sh
python3 analyses/digital-inclusion/kosis_analyze.py --snapshot 2026-10-03
```

| 파일 | 역할 |
|---|---|
| [analyses/digital-inclusion/kosis_analysis_plan.json](kosis_analysis_plan.json) | 2016년 이후 주 비교, 지수 해석과 출처 대조 규칙 |
| [analyses/digital-inclusion/data/kosis_digital_divide_2026-10-03.csv](data/kosis_digital_divide_2026-10-03.csv) | 종합·접근·역량·활용 × 5계층·집계 × 2014~2025, 총 240셀 |
| [analyses/digital-inclusion/data/kosis_metadata_2026-10-03.json](data/kosis_metadata_2026-10-03.json) | 통계표명·수록기간·항목/분류·주석 |
| [analyses/digital-inclusion/data/kosis_manifest_2026-10-03.json](data/kosis_manifest_2026-10-03.json) | 조회조건·응답 해시·기대 셀과 실제 셀 대조 |
| [analyses/digital-inclusion/outputs/kosis_summary_2026-10-03.json](outputs/kosis_summary_2026-10-03.json) | 범위·추세·최신 격차·보고서 일치 여부와 검증 상태 |
| [analyses/digital-inclusion/outputs/kosis_report_comparison_2026-10-03.csv](outputs/kosis_report_comparison_2026-10-03.csv) | 기존 보고서의 디지털정보화 100개 셀과 대조 |
| [analyses/digital-inclusion/data/source_reconciliation_kosis_2026-10-03.json](data/source_reconciliation_kosis_2026-10-03.json) | 2021 농어민 접근지수의 원출처 간 불일치 기록 |

`outputs/kosis_coverage_*`, `kosis_trends_*`, `kosis_annual_changes_*`, `kosis_latest_gaps_*` CSV도 생성한다. 데이터 원응답이 로컬에 있으면 값·단위·분류·수정일·연간 주기와 해시를 대조하고, 원본이 없는 체크아웃에서는 재검증하지 못한 원응답 수를 표시한다. 기존 보고서 기준선은 수정하지 않는다.

새로 수집하려면 `KOSIS_DIGITAL_DIVIDE_API_KEY`와 네트워크가 필요하다. `--snapshot`은 실제 수집일의 로컬 보관명이며 통계의 조사연도가 아니다.

```sh
python3 analyses/digital-inclusion/kosis_collect.py --snapshot 2026-10-03
```

수집기는 `format=json`, `jsonVD=Y`로 메타데이터의 전체 연도·항목·분류를 읽은 뒤 해당 범위를 수집한다. 캐시를 재사용하며 `--refresh` 시 이전 응답이 달라졌으면 해시가 붙은 파일로 보존한다. 인증키는 프로세스 환경변수 또는 저장소 루트 `.env`에서 로딩한다.

```sh
python3 analyses/digital-inclusion/kosis_collect.py --self-test
python3 -m unittest discover -s analyses/digital-inclusion/tests -v
```

KOSIS 경계 검증은 통계부호와 숫자 0의 구분, 기대 셀 누락·중복, 연간 주기, 100을 넘는 상대지수, 연도 간격 기준 연평균, 출처 단위·비수치 차이를 다룬다.

## 후속 자료

NIA 목록을 다시 확보하면 과거 집계를 새 원자료로 덮어쓰지 않고 수집일·출처를 별도로 보존한다. 검증 이력, 조달 흐름, 기기 기능 이력, 이용자 연간 통계는 관측 단위가 다르므로 각각 분석한다.


## 기관·제품별 후속 분석

`python3 analyses/digital-inclusion/followup_analyze.py`는 기존 검증 함수를 재사용해 2025·2026년 2~9월 조달을 기관 코드·제품 ID·기관 관측 집합별로 분해하고, 2026-10-03 행안부 자료의 기능 조합을 계산한다. 네트워크와 키가 필요 없다. 기관의 한 해 미관측을 폐쇄·구매 중단으로 해석하지 않으며, 기능 조합을 접근성 점수로 만들지 않는다.

결과는 [analyses/digital-inclusion/outputs/followup_summary.json](outputs/followup_summary.json)과 여기서 해시로 연결한 CSV 5개에 저장한다. 공개 문서 조사의 확인 수준은 [analyses/digital-inclusion/data/local_history_sources_2026-10-04.json](data/local_history_sources_2026-10-04.json), 해석은 [docs/digital-inclusion-analysis.md](../../docs/digital-inclusion-analysis.md#followup-decomposition)에 있다. 변경·취소·미상 경계 검증은 기존 `python3 -m unittest discover -s analyses/digital-inclusion/tests -v`에 포함된다.

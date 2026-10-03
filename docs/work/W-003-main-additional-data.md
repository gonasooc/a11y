# W-003 · 디지털포용법 분석의 추가 자료 확보

- 상태: 완료
- 최근 갱신: 2026-10-03
- 관련 문서: [docs/work/W-002-main-digital-inclusion-api.md](W-002-main-digital-inclusion-api.md), [docs/digital-inclusion-analysis.md](../digital-inclusion-analysis.md), [docs/10-digital-inclusion-api-guide.md](../10-digital-inclusion-api-guide.md)

## 현재 상황

KOSIS 실제 인증과 네 통계표의 2014~2025년 240개 관측 수집·분석을 완료했다. 2016년 지표·조사대상 기준 변경을 확인해 장기 주 비교를 2016년 이후로 제한했고, 기존 보고서 100셀 중 99개 일치·1개 원출처 차이를 확인했다. 결과는 [docs/digital-inclusion-analysis.md](../digital-inclusion-analysis.md#digital-baseline)에 있다. 기기·제품·제조사 이력과 차기 연간 자료는 [docs/work/W-004-main-history-data.md](W-004-main-history-data.md)에서 이어간다.

- 완료 조건: 추가로 확보한 자료의 출처·기간·단위·품질을 확인하고, 가능한 분석과 남은 한계를 보고서에 반영한다.
- 사람이 판단할 사항: 이번 KOSIS 분석에는 없음. 추가 이력 자료 요청 방식·범위는 후속 작업의 미정 사항이다.

## 진행과 판단

### 배경과 범위

현재 API로 관찰한 조달 요청 변화와 기능 제공 표시만으로 디지털포용법의 인과효과를 식별할 수 없다. 초기 분석에서 확인된 자료 공백을 이어서 관리한다.

### 중요한 시도와 결정

- 2026-10-03 — KOSIS 키 입력을 확인하고, 공통 HTTP 처리에 공식 `kosis.kr/openapi/`와 `apiKey` 매개변수를 추가했다. 기존 공공데이터포털의 `serviceKey` 처리와 구분하며 실제 값은 기록하지 않는다.
- 2026-10-03 — Context7에 일치하는 KOSIS 문서가 없어 공식 개발가이드로 확인했다. [analyses/digital-inclusion/kosis_collect.py](../../analyses/digital-inclusion/kosis_collect.py)는 `jsonVD=Y`로 정상 JSON을 요청하며, 메타데이터의 연간 주기와 실제 응답의 `PRD_SE=A`를 교차 확인한다.
- 2026-10-03 — 메타데이터 16응답과 통계자료 4응답으로 240개 셀을 수집했다. 표별 연도·항목·분류의 조합과 실제 셀이 정확히 일치한다. 주석에서 2016년 지표 통합·명칭 변경 및 고령층 만50→55세 변경을 확인해 [analyses/digital-inclusion/kosis_analysis_plan.json](../../analyses/digital-inclusion/kosis_analysis_plan.json)에 비교 범위를 기록했다.
- 2026-10-03 — [analyses/digital-inclusion/kosis_analyze.py](../../analyses/digital-inclusion/kosis_analyze.py)로 범위·장기 및 연간 변화·최신 격차·기존 보고서 대조를 계산했다. 2016~2025 장애인 종합은 65.4→84.1, 역량은 49.8→77.0이다. 최신 조사연도가 2025년이므로 시행 후 연간 관측은 없다.
- 2026-10-03 — 2021 농어민 접근지수에서 보고서 94.8·API 94.9 차이를 발견했다. 2025 보고서 PDF49페이지와 2021 보고서 PDF44페이지를 시각 확인해 각각 94.8·94.9임을 확인했다. 공식 정정은 확인하지 못해 기존 기준선을 보존하고 [analyses/digital-inclusion/data/source_reconciliation_kosis_2026-10-03.json](../../analyses/digital-inclusion/data/source_reconciliation_kosis_2026-10-03.json)에 원문·해시·처리를 남겼다.
- 2026-10-03 — KOSIS는 기존 보고서 기준선을 보완할 수 있지만 미공표 시행 후 연간 수치를 키만으로 얻을 수는 없다.
- 2026-10-03 — 행안부 수정·갱신일은 설치일이 아니다. 과거 기능·교체 이력이나 반복 스냅샷이 필요하며, 정기 실행은 아직 설정하지 않았다.
- 2026-10-03 — NIA 최초 검증·갱신·철회 이력과 시행 당시 제조사 규모·역할이 추가로 필요하다. 현재 조달 등록의 중소기업 분류로 중기업·소기업을 나눌 수 없다.

### 검증

- 실제 인증·수집 — 통과. 네 통계표의 2014~2025년 240셀, 누락·중복·비수치 0개. 원응답 20개 해시와 정규화 CSV의 값·분류·주기·단위·수정일이 일치한다.
- 독립 산술 대조 — 통과. 범위 20계열, 기간 차이 40개, 연간 차이 180개, 최신 격차 20개, 보고서 대조 100개를 별도 계산해 일치를 확인했다.
- `python3 -m unittest discover -s analyses/digital-inclusion/tests -v` — 13개 통과. 인증 매개변수·노출 방지·통계부호/0·100 초과 지수·연도 간격·출처 단위/결측 차이를 검증했다.
- `python3 analyses/digital-inclusion/kosis_collect.py --self-test` — 기호·중복·누락·음수·주기 검증 통과. 실제 키·네트워크를 사용하지 않았다.
- `python3 analyses/digital-inclusion/kosis_analyze.py --snapshot 2026-10-03` — Python 3.14.2에서 통과. 반복 실행한 출력 해시가 동일하며 초기 기준선·PPS·MOIS 출력도 유지됐다.
- 소스·산출물·캐시 텍스트 502개에서 세 인증키와 인코딩 변형을 검사 — 노출 없음. `.env`와 원본 PDF의 Git 제외, `git diff --check`도 통과.

### 세션 메모

- 2026-10-03 · Codex — 완료된 두 API 분석에서 필요한 후속 자료를 분리했다. 재개 시 첫 행동은 KOSIS 키 또는 추가 이력 자료의 준비 여부와 요청 범위를 확인하는 것이다.
- 2026-10-03 · Codex — KOSIS 인증부터 240셀 수집, 장기 기준선·원출처 대조와 실행 문서까지 마무리했다. 수치 불일치는 전사 오류가 아닌 출처 차이로 남겼다. 다음 행동은 W-004의 추가 이력 확보 범위 확인이다.

## 남은 일

- [x] KOSIS 키의 실제 인증, 분류코드·수록기간을 확인하고 수집기를 구현한다.
- [x] 240개 관측의 완전성·출처·기간을 검증하고 장기 기술통계를 계산한다.
- [x] 기존 보고서 100개 관측과 대조하고 불일치 원문을 확인해 두 버전을 보존한다.
- [x] 비교 가능성과 시행 후 관측 유무를 판단하고 결과·한계를 기록한다.
- [x] 이번 연간 통계로 확보할 수 없는 기기·검증·제조사 이력은 W-004로 연결한다.

재개에 필요한 코드 상태: 작성 당시 `main`, HEAD `c29288ed8116fc374559f24143e7fc72031718b0`. 문서·분석 변경은 미커밋 상태이므로 재개 시 현재 파일과 Git 상태를 다시 확인한다.

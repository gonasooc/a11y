# W-011 · 영상 미디어 접근성 자료 보완: 키 후보 확인, 등록 통계 시계열, 2012~2016 방송 실적

- 상태: 완료
- 최근 갱신: 2026-10-17
- 관련 문서: [docs/README.md](../README.md), [docs/work/W-009-main-media-access.md](W-009-main-media-access.md), [docs/media-access/README.md](../media-access/README.md), [docs/media-access/environment.md](../media-access/environment.md#6-데이터-공백), [analyses/media-access/README.md](../../analyses/media-access/README.md)

## 현재 상황

W-009의 영상 미디어 조사는 공개 파일(HWPX·PDF)만 내려받아 API 키가 필요 없었다. 이 작업은 남은 공백을 메우려고 키가 필요한 후보 서비스를 확인하고, 청각·시각장애인 등록 통계 시계열과 2012~2016년 방송 편성 실적을 보강한다. 2026-10-17에 네 항목을 모두 진행했다. `.env.example` 안내 경로를 고쳤다. 열린재정·KOBIS는 키를 받기 전에 쓸 수 있는지만 확인했다. KOSIS 등록 통계 2007~2025 추이와 2012~2016년 방송 실적은 수집·계산·테스트를 마치고 근거 문서에 반영했다. 사용자가 `.env`에 새 KOSIS 변수와 열린재정 키를 넣었고, 열린재정으로 관련 4개 부처의 2024~2026년 세부사업을 조회해 OTT 장애인 접근 지원을 이름으로 내건 세부사업이 없음을 확인했다. 완료 조건을 모두 채워 완료로 바꿨다. 남은 확인 항목은 [docs/media-access/README.md](../media-access/README.md#다시-확인해야-할-시점)에서 관리한다.

- 완료 조건: 열린재정·KOBIS를 쓸 수 있는지 판단하고 근거를 남긴다. 등록 통계 시계열과 2012~2016년 실적을 재현 가능한 데이터(출처 명세·해시 포함)로 만들거나, 못 만들면 그 이유를 기록한다. 바뀐 실행 방법·환경 변수를 `docs/specs.md`·`docs/architecture.md`·`analyses/media-access/README.md`에 반영한다.
- 사람이 판단할 사항: 없음. 열린재정 키는 2026-10-17 발급했다. KOBIS 키는 발급하지 않는 쪽을 권했다(약관이 결과 저장을 금지하고, 상영 횟수를 상영형태별로 주는 API가 없음).

## 진행과 판단

### 배경과 범위

- 2026-10-17 — 사용자가 영상 미디어 조사에 키가 필요 없었던 이유와 보완 시 필요한 키를 물었다. 에이전트가 필수 키는 없고, KOSIS 기존 키 재사용(선택), 열린재정·KOBIS(확인 먼저), `.env.example` 주석 수정을 제안했다. 사용자가 네 항목(주석 수정, 열린재정·KOBIS 확인, 등록 통계 시계열, 2012~2016 방송 실적)을 모두 진행하라고 했다.

### 중요한 시도와 결정

- 2026-10-17 — [.env.example](../../.env.example) 2행이 없는 파일 `docs/10-digital-inclusion-api-guide.md`를 안내하고 있었다. [docs/specs.md](../specs.md)가 가리키는 [docs/digital-inclusion/analysis.md](../digital-inclusion/analysis.md#부록-b-디지털포용법-분석에-필요한-api) 부록 B로 바꿨다. [docs/digital-inclusion/README.md](../digital-inclusion/README.md)의 같은 경로는 이전 경로 대응표라 그대로 둔다.
- 2026-10-17 — **키 후보 확인(에이전트 조사, 공개 화면과 공식 샘플키 미리보기만 사용, 키 신청·로그인 없음).**
  - 열린재정: 자체 인증키(본인인증 필요, 공공데이터포털 아님). 세부사업 '소외계층방송접근권보장'(소관 과학기술정보통신부, 방송통신발전기금, 단위사업 '미디어 다양성 및 공공성 확보')의 2018~2026년 예산이 `TotalExpenditure5`에 있다. 당년도조정금액은 2018년 11,016,000에서 2025년 21,870,000, 2026년 19,677,000(확정조정 20,077,000)이고, 단위 표기가 없어 천원으로 추정한다. 세부사업 단위 집행액은 Open API에 없다(결산·월별 집행은 단위사업×지출목까지). OTT 경비 지원(제22조의10②)에 해당하는 별도 세부사업은 찾지 못했지만, 샘플키가 5건 고정이라 단위사업 안의 세부사업 10~11건을 다 보지 못해 없다고 확정할 수 없다. 정식 키로 `pSize=100` 조회 한 번이면 확인된다.
  - KOBIS: 오픈API에 배리어프리·자막·화면해설 전용 필드가 없고, 박스오피스는 상영형태별로 나뉘지 않아 배리어프리 상영 횟수를 뽑을 수 없다. 영화 상세 `showTypeNm`에 '디지털 한글자막 CC', '디지털 가치봄'이 나올 가능성은 있지만 확인하지 못했다(추정, 웹 상세화면에는 표시됨). 약관이 "결과를 복제 또는 저장"하는 것을 금지해, 원응답을 저장하는 이 저장소의 방식과 맞지 않는다. 대안은 영화진흥위원회 공지 '한국영화의 한글자막(CC) 상영 영화 및 극장 안내'(2023·2024·2025)와 보도자료(매년 약 100편 CC·AD 제공, 2024년부터 복권기금 약 45억 원)다. 연도별 지원 편수·상영 횟수를 표로 낸 공식 자료는 찾지 못했다.
  - 판단(에이전트 제안): KOBIS 키는 발급하지 않는 쪽을 권한다. 열린재정 키는 OTT 세부사업 유무 하나를 확인할 때만 의미가 있다. 발급 여부는 사용자가 정한다.
- 2026-10-17 — **KOSIS 등록 통계.** 보건복지부 「장애인현황」(orgId=117)의 `DT_11761_N003`(연령별·유형별·성별, 2007~2025)에서 청각·시각·전체 × 5세 구간 × 계를 받았다. `DT_11761_N001`(유형별, 1989~)은 유형별 합계 대조용이다. 수집기 [analyses/media-access/kosis_registry_collect.py](../../analyses/media-access/kosis_registry_collect.py), 분석 [analyses/media-access/registry_analyze.py](../../analyses/media-access/registry_analyze.py).
  - 인증 코드는 [analyses/digital-inclusion/api_common.py](../../analyses/digital-inclusion/api_common.py)를 경로를 더해 가져다 쓴다. 키 처리 코드를 두 벌 두지 않으려는 선택이다(에이전트 판단). 공통 폴더로 옮기는 방안은 열어 둔다.
  - 키 이름은 [docs/specs.md](../specs.md)의 서비스별 이름 규칙에 따라 `KOSIS_DISABILITY_API_KEY`로 새로 두고 [.env.example](../../.env.example)에 더했다. 사용자 `.env`는 고치지 않았다(W-002와 같은 원칙). 이번 수집은 기존 `KOSIS_DIGITAL_DIVIDE_API_KEY` 값을 새 이름으로 실행 프로세스 환경에만 넘겨 실행했다. 다음 수집부터는 사용자가 `.env`에 같은 값으로 한 줄을 더해야 한다.
  - 처음 실행은 2007년 연령 구간 합이 합계보다 작아 멈췄다. 2007~2014년은 100세 이상 구간과 '해당없음'을 공표하지 않는다(2015년부터 100세 이상, 2016년에만 '해당없음' 셀이 있음). 그래서 이 두 가지가 모두 없는 해에만 차이를 `unallocated_by_year`로 남기고, 그 밖의 불일치·초과는 계속 멈추게 했다. 차이는 2007년 전체 1,014명이 가장 크다(청각 167, 시각 123). 65세 이상 비율은 공표 구간만 더하고, 차이를 모두 65세 이상으로 볼 때의 비율을 따로 둔다(최대 0.1%p 차이, 10칸).
  - N001은 청각을 '청각ㆍ언어'(`CHU45`)의 하위 코드 `CHU041`에 둔다. `CHU04`로 요청하면 빈 응답이라 표마다 유형 코드를 나눴다. 청각·시각은 19개 연도 모두 N001과 같다. **2013년 전체만 N003 2,500,961명, N001 2,501,112명으로 151명 다르다.** 원인은 확인하지 못했고 양쪽 값을 남긴다.
  - 결과(사실, [analyses/media-access/outputs/registry_by_year.csv](../../analyses/media-access/outputs/registry_by_year.csv)): 청각 203,324명(2007) → 250,334명(2015) → 449,269명(2025), 65세 이상 비율 52.3% → 84.6%. 시각 216,881명(2007) → 최대 253,095명(2013) → 245,361명(2025), 65세 이상 36.5% → 59.1%. 전체 등록장애인 중 청각 비중 9.7% → 17.1%. 2016년 이후 청각 등록이 빠르게 늘었지만 원인(판정 기준·보청기 지원 등)은 이 자료로 알 수 없다.

- 2026-10-17 — **2012~2016년 방송 실적.** 방송통신위원회 보도자료 5건(boardSeq 36057·38640·41299·42607·44899)의 HWP 7개를 받아 방송사별 목표·실적을 읽었다. 수집기 [analyses/media-access/kmcc_collect.py](../../analyses/media-access/kmcc_collect.py), 해석기 [analyses/media-access/hwp5_table.py](../../analyses/media-access/hwp5_table.py)·[analyses/media-access/kmcc_parse.py](../../analyses/media-access/kmcc_parse.py), 분석 [analyses/media-access/broadcast_early_analyze.py](../../analyses/media-access/broadcast_early_analyze.py).
  - 수집 전 확인(사실): robots.txt는 `User-agent: Googlebot`에만 `/user.do` 등을 막고 `*` 규칙이 없다(직접 확인). 누리집 하단에 이용약관은 없고 저작권보호정책에 자동 수집 금지 조항이 없다. 다섯 게시물의 공공누리 유형 칸은 비어 있다(에이전트 확인). 첨부는 게시물을 먼저 연 같은 세션에서 Referer를 붙여야 받을 수 있다.
  - 구형 HWP는 표준 라이브러리로 OLE 복합 문서와 본문 레코드를 읽는다. 실제 파일에서 셀 목록 머리가 표 레코드와 같은 깊이에 있고, 각주·글상자의 목록 머리는 더 깊은 것을 확인해 그 깊이로 셀만 골랐다. 에이전트의 임시 해석기는 이 구분이 없어 글상자를 가짜 셀로 읽었다.
  - 2013년 SO 표는 번호 칸과 사업자명 칸의 병합이 한 줄 어긋나 있다(번호 39가 경남방송 아랫줄에서 시작). 그래서 보조 행은 '앞 사업자 행과 같은 번호 칸을 쓰는 행'으로 판정한다. 해마다 MBC경남(창원·진주) 한 줄이 보조 행이다.
  - 2012년 미달은 행으로 세면 24, 사업자로 세면 23이다. MBC경남 진주 행도 미달이기 때문이고, 보조 행을 빼는 기존 규칙으로 보도자료의 23개사와 같아졌다(에이전트의 추정을 확인).
  - 목표의 성격은 `target_basis`로 남긴다. 2012년은 방송사 제시·방통위 승인(붙임 원문), 2013~2016년은 보도자료의 '방송사업자별 편성비율 목표치를 ’12년부터 ’16년까지 단계적으로 높여왔다'에 따라 사업자별 단계 목표로 둔다. 2017년 이후와 기준이 달라 출력 파일을 `broadcast_early_*`로 나누고, 웹 보고서가 읽는 기존 `broadcast_*` 출력과 `site/`는 건드리지 않았다(에이전트 판단, 구조 규칙으로 [docs/architecture.md](../architecture.md)에 적음).
  - 보도자료 집계 43건을 [analyses/media-access/data/kmcc_early_statements.csv](../../analyses/media-access/data/kmcc_early_statements.csv)로 옮겼다. 2012년 집계표의 지역지상파 자막 '44(3)'은 달성 수가 46개사와 맞지 않는 원문 표기 오류로 보고 미달 수 3만 대조한다.
  - 결과(계산, [analyses/media-access/outputs/broadcast_early_compliance_by_year.csv](../../analyses/media-access/outputs/broadcast_early_compliance_by_year.csv)): 한 가지 이상 미달 사업자 2012년 50곳 중 23, 2013년 153곳 중 58, 2014년 156곳 중 3, 2015년 145곳 중 4, 2016년 139곳 중 6.
- 2026-10-17 — 사용자가 열린재정 인증키를 발급받았다(활용용도 '연구 목적'). 변수 이름은 서비스별 이름 규칙에 따라 `OPENFISCAL_BUDGET_API_KEY`로 정하고(에이전트 제안) [.env.example](../../.env.example)과 [docs/specs.md](../specs.md)에 더했다. 키 값은 사용자가 `.env`에 직접 넣는다.
- 2026-10-17 — **열린재정 조회.** 사용자가 `.env`에 키를 넣은 뒤(키 값 출력 없이 한 줄·32자 영숫자 확인) [analyses/digital-inclusion/api_common.py](../../analyses/digital-inclusion/api_common.py)의 허용 호스트에 `openapi.openfiscaldata.go.kr`(인증 매개변수 `Key`)을 더하고, 요청 매개변수로 `Key`를 넘기지 못하게 했다. 수집기 [analyses/media-access/openfiscal_collect.py](../../analyses/media-access/openfiscal_collect.py).
  - 수집 전 확인(사실): API 호스트에는 robots.txt가 없다(오류 페이지로 넘어감). 누리집(www) robots.txt는 `User-agent: *`에 `Disallow: /`라 약관 페이지를 자동으로 받지 않았다. 검색으로도 Open API 약관 원문을 찾지 못했다. 공공데이터포털의 한국재정정보원 재정 데이터는 '이용허락범위 제한 없음'이다. 사용자가 발급받은 키로 공식 API를 목적대로 쓰는 것이라 진행했다(에이전트 판단).
  - 확인용 조회 3회(scratchpad, 저장소 밖)로 응답 구조를 봤다. 본문이 JSON 문자열을 한 번 더 감싼 형태다. 2026년 단위사업 '미디어 다양성 및 공공성 확보'의 세부사업은 11개이고 OTT 지원 항목이 없다. 새로 생긴 1건은 '방송·통신 쇼핑 이용자 보호 연구용역'이다.
  - 본 조회(API 21회): 과학기술정보통신부·방송통신위원회·방송미디어통신위원회·문화체육관광부 × 2024~2026년 전체 세부사업 3,903행(총지출, 예산·기금 전체)과 '소외계층방송접근권보장' 2018~2026년. **결과(사실)**: 장애인의 OTT 시청 편의를 이름으로 내건 세부사업은 없다. OTT가 들어간 것은 'OTT산업경쟁력강화'(방송통신발전기금, 해마다 600,000)와 'AI 융합 OTT 글로벌 진출 확산 지원'(2026년, 1,200,000)뿐이다. '소외계층방송접근권보장' 확정액은 2018년 11,016,000 → 2025년 21,870,000 → 2026년 20,077,000(천원 추정)으로, 에이전트가 샘플키로 본 값과 같다.
  - 해석의 한계: 이름으로만 골랐다. 세부사업 안의 내역사업과 집행액은 Open API에 없어 'OTT 경비 지원이 없다'가 아니라 '별도 세부사업이 없다'까지만 말할 수 있다. 2024년 콘진원 OTT 배리어프리 지원은 문체부의 다른 세부사업 안에 들어 있을 것으로 보인다(추정).
- 2026-10-17 — **문서 반영.** [docs/media-access/environment.md](../media-access/environment.md#21-규모와-나이-ab)(등록 추이 표), [docs/media-access/analysis.md](../media-access/analysis.md#28-20122016년-실적)(2.8절), [docs/media-access/README.md](../media-access/README.md#다시-확인해야-할-시점)(출처·서로 다른 수치·한계·재확인 목록), [analyses/media-access/README.md](../../analyses/media-access/README.md), [docs/specs.md](../specs.md)(실행 명령·환경 변수·'공표 구조로 인한 합계 차이' 규칙), [docs/architecture.md](../architecture.md)(구성 요소·폴더·폴더 간 의존 규칙), [docs/README.md](../README.md). 웹 보고서는 바꾸지 않았다.

### 검증

- 2026-10-17 · macOS, `/usr/bin/python3`(3.9.6) — KOSIS 수집: 수집기의 실제 호출은 7회(메타 4, N003 자료 1, N001 자료 2)다. 첫 N001 응답은 청각 코드가 맞지 않아 지우고 다시 받았다. 코드 확인용 단발 호출 1회가 따로 있다. 마지막 실행은 캐시만 읽어 호출 0회. 연령 표 1,359칸, 유형 표 57칸, CSV SHA256 `7269876a…`. 키 값은 출력·파일·명령 인자에 남기지 않았다.
- 2026-10-17 · `python3 analyses/media-access/registry_analyze.py --snapshot 2026-10-17` — 3.9.6과 3.11.5에서 같은 결과. N001 대조 57칸 중 일치 56·다름 1, 문서 값(2025년 청각·시각 인원과 65세 이상 비율) 4건 일치. 디지털포용법 문서의 전체 65세 이상 비율(2015년 42.3%, 2020년 49.9%, 2024년 55.3%, 2025년 56.9%)과도 같다.
- 2026-10-17 · `python3 -m unittest discover -s analyses/media-access/tests -v` — KOSIS 테스트 추가 시점 15개, 최종 24개 통과(기존 8, KOSIS 7, HWP·2012~2016 9), 3.9.6·3.11.5. `analyses/digital-inclusion/tests` 16개도 통과.
- 2026-10-17 · `python3 analyses/media-access/kmcc_collect.py --snapshot 2026-10-17` — 게시물 5건·첨부 7개, 리다이렉트 없음. SHA256이 에이전트 조사 때 따로 받은 파일 7개와 모두 같다.
- 2026-10-17 · `kmcc_parse.py` → `broadcast_early_analyze.py` — 사업자 수 50·153·156·145·139가 원문 사업자군 표기·보도자료와 같다. 보도자료 집계 43건 모두 일치(사업자군별 한 가지 이상 미달, 2012·2014년 서비스별 미달). 2016년 미달 6개사 명단과 2014년 '미달성은 폐쇄자막 위반' 비고도 계산과 같다. 2012년 PDF 첨부와 11개 사업자 44칸이 같다.
- 2026-10-17 · 재현 — 3.11.5로 만든 새 출력·데이터 10개를 3.9.6으로 다시 만들어 SHA256이 모두 같다. 기존 `broadcast_analyze.py`를 다시 실행해도 기존 `data/`·`outputs/` 파일에 변경이 없다(`git status`). `node site/scripts/generate.mjs --check`(Node 22.12.0) 두 보고서 통과.
- 2026-10-17 · `.env` 추가 뒤 — `KOSIS_DISABILITY_API_KEY`가 한 줄만 있고 값이 기존 KOSIS 키와 같음을 키 값 출력 없이 확인했다. 프로세스 환경변수 없이 `python3 analyses/media-access/kosis_registry_collect.py --snapshot 2026-10-17`이 `.env`의 키로 실행됐다(캐시 사용, API 호출 0회). 다시 만든 CSV·명세의 SHA256이 같다. `.env`는 Git 제외.
- 2026-10-17 · `python3 analyses/media-access/openfiscal_collect.py --snapshot 2026-10-17` — API 21회, 결과 코드 모두 정상(`INFO-000`, 해당 부처가 없는 해는 0행). 부처·연도 12개 조합 모두 받은 행 수가 `list_total_count`와 같고 중복이 없다. 고른 74행을 CSV로 남겼다.
- 2026-10-17 · 테스트 — `analyses/media-access/tests` 28개(열린재정 4개 추가), `analyses/digital-inclusion/tests` 17개(열린재정 인증 1개 추가) 통과, Python 3.9.6·3.11.5.
- 2026-10-17 · 문서 — 변경 문서 9개의 상대경로 링크·앵커 191개(열린재정 반영 뒤 다시 218개) 검사 오류 0(임시 검사 스크립트, GitHub 방식 앵커 근사), `git diff --check` 통과, 새 파일 줄 끝 공백 없음, 변경·새 파일 UTF-8 확인. 새·수정 파일과 로컬 원응답 42개에서 KOSIS 키와 인코딩 변형이 나오지 않았다. 열린재정 반영 뒤 저장소 변경 파일·원응답·임시 폴더 179개에서 세 키(KOSIS 2, 열린재정 1)를 다시 찾았고 나오지 않았다. 사이트 생성 검사도 다시 통과했다.

### 세션 메모

- 2026-10-17 · Claude Code — 작업 문서를 만들고 주석을 고쳤다. 에이전트 세 개로 열린재정·KOBIS, KOSIS 통계표, 2012~2016년 보도자료를 조사했고, KOSIS와 2012~2016년 파이프라인·테스트·문서 반영을 마쳤다. 커밋은 하지 않았다. 열린재정 키를 받아 OTT 지원 세부사업이 없음을 확인하고 작업을 완료로 바꿨다. 다음 행동은 사용자가 커밋이나 웹 보고서 반영(선택)을 정하는 것이다.

## 남은 일

- [x] `.env.example`의 안내 경로 수정.
- [x] 열린재정: 장애인방송·OTT 관련 세부사업이 따로 보이는지, Open API 키 발급 방식을 확인한다.
- [x] KOBIS: Open API 응답에 배리어프리·자막·화면해설 표시가 있는지 확인한다.
- [x] 사용자 결정: 열린재정 키를 발급해 OTT 세부사업 유무를 확인할지(2026-10-17 발급). KOBIS 키는 발급하지 않는 쪽을 권했다.
- [x] 사용자: `.env`에 `OPENFISCAL_BUDGET_API_KEY`를 넣는다.
- [x] 등록 통계: KOSIS에 청각·시각 등록장애인 연도별·연령별 통계표가 있는지 확인하고, KOSIS와 보건복지부 XLSX 중 수집 경로를 정한다(KOSIS `DT_11761_N003`).
- [x] 등록 통계 수집기·분석·테스트 작성.
- [x] 사용자: `.env`에 `KOSIS_DISABILITY_API_KEY`를 `KOSIS_DIGITAL_DIVIDE_API_KEY`와 같은 값으로 더한다(2026-10-17 사용자가 명령으로 추가).
- [x] 2012~2016년 방송 실적: 보도자료 첨부(PDF·HWP)를 수집하고 표를 읽을 수 있는지 확인한다.
- [x] 2012~2016년 수집기·HWP 해석기·분석·테스트 작성, 보도자료 집계 대조.
- [x] 키·실행 방법이 바뀌면 `.env.example`, `docs/specs.md`, `docs/architecture.md`, `analyses/media-access/README.md`, `docs/media-access/` 문서를 갱신한다.
- [x] 키가 들어가면 `TotalExpenditure5`로 단위사업 '미디어 다양성 및 공공성 확보'의 세부사업 전체를 조회해 OTT 지원 항목이 있는지 확인한다(관련 4개 부처 2024~2026년 전체로 넓혀 확인, 별도 세부사업 없음).
- [x] (선택) 웹 보고서에 등록 추이나 2012~2016년 실적을 넣을지는 사용자가 정한다. 넣는다면 2017년 이후와 한 줄로 잇지 않는 표시가 필요하다. → 2026-10-17 사용자 요청으로 [docs/work/W-012-main-media-access-report-update.md](W-012-main-media-access-report-update.md)에서 넣었다.
- [ ] 남은 확인 항목(청각 등록 급증 원인, 2013년 KOSIS 151명 차이, 2016·2017 산정 기준)은 [docs/media-access/README.md](../media-access/README.md#다시-확인해야-할-시점)에서 관리한다.

재개에 필요한 코드 상태: `main`, 모두 미커밋. 수정 11개(`.env.example`, `docs/README.md`, `docs/architecture.md`, `docs/specs.md`, `docs/media-access/` 4개, `analyses/media-access/README.md`, `analyses/digital-inclusion/api_common.py`·`tests/test_api_common.py`)와 새 파일 25개(이 문서, `analyses/media-access/`의 코드 7개·테스트 3개·`data/` 8개·`outputs/` 6개). 원본은 로컬 `analyses/media-access/raw/`의 `kosis/2026-10-17/`(6개), `kmcc/`(7개), `openfiscal/2026-10-17/`(21개)에만 있다(Git 제외, 해시는 `data/`의 명세).

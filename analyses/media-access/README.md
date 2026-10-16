# 장애인방송 편성 실적 분석 재현

**2026-10-13 기준 기술통계**다. 결과와 해석 한계는 [docs/media-access/analysis.md](../../docs/media-access/analysis.md), 조사 범위와 출처는 [docs/media-access/README.md](../../docs/media-access/README.md)에 있다. 2026-10-17에 [등록 장애인 통계(KOSIS)](#등록-장애인-통계kosis), [2012~2016년 편성 실적](#20122016년-편성-실적방송통신위원회-보도자료), [열린재정 세부사업 예산](#열린재정-세부사업-예산)을 더했다(작업 기록 [docs/work/W-011-main-media-access-supplement.md](../../docs/work/W-011-main-media-access-supplement.md)).

시청자미디어재단이 사전정보공표로 공개한 2017~2025년 방송사별 장애인방송 편성 실적(폐쇄자막·화면해설·한국수어방송의 목표·실적)을 읽어, 연도별 미달 사업자 수와 사업자군 평균을 계산한다. 방송미디어통신위원회 보도자료의 공식 평균·발표 수치와도 대조한다. OTT는 다루지 않는다(이유는 [docs/media-access/analysis.md](../../docs/media-access/analysis.md#3-ott는-왜-세지-않았나)).

## 실행

Python 표준 라이브러리만 쓴다. Python 3.9.6에서 실행을 확인했다(2026-10-17 추가분은 3.9.6과 3.11.5). 저장소 루트에서:

```sh
python3 analyses/media-access/broadcast_analyze.py
python3 -m unittest discover -s analyses/media-access/tests -v
```

분석은 `data/`만 읽고 `outputs/` 네 파일을 다시 만든다. 네트워크와 API 키가 필요 없다.

원본에서 다시 만들 때는 수집과 해석을 먼저 실행한다. 수집기는 요청 사이에 1초씩 쉬고 `kcmf.or.kr`에만 접속한다.

```sh
python3 analyses/media-access/kcmf_collect.py --snapshot 2026-10-13
python3 analyses/media-access/kcmf_parse.py
```

| 파일 | 내용 |
|---|---|
| [hwpx_table.py](hwpx_table.py) | HWPX(한글 문서) 표의 셀 주소·병합을 읽는다. 형광펜 같은 하위 요소 뒤의 글자도 읽는다 |
| [kcmf_collect.py](kcmf_collect.py) | 재단 게시판의 연도별 첨부 HWPX를 `raw/kcmf/`에 받고 크기·SHA256을 명세에 남긴다 |
| [kcmf_parse.py](kcmf_parse.py) | 원본 해시를 확인한 뒤 표를 행으로 바꾼다. 사업자군별 행 수, 일련번호, 빈 값, 중복을 검사하고 어긋나면 멈춘다 |
| [broadcast_analyze.py](broadcast_analyze.py) | 연도별 미달 수, 사업자군 평균, 공식 발표와의 대조, 화면해설 재방송 요약 |
| [data/kcmf_manifest.json](data/kcmf_manifest.json) | 게시물 제목·작성일·첨부 파일 이름·크기·SHA256 |
| [data/broadcast_operator_years.csv](data/broadcast_operator_years.csv) | 9개 연도 1,139행. 사업자 1,135행과 보조 행 4행 |
| [data/broadcast_ad_rerun.csv](data/broadcast_ad_rerun.csv) | 2023~2025년 화면해설 재방송 비율 30행. 2025년은 분 단위 시간 포함 |
| [data/broadcast_parse_notes.json](data/broadcast_parse_notes.json) | 연도별 행 수, 원문에 표기된 사업자군별 사업자 수 |
| [data/kmcc_group_means.csv](data/kmcc_group_means.csv) | 2023·2025년 보도자료 붙임 표의 사업자군 평균 42개(원문 PDF에서 옮김) |
| [data/kmcc_compliance_statements.csv](data/kmcc_compliance_statements.csv) | 보도자료 본문의 미달 사업자 수 6건 |
| [outputs/broadcast_compliance_by_year.csv](outputs/broadcast_compliance_by_year.csv) | 연도·서비스별 미달 수, 미달 폭 분포, 최대 미달 폭 |
| [outputs/broadcast_group_summary.csv](outputs/broadcast_group_summary.csv) | 연도·사업자군별 목표 값과 실적 평균(ROUND_HALF_UP, 소수 둘째 자리) |
| [outputs/broadcast_official_check.csv](outputs/broadcast_official_check.csv) | 공식 사업자군 평균과 계산값의 대조 결과 |
| [outputs/broadcast_summary.json](outputs/broadcast_summary.json) | 입력 SHA256, 연도별 요약, 대조 결과, 해석 한계 |

## 해석 규칙과 원문 처리

- **미달**은 실적이 목표보다 작은 경우다. 목표 100%에 99.99%도 미달로 센다. 공식 발표도 같은 기준이다(2025년 12곳 일치).
- **보조 행**은 일련번호를 앞 행과 나눠 쓰는 행이다(2017년 같은 사업자의 다른 편성 단위 2행, 2019년 '스마트수어 포함' 실적 2행). 사업자 수와 미달 수에서 빼고 따로 센다.
- 원문 `-`는 `NA`(해당 없음), 빈칸은 오류로 처리한다. 값은 원문 자릿수를 그대로 둔다.
- 2018년 파일에는 사업자군 열이 없다. 이 해는 사업자군별 요약에서 '표기 없음'으로 둔다.
- 2022년 지상파·보도·종편의 한국수어 목표는 원문이 5.06%다. 2023년 7% 상향과 관련된 일할 계산으로 보이지만 확인하지 못했다(추정).
- 공식 표의 사업자군 평균은 방송사별 실적의 단순 평균을 소수 둘째 자리에서 **버린** 값과 같다(2025년 21개 모두). 2023년은 21개 가운데 12개가 계산값과 다르고 채널 수 가중으로도 맞지 않는다. 원인을 모르므로 양쪽 값을 남기고 오류로 멈추지 않는다.

## 재현 범위와 검증

원본 HWPX는 `raw/`에 두고 Git에서 제외한다. 다른 환경에서는 명세의 `download_url`에서 받아 SHA256을 비교하면 원문을 다시 확인할 수 있다. 재단이 같은 게시물의 파일을 바꾸면 해시가 달라지므로 해석기가 멈춘다.

2026-10-13 확인 내용: 해석을 다시 실행해 `data/`·`outputs/`의 해시가 같았다. 9개 연도 모두 원문에 표기된 사업자군별 사업자 수와 행 수가 일치했고, 일련번호가 1부터 빠짐없이 이어졌다. 테스트 8개(`tests/test_media_access.py`)는 병합 셀, 형광펜 속 글자, 쪽이 바뀐 연속 표, 보조 행, 합계 불일치, 빈 값, 재방송 시간 합계, 미달 판정과 버림 대조를 확인한다. 2026-10-17에 아래 두 자료의 테스트 16개를 더해 모두 24개다.

## 등록 장애인 통계(KOSIS)

**2026-10-17 수집.** 보건복지부 「장애인현황」(KOSIS orgId=117)에서 청각·시각장애인의 2007~2025년 연말 등록 인원과 65세 이상 비율을 계산한다. 결과는 [docs/media-access/environment.md](../../docs/media-access/environment.md#21-규모와-나이-ab)에 있다.

```sh
python3 analyses/media-access/registry_analyze.py --snapshot 2026-10-17
```

분석은 저장된 CSV와 수집 명세만 읽는다. 키와 네트워크가 필요 없다. `--snapshot`은 수집일이고 통계의 기준연도가 아니다.

새로 수집하려면 저장소 루트 `.env`에 `KOSIS_DISABILITY_API_KEY`가 있어야 한다. KOSIS 공유서비스 키는 사용자 단위라 `KOSIS_DIGITAL_DIVIDE_API_KEY`와 같은 값을 넣는다. 키 로딩·HTTPS·오류 처리는 [analyses/digital-inclusion/api_common.py](../digital-inclusion/api_common.py)를 가져다 쓴다. 요청 사이 3.1초를 쉬고, 원응답은 `raw/kosis/<수집일>/`에 둔다.

```sh
python3 analyses/media-access/kosis_registry_collect.py --snapshot 2026-10-17
```

| 파일 | 내용 |
|---|---|
| [kosis_registry_collect.py](kosis_registry_collect.py) | 메타데이터(수록연도·항목·분류 코드)를 확인한 뒤 `DT_11761_N003`(연령 5세 구간 × 전체·청각·시각)과 `DT_11761_N001`(유형별 합계, 대조용)을 받는다 |
| [registry_analyze.py](registry_analyze.py) | 연도별 등록 인원, 65세 이상 인원·비율, 전체 중 비중, N001·문서 값 대조 |
| [data/kosis_registry_2026-10-17.csv](data/kosis_registry_2026-10-17.csv) | N003 1,359칸, N001 57칸 |
| [data/kosis_registry_manifest_2026-10-17.json](data/kosis_registry_manifest_2026-10-17.json) | 요청 매개변수, 응답 SHA256, 통계표 주석, 공표되지 않은 연령 차이 |
| [outputs/registry_by_year.csv](outputs/registry_by_year.csv) | 19개 연도 × 전체·청각·시각, 57행. 65세 이상·65세 미만·연령 미상·공표되지 않은 차이를 열로 나눈다 |
| [outputs/registry_summary.json](outputs/registry_summary.json) | 입력 SHA256, 처음·마지막 해와 최대값, 대조 결과, 해석 한계 |

- 65세 이상은 65-69세부터 120-124세까지 구간의 합이다. '해당없음'(2016년에만 있음)은 넣지 않는다.
- 2007~2014년은 100세 이상 구간과 '해당없음'을 공표하지 않아 연령 구간 합이 합계보다 작다(가장 큰 차이는 2007년 전체 1,014명). 이 차이는 `unallocated`에 두고, 모두 65세 이상이라고 볼 때의 비율을 `age65_plus_share_upper_pct`에 둔다. 두 비율의 차이는 많아야 0.1%p다. 다른 해에 구간 합이 합계와 다르면 수집기가 멈춘다.
- N001은 청각을 '청각ㆍ언어'(`CHU45`)의 하위 코드 `CHU041`에 둔다. 청각·시각은 19개 연도 모두 N003과 같고, 2013년 전체 등록장애인만 N003 2,500,961명, N001 2,501,112명으로 다르다. 원인을 모르므로 양쪽 값을 남긴다.
- KOSIS 기호(`-`)는 0으로 바꾸지 않고 빈 값으로 둔다. 2025년 값 4개(청각·시각 인원과 65세 이상 비율)는 [data/context_facts_2026-10-13.csv](data/context_facts_2026-10-13.csv)의 보건복지부 XLSX 값과 대조해 모두 같았다.

## 2012~2016년 편성 실적(방송통신위원회 보도자료)

**2026-10-17 수집.** 방송통신위원회(현 방송미디어통신위원회) 보도자료 5건에 붙은 구형 한글(HWP) 파일에서 방송사별 자막·화면해설·수화(수어)통역의 목표와 실적을 읽는다. 결과와 해석 한계는 [docs/media-access/analysis.md](../../docs/media-access/analysis.md#28-20122016년-실적)에 있다. 2017~2025년 파일(`broadcast_*.csv`)과 섞지 않는다. 웹 보고서는 이 출력을 2017~2025년 그림과 따로 그린다(그림 3, [docs/work/W-012-main-media-access-report-update.md](../../docs/work/W-012-main-media-access-report-update.md)).

```sh
python3 analyses/media-access/broadcast_early_analyze.py
```

원본부터 다시 만들 때는 수집과 해석을 먼저 실행한다. 수집기는 `www.kmcc.go.kr`에만 접속하고 요청 사이 1초를 쉰다. 첨부는 같은 세션으로 게시물을 먼저 열고 Referer를 붙여야 받을 수 있으며, 리다이렉트되면 멈춘다. 키는 필요 없다.

```sh
python3 analyses/media-access/kmcc_collect.py --snapshot 2026-10-17
python3 analyses/media-access/kmcc_parse.py
```

| 파일 | 내용 |
|---|---|
| [hwp5_table.py](hwp5_table.py) | 구형 HWP(OLE 복합 문서)의 본문 레코드에서 표의 셀 주소·병합·글자를 읽는다. 각주·글상자의 목록은 셀로 세지 않는다. 암호화·배포용 문서는 읽지 않는다 |
| [kmcc_collect.py](kmcc_collect.py) | 게시물 5건의 HWP 7개(본문·붙임)를 `raw/kmcc/`에 받고 크기·SHA256을 명세에 남긴다 |
| [kmcc_parse.py](kmcc_parse.py) | 머리글로 열을 찾아 방송사별 행으로 바꾼다. 원문 사업자군 표기와 행 수, 표마다 일련번호, 빈 값을 검사하고 어긋나면 멈춘다 |
| [broadcast_early_analyze.py](broadcast_early_analyze.py) | 2017~2025년과 같은 형식의 미달 수·사업자군 평균, 한 가지 이상 미달한 사업자 수, 보도자료 집계 대조 |
| [data/kmcc_manifest.json](data/kmcc_manifest.json) | 게시물 제목·등록일·첨부 이름·크기·SHA256, robots.txt·약관 확인 내용 |
| [data/broadcast_operator_years_2012_2016.csv](data/broadcast_operator_years_2012_2016.csv) | 5개 연도 648행(사업자 643, 보조 5). `target_basis`에 목표의 성격을 둔다 |
| [data/broadcast_parse_notes_2012_2016.json](data/broadcast_parse_notes_2012_2016.json) | 연도별 사용한 표, 사업자군별 표기 수, 보조 행 |
| [data/kmcc_early_statements.csv](data/kmcc_early_statements.csv) | 보도자료 집계표의 사업자 수·미달 수 43건(원문 HWP에서 옮김) |
| [outputs/broadcast_early_compliance_by_year.csv](outputs/broadcast_early_compliance_by_year.csv) | 연도·서비스별 미달 수와 미달 폭 |
| [outputs/broadcast_early_group_summary.csv](outputs/broadcast_early_group_summary.csv) | 연도·사업자군별 목표 값과 실적 평균 |
| [outputs/broadcast_early_official_check.csv](outputs/broadcast_early_official_check.csv) | 보도자료 집계 43건과 계산값 대조 |
| [outputs/broadcast_early_summary.json](outputs/broadcast_early_summary.json) | 입력 SHA256, 한 가지 이상 미달 수, 목표의 성격, 해석 한계 |

- **목표의 성격**: 사업자별로 해마다 높인 목표다. 2012년은 방송사가 제시하고 방송통신위원회가 승인했다(붙임 원문). 2015·2016년 보도자료는 "방송사업자별 장애인방송 편성비율 목표치를 ’12년부터 ’16년까지 단계적으로 높여왔"다고 적었다. 2017년 이후 고시의 사업자군별 의무 비율과 기준이 달라, 미달 수와 평균을 2017년 이후 출력과 한 줄로 잇지 않는다.
- **표 구조**: 2012년 표에는 사업자군 칸이 없다(지상파 50개사뿐). 2013년은 필수지정·고시의무 사업자 표가 나뉘고 표마다 1번부터 센다. '보도'·'종편'은 '보도PP'·'종편PP'로 맞춘다. 2012년 표의 달성률 열은 읽지 않는다.
- **보조 행**: 앞 사업자 행과 같은 번호 칸을 쓰는 행이다(해마다 MBC경남 창원·진주 가운데 둘째 행). 2013년 SO 표는 번호 칸과 사업자명 칸의 병합이 한 줄 어긋나 있어, 번호 칸이 시작하는 행으로는 판정하지 않는다.
- **한 가지 이상 미달**은 사업자 행만 센다. 2012년 MBC경남 진주 행도 미달이라 행으로 세면 24가 되지만, 사업자로 세면 보도자료의 23개사와 같다.
- **원문 표기 오류**: 2012년 집계표의 지역지상파 자막 '44(3)'은 달성 수가 지역 46개사와 맞지 않는다(KBS 지역국 18, 지역MBC 15, 지역민방 10의 합은 43). 미달 수 3만 대조한다.

2026-10-17 확인 내용: 사업자 수가 5개 연도 모두 원문 사업자군 표기·보도자료(50·153·156·145·139)와 같다. 보도자료 집계 43건(사업자군별 한 가지 이상 미달, 2012·2014년 서비스별 미달)이 모두 계산과 일치하고, 2016년 미달 6개사 명단도 같다. 2012년 PDF 첨부(같은 문서)와 11개 사업자 44칸을 맞춰 봤다. 원본 7개는 다시 받아도 SHA256이 같았다.

## 열린재정 세부사업 예산

**2026-10-17 수집.** 열린재정 Open API(`TotalExpenditure5`, 총지출 기준)로 과학기술정보통신부·방송통신위원회·방송미디어통신위원회·문화체육관광부의 2024~2026년 세부사업을 모두 받고, 단위사업·세부사업 이름에 OTT·장애·자막·화면해설·수어·수화·접근권·배리어·소외계층이 들어간 행을 고른다. 단위사업 '미디어 다양성 및 공공성 확보'의 세부사업 전체와 세부사업 '소외계층방송접근권보장'의 2018~2026년 금액도 함께 남긴다. 결과는 [docs/media-access/law.md](../../docs/media-access/law.md#41-정부가-ott-접근성에-쓴-것으로-확인된-경로)에 있다.

```sh
python3 analyses/media-access/openfiscal_collect.py --snapshot 2026-10-17
```

`.env`의 `OPENFISCAL_BUDGET_API_KEY`(열린재정에서 발급, 공공데이터포털 키가 아님)와 네트워크가 필요하다. 요청 사이 1.1초를 쉬고, 원응답은 `raw/openfiscal/<수집일>/`에 둔다. 따로 계산하는 분석 스크립트는 없고, 고른 행을 그대로 읽는다.

| 파일 | 내용 |
|---|---|
| [openfiscal_collect.py](openfiscal_collect.py) | 부처·연도별로 모든 쪽을 받아 행 수가 `list_total_count`와 같은지, 중복이 없는지 확인한다. 응답 본문이 JSON 문자열을 한 번 더 감싼 형태라 두 번 푼다 |
| [data/openfiscal_access_lines_2026-10-17.csv](data/openfiscal_access_lines_2026-10-17.csv) | 고른 74행. `included_by`에 고른 이유(keyword·unit·series)가 있다 |
| [data/openfiscal_manifest_2026-10-17.json](data/openfiscal_manifest_2026-10-17.json) | 요청 21건의 매개변수·응답 SHA256·결과 코드, 부처·연도별로 훑은 행 수 |

- 금액 필드는 원문 이름 그대로 둔다. 단위 표기가 없고 이름의 `KCUR`로 보아 천원으로 추정한다. 확정액은 `Y_YY_DFN_MEDI_KCUR_AMT`(필드 설명 '당년도확정조정금액')로 읽는다.
- 이름으로만 고른다. 세부사업 안의 내역사업과 집행액은 이 API에 없다.
- API 호스트에는 robots.txt가 없다. 누리집(www) robots.txt는 일반 로봇에 전체 경로를 막아 약관 페이지를 자동으로 받지 않았고, 약관 원문은 직접 확인하지 못했다. 사용자가 인증키를 발급받으며 약관에 동의했다. 공공데이터포털에 올라 있는 한국재정정보원 재정 데이터는 '이용허락범위 제한 없음'으로 표기돼 있다(검색으로 확인).

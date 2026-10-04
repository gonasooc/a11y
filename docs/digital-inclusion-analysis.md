# 디지털포용법 시행 전후 데이터 분석

> 수집·분석 기준: 2026-10-03 · 초기 보고서·과거 집계 재계산: 2026-10-02
>
> 분석 성격: 공개 자료의 탐색적 기술통계 · 정책 인과효과 판정: **판단 불가**
>
> [docs/10-digital-inclusion-api-guide.md](10-digital-inclusion-api-guide.md) · [analyses/digital-inclusion/README.md](../analyses/digital-inclusion/README.md) · [docs/05-policy-effect-case-proposals.md](05-policy-effect-case-proposals.md)

**시행 전 이용자 지수의 상승, 현재 발급기의 기능 차이, 시행 전후 조달 요청의 변화를 확인했다. 그러나 디지털포용법이 접근성을 얼마나 개선했는지는 아직 판단할 수 없다.** 자료마다 관측 단위와 기간이 다르고, 같은 시기에 다른 접근성 정책도 시행됐기 때문이다.

- 이용자 측에서는 장애인 종합지수가 2016년 **65.4 → 2025년 84.1**, 역량지수가 **49.8 → 77.0**으로 높아졌다. 최신 조사연도는 2025년이어서 모두 법 시행 전 기준선이다.
- 현장 기기 자료에서는 사용 중으로 기재된 무인민원발급기 **5,800건 중 562건**에 휠체어 사용자 조작이 불가능하다고 표시돼 있다. 실제 작동이나 이용 경험은 별도 확인이 필요하다.
- 조달 자료에서는 증명발급기·무인안내시스템의 같은 2~9월 납품요구 순증이 2025년 **872대 → 2026년 597대, 31.5% 감소**했다. 법정 시행일과 같은 날짜인 1/22~9/30끼리 비교하면 **930대 → 716대, 23.0% 감소**다. 구매 요청·변경의 흐름이며 설치 대수나 접근성 개선량은 아니다.

아래 수치는 실제 수집·계산한 기술통계다. 신뢰구간·p값·정책효과 추정치는 산출하지 않았다.

- 결과별 보기: [이용자 기준선](#digital-baseline) · [웹 접근성](#web-baseline) · [발급기 기능·지역](#mois-status) · [조달 흐름](#pps-flow) · [과거 검증 목록](#archived-registry)
- 근거와 한계: [정책 시점](#policy-timeline) · [효과 판정의 한계](#interpretation-limits) · [출처 간 수치 차이](#source-reconciliation) · [재현과 검증](#reproduction)

<a id="data-scope"></a>
## 1. 자료 범위와 정책 시점

### 확보한 자료와 관측 단위

| 자료 | 확보 범위 | 무엇을 관찰하는가 |
|---|---|---|
| NIA 공식 조사 보고서 | 디지털정보화 2021~2025년 100개 값, 민간 웹 접근성 2019~2025년 7개 값 | 이용자 상대지수와 웹 평가의 공표 평균 |
| KOSIS 디지털정보격차 4개 통계표 | 2014~2025년 240개 값; 주 비교는 2016~2025년 200개 | 4개 지표 × 5개 계층·집계의 연간 상대지수 |
| 행안부 무인민원발급기정보 | 2026-10-03 수집, 고유 기기 기록 5,803건 | 사용 여부와 접근성 기능 제공 표시 |
| 조달청 나라장터쇼핑몰 품목정보 | 2025-01~2026-09 등록 397행, 납품요구 상세 1,494행 | 계약·물품 등록과 납품요구의 접수·변경 |
| 과거 NIA 우선구매 검증 목록 집계 | 2026-09-30 기록의 771개 모델에 관한 집계 14개 | 당시 목록의 등록번호 연도·기업유형·제품분류 구성 |
| [NIA 배리어프리 키오스크 위치 API `15157403`](https://www.data.go.kr/data/15157403/openapi.do) | **사용자 결정으로 조회 보류** | 이번 분석에 포함하지 않음 |

보고서의 디지털정보화 100개 값은 KOSIS와 대조하는 자료이므로 240개와 합쳐 독립 관측 수로 세지 않는다. 과거 검증 목록과 위치 API도 서로 다른 자료다. 검증 모델 수, 설치 기기 수, 납품요구 수, 이용자 연간 지수를 하나의 패널로 합치지 않았다.

조달청·행안부·KOSIS는 모두 실제 인증과 수집을 완료했다. `전체 수집`은 명시한 조회조건에서 API가 반환하는 자료를 모두 받았다는 뜻이며, 현장의 모든 기기나 전체 시장 거래를 포괄한다는 뜻은 아니다. 서비스 명세와 신청 경로는 [docs/10-digital-inclusion-api-guide.md](10-digital-inclusion-api-guide.md)에 있다. 공식 데이터 출처는 [조달청 API](https://www.data.go.kr/data/15129471/openapi.do), [행안부 API](https://www.data.go.kr/data/15154774/openapi.do), 아래 KOSIS 통계표다.

<a id="policy-timeline"></a>
### 어떤 정책의 전후인가

디지털포용법은 **2026-01-22 시행**됐다. 모든 접근성 의무가 이날 새로 생긴 것은 아니다. 제조·임대 의무, 설치·운영 의무, 민간 웹·앱의 노력의무를 구분해야 한다. 검증 제품 모델 수 역시 법 전체의 효과를 대표하지 않는다. [법률 원문](https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq=268533), [민간 웹·앱 제19조](https://www.law.go.kr/LSW/lsLinkCommonInfo.do?lsJoLnkSeq=1031809803)

| 날짜 | 사건 | 비교에 미치는 영향 |
|---|---|---|
| 2025-01-21 | 법 제정·공포 | 시행 전에도 기업이 대응했을 수 있다 |
| 2025-03-27 | 기존 지능정보화 기본법의 설치·운영 의무 도입 | 제조·임대 의무와 별도로 이어지는 정책 |
| 2025-10-20 | 검증기준 개정 | 등록 수요·처리 일정에 영향을 줄 수 있는 경쟁 사건 |
| 2026-01-22 | 법 시행, 대기업·중견기업 제조·임대 의무 | 1월 전체를 사후로 분류하면 시행 전 21일이 섞인다 |
| 2026-01-28 | 장애인차별금지법의 키오스크 편의 조치 전면 적용 | 제조 의무 6일 뒤 수요 측 정책이 겹친다 |
| 2026-04-20 | 구 검증기준 적용 가능한 신청 마감 | **발급 마감이 아니다.** 이후 발급량에도 영향을 줄 수 있다 |
| 2026-04-22 | 대기업·중견기업 계도 종료 | 법정 시행일과 행정 집행 일정을 구분해야 한다 |
| 2026-07-22 | 중기업 제조·임대 의무 | 중소기업 전체를 미처치 비교군으로 둘 수 없다 |
| 2027-01-22 | 소기업·소상공인 제조·임대 의무 예정 | 분석 기준일 현재 미래 사건이다 |

시차 적용과 계도는 [정부 발표](https://www.korea.kr/news/policyNewsView.do?newsId=148958373)·[시행령](https://www.law.go.kr/lsInfoP.do?lsiSeq=282439), 장차법 조치는 [복지부 발표](https://www.mohw.go.kr/board.es?act=view&bid=0027&list_no=1487865&mid=a10503000000), 검증기준은 [2025년 고시](https://www.law.go.kr/LSW/admRulLsInfoP.do?admRulSeq=2100000266100)·[2026년 고시 부칙](https://www.law.go.kr/LSW/admRulLsInfoP.do?admRulSeq=2100000273422)에서 확인했다. 기계 판독용 일정과 출처는 [analyses/digital-inclusion/data/policy_events.csv](../analyses/digital-inclusion/data/policy_events.csv)에 있다.

제조자는 검증기준 충족 외에 직원 호출·실시간 음성안내 기능 지원 방식으로도 대응할 수 있다. 따라서 검증 모델 증가를 제조 의무 준수율 증가로 해석할 수 없다. [시행령 제15조제2항](https://www.law.go.kr/LSW/lsLinkCommonInfo.do?chrClsCd=010202&lspttninfSeq=197967)

<a id="digital-baseline"></a>
## 2. 이용자 측의 시행 전 기준선

### 통계표와 비교 기준

KOSIS 기관 ID는 `127`, 항목은 `1`인 비율, 분류 차원은 `15110BK8`의 계층별 구분이다. 네 표 모두 2014~2025년 12개 연도와 장애인·고령층·저소득층·농어민·취약계층 평균을 제공한다.

| 통계표 | 지표 | 기간 | 관측값 |
|---|---|---|---:|
| [`DT_12017N008`](https://kosis.kr/statHtml/statHtml.do?orgId=127&tblId=DT_12017N008) | 디지털정보화 종합 | 2014~2025 | 60 |
| [`DT_12017N009`](https://kosis.kr/statHtml/statHtml.do?orgId=127&tblId=DT_12017N009) | 접근 | 2014~2025 | 60 |
| [`DT_12017N0010`](https://kosis.kr/statHtml/statHtml.do?orgId=127&tblId=DT_12017N0010) | 역량 | 2014~2025 | 60 |
| [`DT_12017N0011`](https://kosis.kr/statHtml/statHtml.do?orgId=127&tblId=DT_12017N0011) | 활용 | 2014~2025 | 60 |

각 지수는 **해당 연도 일반국민을 100으로 둔 상대 수준**이다. 100점 만점의 성공률도, 100을 상한으로 하는 점수도 아니다. 변화 단위는 지수 포인트다. 일반국민의 수준이 움직여도 상대지수가 달라질 수 있어 취약계층의 절대 능력이 같은 폭으로 높아졌다고 해석하지 않는다. 취약계층 평균은 인구 규모를 고려한 **가중평균**이며, 독립적인 다섯 번째 조사집단이나 단순평균으로 취급하지 않는다.

네 표의 주석에 따르면 **2016년부터 기존 정보화·스마트정보화로 분리 산출하던 지표를 디지털정보화 지표로 통합**했고 명칭도 바뀌었다. 고령층 기준은 2015년까지 만 50세 이상에서 2016년부터 **만 55세 이상**으로 조정됐다. 따라서 주 비교는 **2016~2025년 200개 값**으로 제한하고, 2014~2015년 40개 값은 원자료에 보존했다. [KOSIS 종합 통계표](https://kosis.kr/statHtml/statHtml.do?orgId=127&tblId=DT_12017N008)

2016년 이후 20개 계열 모두 공통기간의 숫자 관측이 있지만, 모든 연도의 표본·문항·가중치가 같다는 뜻은 아니다. 아래 변화는 **조사구성 변화를 보정하지 않은 공표값의 차이**다. 상대지수로 원점수를 역산하지 않았다.

<a id="overall-trends"></a>
### 집단별 종합지수

| 집단·집계 | 2016 | 2021 | 2024 | 2025 | 2016→2025 차이 | 연평균 포인트 변화 | 2024→2025 차이 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 장애인 | 65.4 | 81.7 | 83.5 | 84.1 | +18.7 | +2.08 | +0.6 |
| 고령층 | 54.0 | 69.1 | 71.4 | 71.8 | +17.8 | +1.98 | +0.4 |
| 저소득층 | 77.3 | 95.4 | 96.5 | 97.0 | +19.7 | +2.19 | +0.5 |
| 농어민 | 61.1 | 78.1 | 80.0 | 80.6 | +19.5 | +2.17 | +0.6 |
| 취약계층 가중평균 | 58.6 | 75.4 | 77.5 | 77.9 | +19.3 | +2.14 | +0.4 |

연평균 변화는 `(2025년 값 − 2016년 값) ÷ 9년`이다. 관측값은 10개지만 연도 간격은 9개이며, 복리 증가율이나 회귀모형의 추세 계수가 아니다. 모든 집단의 종합 공표지수가 시행 전부터 높아졌으므로 향후 2026년 값이 상승해도 그 전체를 법 효과로 돌릴 수 없다. 원수치와 계산은 [analyses/digital-inclusion/outputs/kosis_trends_2026-10-03.csv](../analyses/digital-inclusion/outputs/kosis_trends_2026-10-03.csv)에 있다.

<a id="disability-trends"></a>
### 장애인의 접근·역량·활용

| 장애인 지표 | 2016 | 2021 | 2024 | 2025 | 2016→2025 차이 | 2021→2025 차이 | 2024→2025 차이 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 종합 | 65.4 | 81.7 | 83.5 | 84.1 | +18.7 | +2.4 | +0.6 |
| 접근 | 88.1 | 95.6 | 98.1 | 98.1 | +10.0 | +2.5 | 0.0 |
| 역량 | 49.8 | 74.9 | 76.1 | 77.0 | +27.2 | +2.1 | +0.9 |
| 활용 | 64.6 | 81.5 | 83.7 | 84.3 | +19.7 | +2.8 | +0.6 |

접근은 기기 보유·인터넷 접속, 역량은 이용 능력, 활용은 실제 이용 양상에 관한 상대 수준이다. 2025년 장애인의 일반국민 기준과의 차이는 **종합 15.9, 접근 1.9, 역량 23.0, 활용 15.7 지수 포인트**다. 기기 접근 지수가 높다는 사실만으로 웹·앱·키오스크를 독립적으로 이용할 수 있다고 판단하지 않는다. [NIA 2025 디지털정보격차 실태조사](https://www.nia.or.kr/site/nia_kor/ex/bbs/View.do?cbIdx=81623&bcIdx=29168&parentSeq=29168), 표2~5·본문 21~27쪽

장애인 역량의 2016→2021 차이는 +25.1, 2021→2025 차이는 +2.1 지수 포인트다. 서로 다른 길이의 기간이며 표본·일반국민 분모·정책 기여를 분리하지 않았다. 특정 시점에 개선 속도가 유의하게 바뀌었다는 검정은 하지 않았다.

2025년 보고서의 장애인 조사 대상은 **7~69세, 지체·뇌병변·시각·청각/언어 장애인**이다. 전체 장애인이나 70세 이상을 대표하지 않는다. 반올림된 집계값으로 차이를 계산했으며 표본 구성·조사설계 변동을 보정하거나 통계적 유의성을 판정하지 않았다.

<a id="latest-gaps"></a>
### 2025년 남은 상대 격차

| 집단·집계 | 접근 지수 | 역량 지수 | 활용 지수 | 역량의 일반국민 기준과 차이 |
|---|---:|---:|---:|---:|
| 장애인 | 98.1 | 77.0 | 84.3 | 23.0 |
| 고령층 | 95.4 | 56.2 | 75.6 | 43.8 |
| 저소득층 | 99.8 | 94.1 | 98.5 | 5.9 |
| 농어민 | 97.2 | 72.4 | 80.5 | 27.6 |
| 취약계층 가중평균 | 96.6 | 65.9 | 80.5 | 34.1 |

고령층 역량지수는 일반국민 기준과 43.8포인트 차이가 난다. 후속 이용자 분석에서 역량·과업 수행을 함께 봐야 한다는 근거로 읽을 수 있다. 집단마다 연령·자격 범위가 다르고 중복도 가능하므로, 연령 표준화된 정책 성과 비교나 독립 대조군으로 사용하지 않는다. 모두 포용 정책과 관련된 집단이다. [analyses/digital-inclusion/outputs/kosis_latest_gaps_2026-10-03.csv](../analyses/digital-inclusion/outputs/kosis_latest_gaps_2026-10-03.csv)

<a id="web-baseline"></a>
## 3. 민간 웹 접근성의 시행 전 공표점수

| 조사연도 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 민간 웹 접근성 평균 | 53.7 | 60.7 | 60.8 | 60.9 | 65.8 | 66.7 | 70.4 |

2024→2025 차이는 **+3.7점**이다. 동일 사이트의 개선량이 아니라 공표 평균점수의 차이다. 2025년 표본은 8개 업종의 민간 웹사이트 1,000개이며 PC 환경에서 평가했다. KWCAG 평가기준·배점·표본 변화의 영향을 분리하지 못했으므로 기간 전체를 동일한 척도의 추세로 단정하지 않는다. 공공 웹·모바일 앱·키오스크 결과로 일반화할 수 없다. [NIA 웹 접근성 보고서](https://www.nia.or.kr/site/nia_kor/ex/bbs/View.do?cbIdx=99873&bcIdx=29170&parentSeq=29170), [2024년 조사 발표](https://www.korea.kr/briefing/pressReleaseView.do?newsId=156681128)

**2026년 3월 발표된 결과라도 조사연도는 2025년이다.** 이용자·웹 연간 통계에는 시행 후 관측이 없다. KOSIS의 최종수정일이 2026년인 셀도 조사연도를 기준으로 분류했다. [2025년 조사 결과 발표](https://www.korea.kr/briefing/pressReleaseView.do?newsId=156751063)

<a id="mois-status"></a>
## 4. 무인민원발급기의 현재 접근성 기능

### 분모와 수집 완전성

분모는 기기 고유키 `OPN_ATMY_GRP_CD + MNG_NO`가 확인되고 사용 여부가 `사용`으로 기재된 **5,800건**이다. 전체 5,803건 중 나머지 3건은 `미사용`이며 사용 여부 미상은 없다. `I`·`U` 갱신구분만 관측했고 응답에 `D` 표시는 없었다. 이 사실만으로 삭제 이력이 제공되지 않는다고 결론 내리지는 않는다.

첫 페이지 방식 수집에서는 5,803행의 고유키가 5,768개였다. 페이지 경계에서 35행이 반복돼 단순 중복 제거로는 누락을 배제할 수 없었다. **230개 개방기관으로 나누고, 100건을 넘는 기관은 겹치지 않는 갱신시각 구간으로 나눠 재수집**했다. 최종 231개 분할의 합계·고유키 수·API 총건수가 모두 5,803으로 일치했고, 종료 시 무필터 총건수도 재확인했다.

분할 부모를 포함한 응답 232개의 해시·기관 조건·시각 범위와 CSV 내용을 대조했다. 다만 여러 요청에 걸친 수집이므로 데이터베이스의 한 시점 상태를 보장하는 트랜잭션 스냅샷은 아니다. [analyses/digital-inclusion/data/mois_manifest_2026-10-03.json](../analyses/digital-inclusion/data/mois_manifest_2026-10-03.json), [analyses/digital-inclusion/data/mois_devices_2026-10-03.csv](../analyses/digital-inclusion/data/mois_devices_2026-10-03.csv)

<a id="mois-features"></a>
### 기능별 제공 표시

| 기능 | 제공·가능 | 미제공·불가능 | 미상 | 제공 비율 |
|---|---:|---:|---:|---:|
| 시각장애인용 키패드 | 5,800 | 0 | 0 | 100.00% |
| 시각장애인용 음성안내 | 5,800 | 0 | 0 | 100.00% |
| 청각장애인용 화면안내 | 5,800 | 0 | 0 | 100.00% |
| 점자라벨 부착 | 5,800 | 0 | 0 | 100.00% |
| 이어폰 소켓 | 5,799 | 1 | 0 | 99.98% |
| 촉각 전자모니터 | 1,550 | 4,250 | 0 | 26.72% |
| 화면 확대 | 5,799 | 1 | 0 | 99.98% |
| 휠체어 사용자 조작 | 5,238 | 562 | 0 | 90.31% |

분모는 모두 사용 기재 5,800건이다. `제공`과 `미제공`을 부분 문자열로 판별하지 않고 필드별 정확한 값으로 구분했다. 미상을 미제공으로 바꾸지 않았으며 이번 자료의 기능별 미상은 모두 0건이다. 네 기능의 100%는 원응답에 그렇게 기재돼 있음을 확인했고, 조회조건에 기능 제공 여부 필터를 넣지 않았다. [analyses/digital-inclusion/outputs/mois_features_2026-10-03.csv](../analyses/digital-inclusion/outputs/mois_features_2026-10-03.csv), [analyses/digital-inclusion/outputs/mois_raw_value_frequencies_2026-10-03.csv](../analyses/digital-inclusion/outputs/mois_raw_value_frequencies_2026-10-03.csv)

**휠체어 조작 불가능 562건은 우선 현장 확인할 후보**다. 실제 접근 동선, 높이, 작동 여부, 보조인력은 확인하지 않았다. 촉각 모니터가 없다고 위법·부적합 기기로 판정할 수 없으며, 여덟 기능을 합쳐 법 준수율을 만들지도 않는다.

<a id="mois-regions"></a>
### 지역별 차이와 행정구역 개편

지역 집계는 설치 위치의 `ROAD_SGG_CD`를 사용했다. `OPN_ATMY_GRP_CD`는 수집 분할·고유키에 쓰는 개방기관 코드이며 설치지역을 대신하지 않는다. 관측한 시군구 코드 259개도 코드값의 종류 수이지 현재 자치단체 수가 아니다.

`12` 접두어 기록 601건의 원주소를 확인했을 때 600건의 첫 토큰은 `전남광주통합특별시`, 1건은 `강진군`이었고 모두 같은 광역 기관코드가 기재돼 있었다. 행안부는 **2026-07-01 전남·광주 통합 출범**을 안내한다. 과거의 17개 시도 명칭표를 그대로 적용하면 잘못 분류할 수 있어 지역 전후 비교에는 행정구역 개편을 반영해야 한다. [행안부 통합 안내](https://www.mois.go.kr/frt/bbs/type010/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000008&nttId=126845)

아래는 설치 시군구 코드의 앞 두 자리로 묶고, 원주소에서 가장 많이 나온 첫 행정구역 토큰을 표시명으로 사용한 결과다. 전체 법정 코드표와의 일치 검증은 하지 않았다. 비율의 분모는 지역별 사용 기재 기록이며 두 기능의 미상은 모두 0건이다.

| 코드 | 자료의 지역 표시명 | 사용 기록 | 휠체어 조작 가능 | 촉각 모니터 제공 |
|---|---|---:|---:|---:|
| 11 | 서울특별시 | 772 | 92.36% | 33.81% |
| 12 | 전남광주통합특별시 | 601 | 96.34% | 32.45% |
| 26 | 부산광역시 | 264 | 98.86% | 7.58% |
| 27 | 대구광역시 | 148 | 100.00% | 15.54% |
| 28 | 인천광역시 | 225 | 87.11% | 8.89% |
| 30 | 대전광역시 | 120 | 90.00% | 30.83% |
| 31 | 울산광역시 | 145 | 81.38% | 48.97% |
| 36 | 세종특별자치시 | 46 | 23.91% | 0.00% |
| 41 | 경기도 | 1,146 | 91.54% | 32.11% |
| 43 | 충청북도 | 277 | 87.73% | 32.49% |
| 44 | 충청남도 | 426 | 93.90% | 25.59% |
| 47 | 경상북도 | 493 | 89.05% | 22.92% |
| 48 | 경상남도 | 490 | 91.43% | 17.96% |
| 50 | 제주특별자치도 | 85 | 56.47% | 11.76% |
| 51 | 강원특별자치도 | 301 | 89.70% | 29.24% |
| 52 | 전북특별자치도 | 261 | 79.31% | 21.84% |

세종 표시명 묶음은 휠체어 조작 가능 11건·불가능 35건, 제주 묶음은 가능 48건·불가능 37건으로 기재돼 있다. 전국 평균에 가려지는 현장 확인 후보를 찾는 데 쓸 수 있지만, 기기 구성·관리·갱신 방식 차이를 보정하지 않았으므로 지역 정책 성과 순위로 해석하지 않는다. [analyses/digital-inclusion/outputs/mois_region_comparison_2026-10-03.csv](../analyses/digital-inclusion/outputs/mois_region_comparison_2026-10-03.csv), [analyses/digital-inclusion/data/mois_region_labels_2026-10-03.json](../analyses/digital-inclusion/data/mois_region_labels_2026-10-03.json)

<a id="mois-dates"></a>
### 수정·갱신일은 설치일이 아니다

최종수정시점은 2023-07-14~2026-09-30이고, 마지막 수정이 수집일보다 365일 넘게 앞선 사용 기록은 23건이다. 데이터갱신시점은 2026-01-16~2026-10-01이다. 둘 다 **설치일·기능 도입일이 아니므로 시행 전후 비교 축으로 사용하지 않았다.** 과거 기능·교체 이력이나 반복 스냅샷이 필요하다. 설치일이 있는 별도 자료라도 철거·삭제 기기가 빠졌다면 과거 상태를 완전히 복원할 수 없다. [analyses/digital-inclusion/outputs/mois_summary_2026-10-03.json](../analyses/digital-inclusion/outputs/mois_summary_2026-10-03.json)

<a id="pps-flow"></a>
## 5. 시행 전후 조달 요청의 흐름

### 품목 범위와 순증 지표

`무인민원발급기`라는 자연어 검색만으로는 해당 품목을 찾지 못했다. 실제 응답의 상위 분류 `컴퓨터키오스크(43211514)`를 수집하고, **증명발급기 `4321151401`·무인안내시스템 `4321151402`**를 주 분석 범위로 삼았다. 버스및차량정보안내장치는 상호작용 키오스크와 동일하게 취급하기 어려워 제외했다. 범위는 자료를 탐색한 뒤 정했으므로 사전 등록 분석이 아니다.

등록은 계약·물품 단위, 납품요구는 요구번호·변경차수·품목순번 단위의 행이다. 2025-01~2026-09의 21개 월 구간에 대해 등록·해지 포함 조회 21회와 납품요구 조회 26회가 페이지 검증을 통과했다. 탐색 호출은 이 횟수와 별개다. [analyses/digital-inclusion/data/pps_registrations_manifest.json](../analyses/digital-inclusion/data/pps_registrations_manifest.json), [analyses/digital-inclusion/data/pps_deliveries_manifest.json](../analyses/digital-inclusion/data/pps_deliveries_manifest.json)

주 지표는 **접수월 기준 납품요구 순증**이다. 최초 요구와 이후 변경·취소의 `incdecQty`·`incdecAmt`를 부호대로 합산한다. 3대 요구 후 2대를 추가하면 5대, 3대 요구를 모두 취소하면 0대다. 수량은 `대표품목`이고 단위가 `대`인 행만 합산했다. 최종 변경행의 수량을 최초 요청월로 돌리거나 요구서 전체 금액을 품목마다 중복 합산하지 않았다. [공식 활용 가이드 1.3](https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000003701083&fileDetailSn=1)

이는 구매 요청·변경 기록이다. 실제 납품 완료, 설치, 집행액 또는 접근성 검증을 측정하지 않으며 자료 창 시작 전 최초 요구의 후속 변경도 포함할 수 있다.

<a id="pps-main-comparison"></a>
### 같은 2월부터 9월까지 비교

법 시행일인 2026-01-22를 포함한 1월은 전환월로 두고 **2025년과 2026년의 2~9월**을 주 비교로 선택했다. 최신 불완결 월은 제외했다.

| 주 분석 품목 | 2025년 2~9월 | 2026년 2~9월 | 차이 |
|---|---:|---:|---:|
| 납품요구 순증 수량 | 872대 | 597대 | -275대, **-31.5%** |
| 납품요구 순증 금액 | 147.11억원 | 93.45억원 | -53.66억원, **-36.5%** |
| 변경이 관측된 요구번호 | 389개 | 327개 | -62개 |
| 관련 요구가 있는 수요기관 | 246곳 | 206곳 | -40곳 |

금액은 원 단위 합산 후 억원으로 표시했다. 이 구간의 품목 행은 모두 `대`·`대표품목`이라 수량과 금액의 범위가 같다. 수량을 나누면 **증명발급기 870→596대, 무인안내시스템 2→1대**로 증명발급기가 대부분이다. 전체 키오스크 시장의 변화로 일반화하기 어렵다. [analyses/digital-inclusion/outputs/pps_summary.json](../analyses/digital-inclusion/outputs/pps_summary.json), [analyses/digital-inclusion/outputs/pps_monthly.csv](../analyses/digital-inclusion/outputs/pps_monthly.csv), [analyses/digital-inclusion/outputs/pps_category_monthly.csv](../analyses/digital-inclusion/outputs/pps_category_monthly.csv)

<a id="pps-period-sensitivity"></a>
### 비교 기간에 따른 차이

| 비교 기간 | 2025년 순증 수량 | 2026년 순증 수량 | 변화율 |
|---|---:|---:|---:|
| 2~9월 · 주 비교 | 872대 | 597대 | -31.5% |
| 1/22~9/30 · 같은 날짜 범위 | 930대 | 716대 | -23.0% |
| 1~9월 · 전환월 포함 | 1,051대 | 928대 | -11.7% |
| 2~6월 · 중기업 의무 적용 전 구간 | 733대 | 524대 | -28.5% |

1월 전체 순증은 **2025년 179대, 2026년 331대**다. 2026년 1월 중 시행 전인 **1~21일이 212대**, **22~31일이 119대**였다. 1월을 포함하면 감소 폭이 작아지는 이유이며, 월 전체를 시행 후로 분류해서는 안 된다. 1/22~9/30의 금액은 155.16→112.03억원으로 27.8% 감소했다.

한 구간의 변화율만 유일한 결론으로 제시하지 않는다. 어느 비교도 예산 주기, 기존 수요, 다른 접근성 정책, 검증기준 변경과 법의 영향을 분리한 추정치는 아니다.

<a id="pps-registrations"></a>
### 등록 행과 신규 제품 수의 차이

| 2025-01~2026-09 등록 자료 | 계약·물품 등록 행 | 고유 물품 ID |
|---|---:|---:|
| 컴퓨터키오스크 전체 | 397 | 104 |
| 증명발급기 | 91 | 32 |
| 무인안내시스템 | 12 | 4 |
| 버스및차량정보안내장치 | 294 | 68 |

주 분석 범위는 **등록 103행·고유 물품 ID 36개**다. 같은 2~9월에 등록이 관측된 고유 물품 ID는 2025년 17개, 2026년 30개였다. 계약 갱신·반복 등록이 섞일 수 있어 최초 출시나 최초 NIA 검증 제품 수로 해석하지 않는다. [analyses/digital-inclusion/outputs/pps_registrations_monthly.csv](../analyses/digital-inclusion/outputs/pps_registrations_monthly.csv), [analyses/digital-inclusion/outputs/pps_suppliers.csv](../analyses/digital-inclusion/outputs/pps_suppliers.csv)

주 분석 등록 행의 기업구분은 모두 `중소기업`이었다. 계약업체와 제조사가 같다고 단정할 수 없고, 중기업·소기업 및 시행 당시 규모도 구분하지 못한다. 따라서 대기업·중견기업 대 중소기업 비교를 이 표본만으로 실행할 수 없다.

<a id="archived-registry"></a>
## 6. 과거 NIA 검증 제품 목록에서 확인한 구성

이 절은 **2026-09-30에 작성된 기존 제안 문서의 집계를 2026-10-02에 재계산한 결과**다. 당시 공식 사이트의 기본·목록·www 주소 재요청이 모두 HTTP 400을 반환했다. 신규 수집 완료나 현재 목록으로 표시하지 않는다. 원본 HTML은 저장소에 없으며 근거는 [docs/05-policy-effect-case-proposals.md](05-policy-effect-case-proposals.md#42-우선구매-검증-목록-세부-2026-09-30-조회), [당시 목록 출처](https://kioskui.or.kr/index.do?menu_id=00000830), [analyses/digital-inclusion/data/archived_registry_metadata.json](../analyses/digital-inclusion/data/archived_registry_metadata.json)에 남겼다.

| 등록번호의 연도 | 당시 목록의 모델 수 | 전체 771건 중 비중 |
|---|---:|---:|
| 2023 | 3 | 0.4% |
| 2024 | 39 | 5.1% |
| 2025 | 265 | 34.4% |
| 2026 | 464 | 60.2% |

2026년 표기 모델은 2025년 표기보다 **199건, 산술적으로 75.1% 많다.** 그러나 2026년은 7월 30일 발급분까지 확인한 부분집계이고 1월 1~21일도 포함할 수 있다. **동일 기간 증가율도 정확한 시행 전후 차이도 아니다.** 취소·만료·철회·갱신을 포함한 전체 최초 발급 이력도 검증하지 못했다. 비중의 합은 반올림으로 100%와 다를 수 있다.

2024년 표기 39건과 2025년 표기 265건 사이에도 226건 차이가 있다. 확정된 연간 성장률은 아니지만 2026년 값만 떼어 정책 반응으로 해석해서는 안 되는 이유다. 같은 기간의 최초 발급 이력이 필요하다.

<a id="archived-composition"></a>
### 기업유형과 제품분류의 집중

| 당시 목록의 구성 | 모델 수 | 비중 | 분석상 의미 |
|---|---:|---:|---|
| 대기업·중견기업 보유 | 162 | 21.0% | 기업 수가 아니라 모델 수다 |
| 중소기업 보유 | 591 | 76.7% | 중기업·소기업을 구분할 수 없어 7월 이후 처치가 섞인다 |
| 비영리·기타 | 1 | 0.1% | 별도 분류로 유지한다 |
| 기업유형 미분류 | 17 | 2.2% | 규모를 임의로 채우지 않는다 |
| 무인주차정산기 | 349 | 45.3% | 생활 주문·결제 경험 전체를 대표하지 않는다 |
| 무인주문기 | 93 | 12.1% | 제품군별 수요가 다르다 |
| 상위 5개 제품분류 합계 | 601 | 78.0% | 주차·주문·금융·도서·민원; 나머지 분류 170건 |

분모는 모두 771개 모델이다. 기업유형과 제품분류는 별개 구성이므로 표 전체를 더하지 않는다. 목록 보유업체가 법상 제조·임대 의무 당사자인지도 확인해야 한다. 등록 모델 수를 설치 대수로 바꾸거나 전체 키오스크 보급률의 분자로 사용하지 않는다.

<a id="interpretation-limits"></a>
## 7. 정책 효과를 판단하기 위해 남은 조건

| 질문 | 현재 확인한 내용 | 추가로 필요한 조건 |
|---|---|---|
| 이용자의 디지털 이용 수준이 달라졌나 | 2016~2025년 장기 기준선 확인 | 2026년 이후 조사 결과, 측정기준·모집단 변화 확인 |
| 웹 접근성이 좋아졌나 | 시행 전 공표 평균은 상승 | 평가기준·배점·표본의 연결과 시행 후 관측 |
| 공공 발급기에 어떤 기능이 있나 | 사용 5,800건의 8개 기능 제공 표시 확인 | 실제 작동·이용 경험, 기기별 기능·교체·삭제 이력 |
| 시행 이후 조달 요청이 늘었나 | 선택한 두 품목의 비교 구간에서 순증 수량·금액은 감소 | 다른 품목·민간시장·예산 주기 등 비교 자료 |
| 검증 제품 공급이 늘었나 | 과거 목록의 연도·기업·제품 구성 재계산 | 최초 검증일과 갱신·취소·만료·철회 이력 |
| 법이 이 변화를 만들었나 | **현재 자료로 인과효과 판단 불가** | 시행 당시 제조사 규모·역할·영업 여부, 독립 모집단, 타당한 비교집단과 경쟁 정책을 구분할 설계 |

기업 규모별 비교는 2026년 6월까지로 제한해 검토할 수 있지만, 독립 모집단·사전 영업 여부·처치 당시 기업규모를 확인하기 전에는 미관측 기업의 사전 값을 0으로 채우지 않는다. 검증 목록 밖의 업체가 빠지는 표본 선택 문제도 남아 있다. 신청일·발급일·적용 검증기준·지원사업 참여 자료는 정책 반응과 기관 처리 지연을 구분하는 데 필요하다.

2025년 검증기준 개정과 시행령 완화는 실제 관련 정책 사건이므로 가짜 시행일 검정으로 부르지 않는다. 사전추세 검정이 기각되지 않아도 평행추세가 입증되는 것은 아니다. 현재 자료로 기업·월 패널이나 이중차분 정책효과를 추정하지 않았다.

행안부 기기와 조달청 거래를 잇는 설치·조달 연결키도 확인되지 않았다. 납품요구 변화가 현재 기능 차이를 만들었다고 해석하지 않는다. 이용자 연간 지수는 관측 단위가 또 다르며, 네 취약계층 모두 정책의 영향을 받을 수 있어 독립적인 미처치 대조군으로 바로 삼을 수 없다.

후속 자료의 우선순위는 **기기별 기능·교체 이력, NIA 제품 최초 검증·갱신·철회 이력, 시행 당시 제조사 규모·역할**이다. NIA **위치 API `15157403`의 조회는 사용자가 재개를 요청할 때까지 보류**하며, 제품 검증 이력 확보와 구분한다. 제공된 위치 API 가이드는 별도 API 키를 쓰는 Bearer 인증을 요구한다. 인증 안내는 [docs/10-digital-inclusion-api-guide.md](10-digital-inclusion-api-guide.md)에 있다. 정기 자동 수집은 설정하지 않았다. 후속 자료 상태는 [docs/work/W-004-main-history-data.md](work/W-004-main-history-data.md)에 기록한다.

<a id="source-reconciliation"></a>
## 8. 보고서와 KOSIS 출처를 대조한 결과

[analyses/digital-inclusion/data/baseline_indicators.csv](../analyses/digital-inclusion/data/baseline_indicators.csv)의 디지털정보화 100개 관측을 KOSIS와 동일 지표·집단·연도·단위로 대조했다. **99개가 일치하고 한 셀에서 0.1포인트 차이**가 났다. 웹 접근성 7개 값은 네 KOSIS 표의 범위 밖이므로 대조에서 제외했다.

| 불일치 셀 | 2025 NIA 보고서의 과거 수치 | 현재 KOSIS 응답 | API − 보고서 |
|---|---:|---:|---:|
| 2021년 농어민 디지털정보화 접근 | 94.8 | 94.9 | +0.1 |

2025 NIA 보고서 본문 23쪽 표3, PDF 49페이지를 화면으로 재확인했으며 텍스트 추출도 **94.8**로 같았다. 이전 CSV의 전사 오류로 보이지 않는다. KOSIS는 **94.9**, 해당 셀의 최종수정일은 `2023-06-26`이다. 공식 정정·개정 사유는 확인하지 못했다. [NIA 2025 보고서](https://www.nia.or.kr/site/nia_kor/ex/bbs/View.do?cbIdx=81623&bcIdx=29168&parentSeq=29168), [KOSIS 접근 통계표](https://kosis.kr/statHtml/statHtml.do?orgId=127&tblId=DT_12017N009)

추가로 확인한 **2021년 조사 보고서의 현재 공식 첨부파일** PDF 44페이지 표3은 농어민 접근지수를 2020년 94.8, 2021년 **94.9**로 표시한다. 본문 설명과 뒤의 세부표도 94.9로 KOSIS와 일치한다. 다만 2025년 보고서의 과거 값에 대한 공식 정정 공지는 찾지 못했고, 현재 첨부파일이 최초 게시 당시 파일과 같은지도 검증하지 않았다. [NIA 2021 보고서 게시물](https://www.nia.or.kr/site/nia_kor/ex/bbs/View.do?bcIdx=24287&cbIdx=81623)

**기존 보고서 CSV를 수정하지 않고 양쪽 출처를 보존했다.** 장기 비교는 KOSIS 계열만 사용하며 보고서 계열과 이어 붙이지 않는다. 이 차이는 농어민 접근지수의 2021년을 포함한 변화량에 0.1포인트 영향을 주지만, 2016→2025 끝점 비교와 2025년 수준에는 영향을 주지 않는다.

대조 전수 결과는 [analyses/digital-inclusion/outputs/kosis_report_comparison_2026-10-03.csv](../analyses/digital-inclusion/outputs/kosis_report_comparison_2026-10-03.csv), 원문 확인 기록은 [analyses/digital-inclusion/data/source_reconciliation_kosis_2026-10-03.json](../analyses/digital-inclusion/data/source_reconciliation_kosis_2026-10-03.json)에 있다. 별도로 디지털정보격차 보고서 내부의 활용 **원점수** 불일치도 확인해 원점수 역산을 제외하고 공표 상대지수만 사용했다. 이 판단은 [analyses/digital-inclusion/data/source_manifest_baseline.json](../analyses/digital-inclusion/data/source_manifest_baseline.json)에 남겼다.

<a id="reproduction"></a>
## 9. 재현과 검증

저장된 CSV·메타데이터·수집 명세로 재분석하며 다음 명령에는 API 키와 네트워크가 필요 없다.

```sh
python3 analyses/digital-inclusion/analyze.py
python3 analyses/digital-inclusion/kosis_analyze.py --snapshot 2026-10-03
python3 analyses/digital-inclusion/mois_analyze.py --snapshot 2026-10-03
python3 analyses/digital-inclusion/pps_analyze.py
```

| 분석 | 입력·검증 범위 | 주요 출력 |
|---|---|---|
| 보고서 기준선·과거 검증 목록 | 공식 보고서 관측 107개와 과거 집계 14개; 원문 위치·다운로드 주소·SHA256·조사 모집단 기록 | [analyses/digital-inclusion/outputs/summary.json](../analyses/digital-inclusion/outputs/summary.json), [analyses/digital-inclusion/outputs/baseline_changes.csv](../analyses/digital-inclusion/outputs/baseline_changes.csv), [analyses/digital-inclusion/outputs/registry_composition.csv](../analyses/digital-inclusion/outputs/registry_composition.csv) |
| KOSIS | 메타데이터 16회·통계자료 4회의 정상 응답 20개; 선언된 연도 × 항목 × 분류 240셀과 실제 관측 일치, 중복·누락·비수치 0개 | [analyses/digital-inclusion/outputs/kosis_summary_2026-10-03.json](../analyses/digital-inclusion/outputs/kosis_summary_2026-10-03.json) 및 장기 변화·연도 차이·최신 격차·보고서 대조 CSV |
| 행안부 | 분할 조회 완전성·고유키·원문 해시·원문 필드와 기능별 분모 검증 | [analyses/digital-inclusion/outputs/mois_summary_2026-10-03.json](../analyses/digital-inclusion/outputs/mois_summary_2026-10-03.json) 및 기능·지역 집계 CSV |
| 조달청 | 월별·페이지별 건수, 날짜·품목 범위, 중복 식별키, 변경·취소·단위 처리와 입력 해시 검증 | [analyses/digital-inclusion/outputs/pps_summary.json](../analyses/digital-inclusion/outputs/pps_summary.json) 및 월별·품목별·등록 집계 CSV |

KOSIS 원자료가 로컬에 있으면 20개 응답의 해시와 240개 셀의 값·단위·분류명·수정일·연간 주기도 대조한다. 수집 조건과 원문 해시는 [analyses/digital-inclusion/data/kosis_manifest_2026-10-03.json](../analyses/digital-inclusion/data/kosis_manifest_2026-10-03.json), 분류코드·주석은 [analyses/digital-inclusion/data/kosis_metadata_2026-10-03.json](../analyses/digital-inclusion/data/kosis_metadata_2026-10-03.json), 전체 값은 [analyses/digital-inclusion/data/kosis_digital_divide_2026-10-03.csv](../analyses/digital-inclusion/data/kosis_digital_divide_2026-10-03.csv)에 있다.

2026-10-03에는 조달청·행안부를 먼저 수집하고, 당시 미설정이던 KOSIS 키가 추가된 뒤 같은 날 네 통계표를 수집했다. 조달청·행안부는 정상 응답 `00`·`0`, KOSIS는 정상 통계 응답으로 인증을 확인했다. 조달청·행안부의 URL 인코딩된 키는 수집기에서 한 번 디코딩한 뒤 요청을 인코딩했으며 `.env` 값을 변경하지 않았다. 실제 키·인증 URL은 산출물에 넣지 않았다. 인증 기록은 [analyses/digital-inclusion/data/authentication_check_2026-10-03.json](../analyses/digital-inclusion/data/authentication_check_2026-10-03.json), [analyses/digital-inclusion/data/authentication_check_kosis_2026-10-03.json](../analyses/digital-inclusion/data/authentication_check_kosis_2026-10-03.json)에 있고, 인증 처리는 가짜 키를 사용하는 오프라인 테스트로 인코딩·오류·비밀값 노출 방지를 점검했다.

설계·출처 선택 규칙은 [analyses/digital-inclusion/plan.json](../analyses/digital-inclusion/plan.json), [analyses/digital-inclusion/kosis_analysis_plan.json](../analyses/digital-inclusion/kosis_analysis_plan.json)에 있다. 기존 집계를 이미 본 탐색 분석이므로 사전 등록으로 부르지 않는다. 결측을 0으로 채우거나 100 초과 지수를 잘라내지 않았고, 관측 자료의 산술 집계에 표본 신뢰구간·p값을 붙이지 않았다.

수집 실행법과 전체 출력 목록은 [analyses/digital-inclusion/README.md](../analyses/digital-inclusion/README.md), 인증 분석 작업 기록은 [docs/work/W-002-main-digital-inclusion-api.md](work/W-002-main-digital-inclusion-api.md), 추가 자료 작업 기록은 [docs/work/W-003-main-additional-data.md](work/W-003-main-additional-data.md)에 있다. 입력과 계산 출력을 분리해 후속 분석 페이지에서도 같은 결과를 사용할 수 있도록 했다.


<a id="followup-decomposition"></a>
## 10. 기관·제품별 조달 변화와 기능 조합 — 2026-10-04 추가

기존 2026-10-03 수집본을 재분석했다. API를 새로 수집하거나 비교 대상을 사전 등록한 분석은 아니다. 조달 비교 기간은 두 해 모두 2~9월, 품목 범위·변경 및 취소의 부호·단위 처리 기준은 §5와 같다. 수량은 대표품목·단위 `대`의 순증이며 금액은 해당 품목 범위의 옵션·기타 단위까지 포함한다.

### 조달 감소의 구성

기관 코드별로 기간 내 변경 기록의 존재를 비교했다. 이름이 바뀐 동일 코드는 함께 집계하고 관측 명칭을 모두 남겼다. 코드가 달라진 기관의 통폐합은 연결하지 않았다.

| 기간 내 기록 존재 | 기관 수 | 2025년 순증 수량 | 2026년 순증 수량 | 차이 |
|---|---:|---:|---:|---:|
| 두 해 모두 | 101 | 612 | 395 | -217 |
| 2025년에만 | 145 | 260 | 0 | -260 |
| 2026년에만 | 105 | 0 | 202 | +202 |
| 전체 | 351개 코드의 합집합 | 872 | 597 | -275 |

**감소는 기관 수 변화만의 결과가 아니다.** 양쪽에 기록이 있는 기관에서도 217대 감소했다. 다만 이 분류는 해당 기간의 조달 변경 기록 유무이며 신규 구매기관·구매 중단·기관 폐쇄를 뜻하지 않는다. 0은 완전 수집한 조회 범위에 기록이 없다는 뜻이다. 취소로 순증이 0이 되어도 기록이 있으면 관측 기관이다.

| 감소 상위 기관 | 2025년 | 2026년 | 차이 |
|---|---:|---:|---:|
| 강남구 | 40 | 4 | -36 |
| 영등포구 | 33 | 5 | -28 |
| 성동구 | 25 | 1 | -24 |
| 마포구 | 24 | 2 | -22 |
| 은평구 | 21 | 2 | -19 |

이 다섯 기관은 합계 129대 감소했다. 전체 감소 기관의 감소분은 600대, 증가 기관의 증가분은 325대다. 따라서 다섯 기관은 감소분 600대의 21.5%이며, 순감소 275대를 분모로 하면 46.9%다. 서로 다른 분모를 혼동하지 않는다. 증가 사례는 남양주시 1→15대, 성남시 수정구 0→13대 등이다.

제품 식별번호별 감소 상위는 `24422601` 142→69대(-73), `24362786` 131→61대(-70), `24362785` 82→39대(-43)다. 원자료 이름은 각각 TAPI-9320B, AT-K300E, AT-K300이며 모두 시청각장애인겸용 무인민원발급기라는 명칭을 포함한다. **제품명은 검증·법 준수 여부의 증거가 아니다.** 같은 품목 분류에는 IS-2000L 통합민원발급기(195→154대)도 포함돼 있어 전체 조달량을 배리어프리 무인기만의 수량으로 해석하지 않는다. 제품 ID 변경·후속 모델 대체 여부는 확인하지 않았다.

전체 기관·제품과 금액 분해: [analyses/digital-inclusion/outputs/pps_institutions_comparison.csv](../analyses/digital-inclusion/outputs/pps_institutions_comparison.csv), [analyses/digital-inclusion/outputs/pps_products_comparison.csv](../analyses/digital-inclusion/outputs/pps_products_comparison.csv), [analyses/digital-inclusion/outputs/pps_institution_cohorts.csv](../analyses/digital-inclusion/outputs/pps_institution_cohorts.csv).

### 감소 상위 기관의 공식 이력 대조

감소 상위 다섯 기관을 사후 선택한 탐색 조사이며 대표 표본이 아니다. 공식 본문을 확인한 자료와 검색 결과만 있는 후보를 구분했다.

- **강남구:** 2025-05-12 공지는 5월 15·16·19·20일 역삼세무서·신사역·강남세무서·구청의 교체 및 설치 작업을 예고한다. [정부24 공식 공지](https://www.gov.kr/portal/ntcItm/115093?srchTxt=&srchType=muin)
- **마포구:** 2025-04-28 공지는 5월 1·2·7일 동주민센터·역사·세무서의 교체 및 설치 작업을 예고한다. 장소 명칭 수를 기기 수로 바꾸지 않았다. [정부24 공식 공지](https://www.gov.kr/portal/ntcItm/114850?pageIndex=2&srchType=muin)
- **영등포·성동구:** 관련 교체·구매 자료의 검색 발췌를 찾았으나 원문 열람이 실패해 확정 근거에서 제외했다. **은평구:** 대응 원문 미확보.

확인된 사실은 두 기관에 **시행 전 교체·설치 예정 기록이 존재한다**는 것이다. 이로부터 전년도 교체 수요가 이후 조달 흐름에 영향을 줬을 가능성을 제안할 수 있으나, 공지는 완료 실적이 아니며 조달 요구서·제품 ID·기기 관리번호와 연결되지 않았다. 2026년 감소가 접근성 악화나 특정 법의 효과라는 결론은 낼 수 없다. 출처·확인 수준·미확인 범위는 [analyses/digital-inclusion/data/local_history_sources_2026-10-04.json](../analyses/digital-inclusion/data/local_history_sources_2026-10-04.json)에 남겼다.

### 행안부 접근성 기능의 동시 기재

사용 중으로 기재된 5,800건을 분모로 두 기능을 교차 집계했다. 미상은 별도 범주로 유지했으며 이번 두 필드에는 0건이었다.

| 휠체어 사용자 조작 | 촉각 모니터 | 기록 수 | 전체 대비 |
|---|---|---:|---:|
| 가능 | 제공 | 1,539 | 26.5% |
| 가능 | 미제공 | 3,699 | 63.8% |
| 불가능 | 제공 | 11 | 0.2% |
| 불가능 | 미제공 | 551 | 9.5% |

두 기능이 동시에 부족하게 기재된 551건은 현장 점검 후보를 찾는 데 쓸 수 있다. 8개 필드가 모두 긍정으로 기재된 기록도 1,539건이지만 **법 준수율·종합 접근성 점수·실제 이용 성공률이 아니다.** 이어폰 소켓·화면 확대가 함께 미제공인 1건도 별도 조합으로 보존했다. 시점 비교가 아닌 현황 분석이다.

출력: [analyses/digital-inclusion/outputs/mois_feature_pairs_2026-10-03.csv](../analyses/digital-inclusion/outputs/mois_feature_pairs_2026-10-03.csv), [analyses/digital-inclusion/outputs/mois_feature_patterns_2026-10-03.csv](../analyses/digital-inclusion/outputs/mois_feature_patterns_2026-10-03.csv).

재현 명령은 `python3 analyses/digital-inclusion/followup_analyze.py`다. 기존 입력 해시·수집 완전성·행안부 원문 232개를 검증하고, 기관별·제품별 합계가 원자료 합계와 같은지 확인한다. [analyses/digital-inclusion/outputs/followup_summary.json](../analyses/digital-inclusion/outputs/followup_summary.json)에 입력·출력 해시와 한계를 기록한다.

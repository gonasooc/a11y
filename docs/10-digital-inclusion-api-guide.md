# 디지털포용법 분석에 필요한 API

> 명세 확인: 2026-10-02~03 · 인증 수집 확인: 2026-10-03. 조달청·행안부·KOSIS 인증 수집을 완료했다.
> 관련 문서: [정책 효과 분석 제안](05-policy-effect-case-proposals.md) · [문서 목록](README.md)

먼저 **조달청과 행정안전부 API를 각각 활용신청하고 KOSIS 인증키를 발급**하면 된다. 조달청은 검증을 받지 않은 공급업체와 구매 실적을 보완하고, 행정안전부는 기기별 접근성 기능의 현재 상태를 측정한다. KOSIS는 법 시행 전 장기 추세와 추후 발표되는 연간 결과를 연결한다. 키만으로 과거의 접근성 상태가 복원되지는 않는다.

현재 저장소에서는 세 키의 실제 인증과 데이터 수신을 확인했다. 조달청·행안부·KOSIS 결과는 [docs/digital-inclusion-analysis.md](digital-inclusion-analysis.md)에 통합했다. 아래 신청 안내는 새 환경에서도 사용할 수 있도록 유지한다.

## 1. 발급·확인 순서

| 순서 | 신청할 서비스 | 인증·승인 | 분석에서의 역할 |
|---|---|---|---|
| 1 | [조달청_나라장터쇼핑몰 품목정보 서비스 · 15129471](https://www.data.go.kr/data/15129471/openapi.do) | 공공데이터포털 `serviceKey`. 개발·운영 자동승인, 개발계정 트래픽 1,000 | 공급업체·제조사·기업구분·품목·계약·납품요구를 연결. 공급 측 분석 보완 |
| 2 | [행정안전부_무인민원발급기정보 조회서비스 · 15154774](https://www.data.go.kr/data/15154774/openapi.do) | 공공데이터포털 `serviceKey`. 개발·운영 자동승인, 개발계정 트래픽 10,000 | 전국 무인민원발급기의 접근성 기능별 제공 비율과 지역 차이 |
| 3 | [KOSIS 공유서비스 인증키 신청](https://kosis.kr/openapi/serviceUse/serviceUseUnityReg_01Detail.do) | KOSIS 로그인 후 별도 `apiKey` 신청 | 취약계층의 디지털정보화 수준·접근·역량·활용 연간 추세 |
| 보류 | [NIA_배리어프리 키오스크 위치 정보 조회 데이터 · 15157403](https://www.data.go.kr/data/15157403/openapi.do) | LINK형. Bearer 인증 필요, 키 발급 신청 경로 미확인 | 2026-10-03 사용자 요청으로 조사·연결·수집 보류 |

공공데이터포털 인증키를 가지고 있어도 **두 서비스의 활용신청 상태를 각각 확인**해야 한다. KOSIS 키는 공공데이터포털 키와 별개다. 위 두 공공데이터포털 서비스는 무료이며 이용허락범위 제한 없음으로 표시된다. NIA 위치 데이터는 출처표시 제1유형이다.

발급받은 키는 **저장소 루트의 `.env`**에 입력한다. [.env.example](../.env.example)은 값 없이 이름과 용도만 공유하는 양식이다. 실제 값은 `.env`에만 넣으며, [.gitignore](../.gitignore)가 이 파일을 Git에서 제외한다.

아래 각 줄의 `=` 뒤에 해당 인증키를 붙여 넣는다. 기관·API 용도를 구분하도록 환경변수 이름을 정했다.

```dotenv
# 조달청: 나라장터쇼핑몰 품목정보 서비스 (15129471)
PPS_SHOPPING_MALL_SERVICE_KEY=
# 행정안전부: 무인민원발급기정보 조회서비스 (15154774)
MOIS_KIOSK_INFO_SERVICE_KEY=
# KOSIS: 디지털정보격차 통계표 조회
KOSIS_DIGITAL_DIVIDE_API_KEY=
```

조달청·행안부 항목에는 공공데이터포털의 **Decoding 인증키**, KOSIS 항목에는 **KOSIS 공유서비스 인증키**를 입력한다. 조달청과 행안부에 같은 인증키를 사용하는 경우에는 두 항목에 같은 값을 넣는다. 서비스별 활용신청은 각각 필요하다.

인증 수집기는 프로세스 환경변수를 우선 읽고, 해당 변수가 없으면 저장소 루트 `.env`를 읽는다. 현재 수집기는 Encoding 키도 한 번 디코딩해 처리하며 실제 입력된 두 Encoding 키로 정상 인증을 확인했다. `.env`를 수정할 필요는 없다. 키 저장만으로 수집이 자동 실행되지는 않으며 오프라인 분석에는 키가 필요 없다. 수집·재현 명령은 [analyses/digital-inclusion/README.md](../analyses/digital-inclusion/README.md)에 있다.

NIA는 인증 방식을 확인한 뒤 필요한 환경변수를 추가한다. 현재는 공공데이터포털 키로 호출된다고 가정하지 않는다.

## 2. 조달청: 공급업체 표본과 구매 실적

공식 페이지에 포함된 Swagger의 기본 주소와 다음 기능을 확인했다.

```text
https://apis.data.go.kr/1230000/at/ShoppingMallPrdctInfoService
  /getShoppingMallPrdctInfoList   나라장터쇼핑몰 품목 등록 내역
  /getDlvrReqDtlInfoList         나라장터쇼핑몰 납품요구상세 현황
  /getSpcifyPrdlstPrcureInfoList  특정품목조달내역
```

| 기능 | 확인한 주요 응답 필드 |
|---|---|
| 품목 등록 | `cntrctCorpBizno` 사업자등록번호, `cntrctCorpNm` 계약업체명, `prdctMakrNm` 제조사명, `entrprsDivNm` 기업구분, `prdctIdntNo` 물품식별번호, `dtilPrdctClsfcNo` 세부품명번호, `rgstDt` 등록일시, `cntrctDate` 계약일자, `cntrctBgnDate`·`cntrctEndDate` 계약기간, `prodctCertList` 제품인증목록 |
| 납품요구상세 | `dlvrReqRcptDate` 접수일, `cntrctCorpBizno` 계약업체, `corpNm` 업체명, `corpEntrprsDivNmNm` 기업구분, `prdctQty`·`prdctAmt` 물품 수량·금액, `dminsttCd` 수요기관, `dminsttRgnNm` 지역, `fnlDlvrReqYn` 최종 여부, `incdecQty`·`incdecAmt` 증감 |

등록 내역은 조회 시작·종료일, 품명·세부품명·물품규격명, 등록해지 여부로 검색할 수 있다. 실제 조회한 상위 품명 `컴퓨터키오스크(43211514)`에는 증명발급기·무인안내시스템·버스및차량정보안내장치가 섞여 있었다. 자연어 키워드 하나만으로 전체 키오스크를 포괄한다고 보지 않는다. 공식 가이드의 기업구분은 대기업·중견기업·중소기업·비영리법인및기타이며, **중기업·소기업 구분과 시행 당시 규모는 확인할 수 없었다.**

공급업체 표본은 시행 전 기간에 존재했던 업체를 먼저 고정하는 방식으로 검토한다. 시행 후 검증 제품 목록에 나타난 업체만 고르면 결과로 표본을 선택하게 된다. 다만 조달업체는 민간 시장 전체 제조사 모집단이 아니고, 계약업체와 제조사가 다를 수 있다. NIA 목록과의 명칭 매칭 결과는 사람이 확인해야 한다.

공식 가이드 1.3에서 등록 조회는 최대 12개월, 납품요구 접수일 조회는 최대 1개월이며 `regtCncelYn=Y`는 해지 품목 포함임을 확인했다. 이번에는 2025-01~2026-09를 월별로 수집했다. API의 과거자료 보존 범위가 전체 시장 이력과 같다고 검증한 것은 아니다. 납품요구는 설치 완료나 접근성 충족을 뜻하지 않는다. 변경차수별 `incdecQty`·`incdecAmt`를 접수월에 합산한 순증으로 집계했으며 `fnlDlvrReqYn`은 최종 변경차수 표시다. `prodctCertList`를 NIA 검증 여부로 확정하지 않았다. [analyses/digital-inclusion/data/pps_reference.json](../analyses/digital-inclusion/data/pps_reference.json)

## 3. 행정안전부: 접근성 기능은 있지만 설치일은 없다

```text
GET https://apis.data.go.kr/1741000/kiosk_info/installation_info
```

필수 요청값은 `serviceKey`, `pageNo`, `numOfRows`이며 한 페이지 최대 100건이다. `returnType=JSON`으로 정상 JSON 응답을 확인했다. 2026-10-02 키 없는 요청은 HTTP 401이었고, 2026-10-03 인증 수집에서는 `resultCode=0`·정상과 고유 기록 5,803건을 확인했다.

공식 Swagger에서 다음 접근성 필드를 확인했다.

| 필드 | 의미 |
|---|---|
| `FRBLND_KPD` | 시각장애인용 키패드 |
| `FRBLND_VOICE_GD` | 시각장애인용 음성안내 |
| `FRDEAF_SCRN_GD` | 청각장애인용 화면안내 |
| `BRL_LBL_ATCMNT` | 점자라벨 부착 |
| `EPHN_SCKT` | 이어폰 소켓 |
| `TCTL_ELCTNC_MONITOR` | 촉각(전자)모니터 |
| `SCRN_EXPSN_FWK` | 화면 확대 |
| `WHCHR_USER_MNPLT` | 휠체어 사용자 조작 가능 여부 |

`PWDBS_CVN_ISSUMCHN_SHP`에는 장애인편의기능정보가 있다. 이번 스냅샷에서 `OPN_ATMY_GRP_CD + MNG_NO` 조합의 고유성을 확인했다. 주소·시도코드·도로시군구코드·사용 여부도 제공한다. 페이지 경계의 중복·누락 가능성이 있어 기관별 필터와 겹치지 않는 갱신시각 구간으로 재조회한 뒤, 총건수와 고유키 수를 대조했다. 설치지역은 `ROAD_SGG_CD`를 쓰며 개방기관 코드를 위치로 대체하지 않는다.

**설치일 필드는 공개 명세에 없다.** `LAST_MDFCN_PNT`는 최종수정시점, `DAT_UPDT_PNT`는 데이터갱신시점이다. 이 날짜를 설치일이나 접근성 기능 도입일로 간주하면 안 된다. 갱신시점 조건은 변경분 수집에 유용하지만 특정 과거 날짜의 상태를 재현하는 기능으로 확인된 것은 아니다. 자료는 매일 갱신하며 2일 전 기준으로 현행화한다.

이번 분석은 사용 기재 5,800건을 분모로 기능별 제공·미제공·미상을 표시했다. 미상을 미제공으로 바꾸거나 8개 기능을 법적 적합성 판정으로 합산하지 않는다. 전후 비교에는 과거 스냅샷 또는 기능 변경 이력이 추가로 필요하다.

키 발급 후 최소 호출 예시다. 키 값은 URL 문자열에 직접 붙이지 않는다.

```sh
curl --get 'https://apis.data.go.kr/1741000/kiosk_info/installation_info' \
  --data-urlencode "serviceKey=${MOIS_KIOSK_INFO_SERVICE_KEY}" \
  --data-urlencode 'pageNo=1' \
  --data-urlencode 'numOfRows=100'
```

이 예시에서는 공공데이터포털의 **Decoding 키**를 환경변수에 넣고 `--data-urlencode`가 인코딩하도록 한다. 전체 자료 수집 시에는 `totalCount`와 페이지별 수신 건수를 검증한다.

이 curl 예시는 해당 변수가 이미 현재 셸 환경에 설정돼 있어야 한다. `.env` 파일을 자동으로 읽는 명령은 아니다.

## 4. KOSIS: 확인된 통계표 ID

기관 ID는 `127`이다. 아래 4개 공식 통계표 HTML의 `tblNm` 값을 직접 읽어 이름과 ID의 대응을 확인했다.

| 통계표 ID | 이름 |
|---|---|
| [`DT_12017N008`](https://kosis.kr/statHtml/statHtml.do?orgId=127&tblId=DT_12017N008) | 일반국민 대비 취약계층 디지털정보화 수준 |
| [`DT_12017N009`](https://kosis.kr/statHtml/statHtml.do?orgId=127&tblId=DT_12017N009) | 일반국민 대비 취약계층 디지털정보화 접근 수준 |
| [`DT_12017N0010`](https://kosis.kr/statHtml/statHtml.do?orgId=127&tblId=DT_12017N0010) | 일반국민 대비 취약계층 디지털정보화 역량 수준 |
| [`DT_12017N0011`](https://kosis.kr/statHtml/statHtml.do?orgId=127&tblId=DT_12017N0011) | 일반국민 대비 취약계층 디지털정보화 활용 수준 |

[공식 통계자료 개발가이드](https://kosis.kr/openapi/devGuide/devGuide_0201List.do)의 통계표선택 방식은 다음 주소를 쓴다.

```text
https://kosis.kr/openapi/Param/statisticsParameterData.do?method=getList
```

필수값은 `apiKey`, `orgId`, `tblId`, `objL1`, `itmId`, `prdSe`, `format`이다. 연간 자료는 `prdSe=Y`, 기간은 `startPrdDe`·`endPrdDe`로 지정한다. 이번 인증 수집에서 `orgId=127`, `itmId=1`, `objL1=ALL`, `format=json`, `jsonVD=Y`, `smblChk=Y`로 2014~2025년 전체 계층의 정상 JSON 응답을 확인했다. 실제 응답의 `PRD_SE`는 `A`였으며, 메타데이터의 연간 주기와 네 자리 수록연도를 함께 확인해 원값을 보존했다.

분류 차원은 `15110BK8`이며 네 통계표 모두 아래 코드를 사용했다.

| 분류코드 | 이름 |
|---|---|
| `15110BK8AA` | 장애인 |
| `15110BK8AD` | 고령층 |
| `15110BK8AB` | 저소득층 |
| `15110BK8AC` | 농어민 |
| `15110BK8AE` | 취약계층 평균 |

메타데이터는 `https://kosis.kr/openapi/statisticsData.do`에 `method=getMeta`와 `type=TBL/PRD/ITM/CMMT`를 지정해 조회했다. `PRD`에 `detail=Y`를 넣어 전체 수록시점을 받는다. 통계표·항목·주석을 먼저 확인한 뒤 실제 자료가 선언된 모든 셀을 포함하는지 검사한다. 구현은 [analyses/digital-inclusion/kosis_collect.py](../analyses/digital-inclusion/kosis_collect.py)에 있다.

응답의 `PRD_DE`는 조사 수록시점, `DT`는 수치, `ITM_NM`·`C1_NM` 등은 항목·분류, `UNIT_NM`은 단위, `LST_CHN_DE`는 최종수정일이다. 최종수정일을 관측연도로 사용하지 않는다. 일반국민을 100으로 둔 상대 수준이므로 성공률이나 접근성 준수율과도 다르다.

2026-10-03 실제 수록기간은 네 표 모두 **2014~2025년**이었다. 2025년까지의 자료는 2026-01-22 법 시행 이전 기준선이다. 주석에 2016년 지표 통합과 고령층 기준 변경이 있어 장기 주 비교는 2016년 이후로 한정했다. 기관별·지역별 키오스크 API와 관측 단위가 다르므로 이를 한 패널처럼 합치지 않는다.

## 5. NIA 위치 API 보류

**2026-10-03 사용자 요청으로 보류했다.** 키 발급 경로 조사·연결·수집·분석은 사용자가 재개를 요청할 때 이어간다. 아래는 보류 전에 확인한 내용이다.

포털의 공식 링크 조회 결과는 [NIA API 안내](https://www.kioskui.or.kr/index.do?menu_id=00001559)였다. 2026-10-02에는 안내 페이지가 HTTP 400을 반환하여, 샌드박스 밖 재확인에서도 열리지 않았다. 포털 설명으로 위치·기기 유형·접근성 지원·행정구역·주소·좌표 제공은 확인했다. 포털 등록일은 2026-02-06이다.

이후 사용자가 제공한 안내의 호출 주소는 `https://api.kioskux.com/openapi/v1/kiosk`였고, 첨부 가이드의 인증 절에서 `Authorization: Bearer {KIOSK_API_KEY}`를 확인했다. 키 없는 실제 요청은 HTTP 401을 반환했다. **키 발급 신청 페이지, 설치·등록일과 과거 조회 기능은 아직 확인하지 못했다.** 포털의 자동승인·심의승인 표기만으로 외부 기관의 발급 절차를 확정할 수 없다. 재개 요청이 있으면 다음 항목부터 확인한다.

1. 인증 신청 방법과 이용 조건, 호출 제한을 확인한다.
2. 기기별 고유 ID·설치일·최초 등록일·수정일·삭제 여부·좌표 및 기능 필드를 구분한다.
3. 과거 날짜 조회가 가능한지 확인하고, 안 되면 최초 수집일부터 스냅샷을 쌓는다.

지도에 등록된 기기만 포함한다면 전체 설치 대수 대비 보급률은 산출할 수 없다. 포털에 등록된 날짜는 API 공개일이지 개별 기기 설치일이 아니다. 이번 조사에서는 NIA 검증 제품 목록을 대체할 공공데이터포털 파일도 찾지 못했다.

## 6. 키 발급 후 확인할 데이터 계약

| 확인 항목 | 통과 조건 |
|---|---|
| 출처·보존 | 서비스·기능·조회조건·조회시각·공식 명세 출처와 원본 파일 해시를 보존하고 인증키는 제외 |
| 전체 수집 | 페이지 누락 없이 전체 건수와 중복을 점검; 실패 응답은 관측값 0으로 바꾸지 않음 |
| 날짜 | 설치·검증·등록·갱신·계약·납품요구·조사 연도를 구분; 과거 상태 복원 가능 여부를 별도 판정 |
| 표본·분모 | 시행 전 공급업체 표본과 비교집단, 기기 사용 여부, 결측·미상, 민간 시장 누락을 명시 |
| 정책 연결 | 기업규모가 적용일 당시의 분류인지 확인; 디지털포용법·장애인차별금지법·검증기준 변경을 구분 |

인증 수집 결과로 행안부의 현재 기능 현황과 조달청의 월별 납품요구 순증을 분석했다. 제조사 처치·대조군을 구성하는 패널과 인과효과 추정은 자료 조건을 충족하지 못해 진행하지 않았다.

## 검증 기록

- `find-docs` 절차에 따라 Context7에서 `공공데이터포털`을 검색했으나 등록된 문서가 없었다. 공식 포털·KOSIS 문서와 HTML 내 Swagger로 확인했다.
- KOSIS 인증 수집 전 Context7에서 `KOSIS`·`국가통계포털`을 조회했으나 일치하는 문서가 없어 공식 공유서비스 개발가이드와 인증 응답으로 확인했다.
- 행정안전부·조달청은 **공개 명세 확인과 선택 기능의 인증 수집 완료**다. 조달청은 품목등록·납품요구상세를 호출했으며 특정품목조달내역 기능까지 검증한 것은 아니다. [analyses/digital-inclusion/data/api_catalog.json](../analyses/digital-inclusion/data/api_catalog.json)에 명세와 검증 범위를 남겼다.
- KOSIS는 **메타데이터 16개·실자료 4개 정상 응답과 240개 관측값을 확인**했다. 기존 보고서 100셀과의 대조에서 99개가 일치하고 1개는 출처 간 차이로 남았다. NIA 위치 API는 호출 주소·Bearer 인증 필요를 확인한 뒤 사용자 요청으로 보류했다.

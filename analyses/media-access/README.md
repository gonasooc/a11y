# 장애인방송 편성 실적 분석 재현

**2026-10-13 기준 기술통계**다. 결과와 해석 한계는 [docs/media-access/analysis.md](../../docs/media-access/analysis.md), 조사 범위와 출처는 [docs/media-access/README.md](../../docs/media-access/README.md)에 있다.

시청자미디어재단이 사전정보공표로 공개한 2017~2025년 방송사별 장애인방송 편성 실적(폐쇄자막·화면해설·한국수어방송의 목표·실적)을 읽어, 연도별 미달 사업자 수와 사업자군 평균을 계산한다. 방송미디어통신위원회 보도자료의 공식 평균·발표 수치와도 대조한다. OTT는 다루지 않는다(이유는 [docs/media-access/analysis.md](../../docs/media-access/analysis.md#3-ott는-왜-세지-않았나)).

## 실행

Python 표준 라이브러리만 쓴다. Python 3.9.6에서 실행을 확인했다. 저장소 루트에서:

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

2026-10-13 확인 내용: 해석을 다시 실행해 `data/`·`outputs/`의 해시가 같았다. 9개 연도 모두 원문에 표기된 사업자군별 사업자 수와 행 수가 일치했고, 일련번호가 1부터 빠짐없이 이어졌다. 테스트 8개는 병합 셀, 형광펜 속 글자, 쪽이 바뀐 연속 표, 보조 행, 합계 불일치, 빈 값, 재방송 시간 합계, 미달 판정과 버림 대조를 확인한다.

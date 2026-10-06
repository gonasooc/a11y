# 아키텍처

> 초기 작성: 2026-10-02 · 인증 수집 반영: 2026-10-03 · 웹 사이트 추가: 2026-10-06.

구성 요소의 책임과 의존 관계를 다룬다. 기술 구성과 실행 방법은 [docs/specs.md](specs.md)에 있다.

## 구성 요소와 책임

| 구성 요소 | 현재 책임 | 근거 |
|---|---|---|
| 프로젝트 문서 | 제품 방향·구조·구현 규칙·작업 상태 안내 | [docs/README.md](README.md) |
| 기존 조사 문서 | 접근성 이용 환경, 법·제도, 연표, 출처와 도구 아이디어 | [docs/01-digital-access-environment.md](01-digital-access-environment.md), [docs/05-policy-effect-case-proposals.md](05-policy-effect-case-proposals.md) |
| 디지털포용법 분석 입력 | 집계 관측, 출처·검증 기록, 정책 일정, API 명세 저장 | [analyses/digital-inclusion/data/source_manifest_baseline.json](../analyses/digital-inclusion/data/source_manifest_baseline.json) |
| 오프라인 분석 스크립트 | 초기 기준선·행안부 기능·조달청 조달 흐름을 각각 검증·계산 | [analyses/digital-inclusion/analyze.py](../analyses/digital-inclusion/analyze.py), [analyses/digital-inclusion/mois_analyze.py](../analyses/digital-inclusion/mois_analyze.py), [analyses/digital-inclusion/pps_analyze.py](../analyses/digital-inclusion/pps_analyze.py) |
| 분석 결과 | 계산 출력과 사람이 읽는 결과·한계 설명 | [analyses/digital-inclusion/outputs/summary.json](../analyses/digital-inclusion/outputs/summary.json), [docs/digital-inclusion-analysis.md](digital-inclusion-analysis.md) |
| 외부 API 연동 | 공통 인증·HTTP 처리와 서비스별 페이지·기간 수집, CSV·출처 명세 저장 | [analyses/digital-inclusion/api_common.py](../analyses/digital-inclusion/api_common.py), [analyses/digital-inclusion/mois_collect.py](../analyses/digital-inclusion/mois_collect.py), [analyses/digital-inclusion/pps_collect.py](../analyses/digital-inclusion/pps_collect.py) |
| KOSIS 연간 통계 | 통계표 메타데이터 기반 전체 셀 수집, 장기 추세·보고서 대조 | [analyses/digital-inclusion/kosis_collect.py](../analyses/digital-inclusion/kosis_collect.py), [analyses/digital-inclusion/kosis_analyze.py](../analyses/digital-inclusion/kosis_analyze.py) |
| 웹 사이트 | `site/`의 빌드 없는 정적 사이트. 메인 허브, 분석 보고서 페이지, 공통 스타일과 접근 가능한 차트 스크립트 | [site/README.md](../site/README.md) |
| 보고서 데이터 생성 | 분석 출력을 읽어 HTML의 생성 구역(표·조각·차트 데이터)을 채우고 본문 숫자를 검사한다 | [site/scripts/generate.mjs](../site/scripts/generate.mjs) |
| 배포 | GitHub Actions가 생성 구역을 검사한 뒤 `site/`를 그대로 GitHub Pages에 올린다 | [.github/workflows/pages.yml](../.github/workflows/pages.yml) |

## 주요 폴더와 흐름

```text
.
├── README.md                  # 저장소 소개와 문서 진입점
├── .github/workflows/pages.yml # 사이트 검사·GitHub Pages 배포
├── AGENTS.md                  # 기존 지침과 공통 문서 작업 규칙
├── CLAUDE.md                  # AGENTS.md 연결
├── docs/
│   ├── README.md              # 프로젝트 현황·작업 목록·기존 조사 목록
│   ├── plan.md                # 제품 기획
│   ├── architecture.md        # 구조와 책임
│   ├── specs.md               # 기술 구성·실행·검증
│   ├── 01-*.md … 05-*.md      # 기존 조사·분석 제안
│   ├── 10-digital-inclusion-api-guide.md # 기존 API 안내
│   ├── ideas.md              # 도구 아이디어 통합
│   ├── digital-inclusion-analysis.md # 디지털포용법 통합 보고서
│   ├── work/                 # 작업별 현재 상황·판단·남은 일
│   └── sessions/             # 필요한 경우에만 상세 세션 기록
├── site/                      # GitHub Pages 정적 사이트(빌드 없음)
│   ├── index.html             # 메인 허브, 각 페이지 링크
│   ├── reports/<주제>/        # 보고서 페이지와 데이터 설정(report.config.mjs)
│   ├── assets/                # 공통 스타일·차트 스크립트
│   └── scripts/               # 생성 구역 채우기·숫자 검사(Node)
└── analyses/digital-inclusion/
    ├── README.md              # 분석 재현 안내
    ├── plan.json              # 분석 범위·해석 조건
    ├── analyze.py             # 초기 기준선 계산
    ├── api_common.py          # 키 로딩·HTTPS·안전한 오류 처리
    ├── mois_collect.py        # 행안부 수집·완전성 검증
    ├── pps_collect.py         # 조달청 월별 수집·변경 이력
    ├── mois_analyze.py        # 행안부 현재 기능·지역 집계
    ├── pps_analyze.py         # 조달청 등록·납품요구 흐름
    ├── kosis_collect.py       # KOSIS 메타데이터·연간 통계 수집
    ├── kosis_analyze.py       # 장기 변화·기준선 대조
    ├── kosis_analysis_plan.json # 기간·출처 대조·해석 규칙
    ├── data/                  # 입력 CSV·출처/메타데이터 JSON
    ├── outputs/               # 분석별 JSON·CSV
    ├── tests/                 # 실제 키를 쓰지 않는 인증 처리 검증
    └── raw/                   # 로컬 원본, Git 제외
```

초기 기준선은 `data/`와 `plan.json` → 입력 검증 → 계산 → `outputs/` 흐름이다. API 분석은 외부 API → 공통 인증 처리 → 서비스별 수집 → 로컬 `raw/`·정규화 CSV·수집 명세 → 오프라인 분석 → `outputs/` 흐름이다. 결과 보고서는 사람이 읽을 수 있도록 별도 작성하며 코드가 자동 생성하지 않는다. 기존 PDF·ODT의 추출·전사는 수동이다.

웹 보고서는 `outputs/`·`data/` → `site/scripts/generate.mjs`가 `site/reports/<주제>/report.config.mjs`로 표·차트 JSON·검사값 계산 → HTML의 생성 구역에 기록하고 본문 숫자를 대조 → 브라우저가 생성 구역의 JSON으로 차트를 그리는 흐름이다. 생성 결과를 HTML에 커밋하므로 사이트를 보는 데는 빌드가 필요 없다. Python 분석 코드는 이 과정에 참여하지 않으며, 웹은 저장소에 커밋된 출력만 읽는다.

[analyses/digital-inclusion/analyze.py](../analyses/digital-inclusion/analyze.py)는 초기 입력 파일만 해시로 기록하므로 후속 API 데이터 추가가 기준선의 입력 목록에 섞이지 않는다. 수집과 분석은 별도 명령이며, 오프라인 분석에는 인증키가 필요 없다. 데이터베이스와 웹 서버는 없고, 브라우저 코드는 정적 사이트의 차트 그리기뿐이다.

## 지켜야 할 구조 규칙

- 이번에 적용한 문서 구조에서는 제품 방향은 [docs/plan.md](plan.md), 폴더 책임·의존 관계는 이 문서, 실행·검증 규칙은 [docs/specs.md](specs.md), 작업 진행 상태는 `docs/work/`에 둔다. 근거: [docs/work/W-001-main-docs-starter.md](work/W-001-main-docs-starter.md).
- 사용자 요청으로 통합한 두 문서는 `docs/ideas.md`와 `docs/digital-inclusion-analysis.md`에 두며 `docs/` 깊이를 유지한다. 다른 조사 문서의 경로는 유지하고 공통 문서에서 연결한다. 근거: [docs/work/W-005-main-docs-consolidation.md](work/W-005-main-docs-consolidation.md).
- 현재 분석 구조는 입력·출처·계산 출력·보고서를 별도 파일로 관리한다. 새 수집 자료를 추가할 때 관측 단위·수집일·출처를 보존하고, 과거 집계를 신규 원자료처럼 덮어쓰지 않는다. 근거: [analyses/digital-inclusion/README.md](../analyses/digital-inclusion/README.md).
- 웹 페이지는 `site/<영역>/<이름>/index.html`에 두고 허브 [site/index.html](../site/index.html)에 링크를 더한다. 분석 결과는 생성 스크립트가 출력 파일에서 읽고 수집 원자료는 읽지 않는다. 빌드 도구는 쓰지 않는다. 근거: [docs/work/W-006-main-pages-site.md](work/W-006-main-pages-site.md).
- 도구별 서버·클라이언트 책임과, 빌드가 필요한 서비스를 들일 때의 방식은 미정이다.

## 알려진 구조 제약

- 현재 스크립트는 디지털포용법 초기 분석의 연도·분류·출처 조건에 맞춰 작성돼 있다. 범용 정책 효과 분석 엔진으로 확인된 것은 아니다.
- 공급업체·검증 모델·설치 기기·이용자 연간 통계는 관측 단위가 달라 하나의 패널로 바로 결합할 수 없다. 근거: [analyses/digital-inclusion/plan.json](../analyses/digital-inclusion/plan.json).
- Git에서 제외한 로컬 원본은 다른 체크아웃에 포함되지 않는다. 원문 재확인은 출처 명세의 다운로드 주소·해시를 이용한다.
- 인증 수집기는 명시적으로 실행하는 로컬 명령이다. 정기 갱신은 없다. 결과 게시는 커밋된 출력으로 생성 구역을 다시 채운 HTML을 올리는 방식이며, 출력과 본문 숫자가 어긋나면 검사가 실패해 배포되지 않는다.
- 행안부는 일반 페이지 순서의 중복을 감지하면 기관·시간 구간을 나눠 완전성을 검증한다. 조달청은 수집일별 응답 캐시를 유지하고 갱신 시 이전 바이트를 해시별로 보존한다. 정규화 CSV·요약은 현재 선택한 수집 결과이므로 새 기간을 적용하기 전에 기존 명세와 원본을 보존한다.
- KOSIS는 보고서 기반 초기 CSV와 별도 입력을 유지한다. 출처 간 불일치 셀을 기록하고 계열을 조용히 접합하지 않는다. 연간 이용자 통계는 기기·조달 기록과 관측 단위가 달라 각각 분석한다.

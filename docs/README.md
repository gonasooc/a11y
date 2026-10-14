# a11y 프로젝트 문서

## 현재 상황

접근성 도구와 데이터 분석 페이지를 하나씩 추가하고, 메인 페이지에서 각 항목에 접근할 수 있도록 구성하는 프로젝트다. 현재는 조사 문서와 디지털포용법 초기 탐색 분석 코드가 있고, 2026-10-06에 GitHub Pages용 정적 사이트(`site/`)와 시각화 보고서를 만들어 `https://gonasooc.github.io/a11y/`에 배포했다.

2026-10-02에 docs-starter의 한국어 문서 구조를 적용했고, 2026-10-03에는 조달청·행안부·KOSIS 인증 수집과 추가 분석을 완료했다. 결과와 다음 자료 확보 작업은 아래에서 확인한다. 기존 접근성 조사 문서와 디지털포용법 분석 문서는 2026-10-12에 [docs/digital-inclusion/README.md](digital-inclusion/README.md) 아래 네 문서로 모았다. 2026-10-13에는 두 번째 주제로 영상 미디어 접근성 조사를 시작했다.

## 기본 문서

- [docs/plan.md](plan.md): 제품 목적, 사용자, 기능 범위와 정책.
- [docs/architecture.md](architecture.md): 현재 구성 요소, 폴더 책임과 데이터 흐름.
- [docs/specs.md](specs.md): 코드에서 확인한 기술 구성과 실행·검증 방법.

- [docs/design.md](design.md): 사이트의 시각·상호작용·반응형·접근성 기준. 글꼴·장식·밝은 화면·머리글·바닥글 문체는 사용자가 정했고 나머지는 검토 전이다.

현재 작업에 필요한 문서부터 선택해 읽는다.

## 진행 중·예정·보류 작업

- [docs/work/W-010-main-media-access-report.md](work/W-010-main-media-access-report.md) — 영상 접근성 웹 보고서(제목 ‘TV 자막·수어·화면해설, 의무는 채웠는데 볼 게 있나’) — 진행 중. `site/reports/media-access/`에 그림 4개·질문형 절 6개로 구현했고 생성 검사·axe·320~1440px 확인을 통과했다. 커밋·공개 전이다.
- [docs/work/W-007-main-lay-reader-report.md](work/W-007-main-lay-reader-report.md) — 비장애인 독자를 위한 디지털포용법 보고서 개편 — 진행 중. 13개 결정을 구현해 공개 주소에 배포했다. 독자 테스트와 첫 화면 구성 결정이 남았다.
- [docs/work/W-006-main-pages-site.md](work/W-006-main-pages-site.md) — GitHub Pages 사이트와 디지털포용법 시각화 보고서 — 진행 중. `https://gonasooc.github.io/a11y/`에 배포해 공개 화면을 확인했다. 실제 스크린리더 확인과 디자인 기준 확정 여부가 남았다.
- [docs/work/W-004-main-history-data.md](work/W-004-main-history-data.md) — 기기·검증 제품 과거 이력 확보 — 진행 중. 기관·제품별 조달 분해·기능 조합 분석 및 공개 교체 공지 조사 완료. 기기별 완료 이력·차기 연간 통계는 미확보.

NIA 배리어프리 키오스크 위치 API(`15157403`)는 사용자 요청으로 **보류**했다. 키 발급 조사·연결·수집은 재개 요청이 있을 때 이어간다. 상세 범위는 W-004의 부분 보류 기록을 따른다.

상태는 `예정`, `진행 중`, `보류`, `완료`를 사용한다. 상세 상태와 판단 근거는 각 작업 문서에서 관리한다.

## 최근 완료

- [docs/work/W-009-main-media-access.md](work/W-009-main-media-access.md) — 영상 미디어 접근성 조사(방송·OTT·영화관의 자막·수어·화면해설) — 완료. 2017~2025년 방송 편성 실적 분석과 deep-research 보완 조사로 근거 문서 네 개를 [docs/media-access/README.md](media-access/README.md) 아래에 썼다. 공개 자료로 확인하지 못한 항목은 그 문서의 재확인 목록에 있다.
- [docs/work/W-008-main-docs-digital-inclusion.md](work/W-008-main-docs-digital-inclusion.md) — 디지털포용법 근거 문서를 docs/digital-inclusion으로 정리 — 완료. 일곱 문서를 네 문서로 합치고, 저장소 링크와 공개 보고서의 GitHub 링크·앵커를 확인했다.
- [docs/work/W-005-main-docs-consolidation.md](work/W-005-main-docs-consolidation.md) — 도구 아이디어·디지털포용법 보고서 통합 — 완료. 같은 `docs/` 깊이에서 내용·출처·링크를 통합했다.
- [docs/work/W-003-main-additional-data.md](work/W-003-main-additional-data.md) — KOSIS 추가 분석 — 완료. 240셀 수집, 2016년 이후 추세·보고서 대조·불일치 원문 확인.
- [docs/work/W-002-main-digital-inclusion-api.md](work/W-002-main-digital-inclusion-api.md) — 조달청·행안부 추가 분석 — 완료. 인증·수집 완전성·기능 현황·조달 흐름·재현 검증.
- [docs/work/W-001-main-docs-starter.md](work/W-001-main-docs-starter.md) — 한국어 프로젝트 문서 구조 적용 — 완료. 기존 내용 보존과 링크·분석 재현을 확인했다.

## 기존 분석 진입점

- [docs/digital-inclusion/README.md](digital-inclusion/README.md): 디지털포용법 보고서의 근거 문서 안내. 조사 개요, 출처와 검증 노트, 이전 경로 대응표.
- [docs/digital-inclusion/environment.md](digital-inclusion/environment.md): 장애인의 인터넷·웹·앱 이용 환경.
- [docs/digital-inclusion/law.md](digital-inclusion/law.md): 민간 기업 웹·앱 접근성의 법적 강제와 정책 동향, 부록 연표.
- [docs/digital-inclusion/analysis.md](digital-inclusion/analysis.md): 디지털포용법 통합 보고서. 이용자·웹 기준선, 기기 현황, 조달 변화와 해석 한계.
- [docs/media-access/README.md](media-access/README.md): 영상 미디어 접근성 조사 안내. 이용자와 시청 경험, 제도와 연표, 2017~2025 장애인방송 편성 실적 분석.
- [analyses/media-access/README.md](../analyses/media-access/README.md): 장애인방송 편성 실적 수집·해석·계산 재현.
- [docs/ideas.md](ideas.md): 도구 아이디어 28개와 하위 제안, 공통 근거·조건별 우선순위.
- [docs/digital-inclusion/analysis.md](digital-inclusion/analysis.md#부록-b-디지털포용법-분석에-필요한-api): API 발급과 명세 확인 안내.
- [analyses/digital-inclusion/README.md](../analyses/digital-inclusion/README.md): 분석 코드·데이터·재현 방법.
- [site/README.md](../site/README.md): 웹 사이트 실행·구조·새 페이지 추가 방법.

## 기록을 찾을 때

작업 문서의 ‘현재 상황’과 ‘남은 일’의 미완료 항목부터 읽는다. 완료 항목은 체크된 상태로 유지하며, 보류 이유와 재개 조건도 같은 작업 문서에 기록한다.

- [docs/work/_template.md](work/_template.md): 새 작업의 현재 상황·진행과 판단·남은 일 양식.
- [docs/sessions/_template.md](sessions/_template.md): 긴 근거가 필요할 때만 사용하는 상세 세션 양식.
- [AGENTS.md](../AGENTS.md): 기존 Context7 지침과 문서 작성·갱신 규칙.

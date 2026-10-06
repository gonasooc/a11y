# W-006 · GitHub Pages 사이트와 디지털포용법 시각화 보고서

- 상태: 진행 중
- 최근 갱신: 2026-10-06
- 관련 문서: [docs/README.md](../README.md), [docs/digital-inclusion-analysis.md](../digital-inclusion-analysis.md), [site/README.md](../../site/README.md), [docs/design.md](../design.md)

## 현재 상황

`site/`에 빌드 도구 없는 정적 사이트를 만들었다. 메인 허브(`site/index.html`)에서 디지털포용법 분석 보고서(`site/reports/digital-inclusion/index.html`)로 이동하고, 보고서는 차트 15개와 HTML 막대·열지도 표로 원문을 시각화한다. 처음에는 Vite로 만들었다가 사용자 판단에 따라 걷어냈고, 이어서 글꼴을 Pretendard 하나로 줄이고 도장 같은 장식을 없앤 담백한 디자인으로 바꿨다. 파일을 직접 열거나 하위 경로로 서빙했을 때의 동작과 접근성 자동 검사를 마쳤다. 저장소 Pages 설정과 실제 배포는 아직이다.

- 완료 조건: `https://gonasooc.github.io/a11y/`에서 허브와 보고서가 열리고, 차트·표·테마 전환이 동작한다.
- 사람이 판단할 사항: 저장소 Settings → Pages의 Source를 ‘GitHub Actions’로 바꿀지, 변경을 커밋·푸시할 시점. 디자인 기준([docs/design.md](../design.md))을 합의된 기준으로 확정할지.

## 진행과 판단

### 배경과 범위

사용자 요청(2026-10-06): [docs/digital-inclusion-analysis.md](../digital-inclusion-analysis.md)를 바탕으로 차트를 활용한 HTML 문서를 만든다. GitHub Pages로 배포하고, 메인 index에서 여러 HTML 문서와 웹 서비스로 들어가며, 한 저장소에 여러 서비스가 함께 있게 될 것을 고려한다. 구성은 [CausalInferenceLab/policy-effect-analytics-agent](https://github.com/CausalInferenceLab/policy-effect-analytics-agent)를 참고해도 된다고 했다.

같은 날 후속 요청: 빌드 도구가 꼭 필요한지 보수적으로 판단하고, 불필요하면 걷어낸다. 메인 index에서 각 HTML로 접근하는 방식이면 충분하다.

같은 날 두 번째 후속 요청: 글꼴은 Pretendard만 쓴다. 신뢰가 중요한 페이지이므로 모던한 느낌이면 된다. `.verdict__stamp` 같은 불필요한 도장 효과를 없애고 모던하고 신뢰감 있게 디자인한다.

### 중요한 시도와 결정

- 2026-10-06 — 처음 구현은 Vite 8 다중 페이지 프로젝트였다. Vite가 맡은 일은 네 가지였다: npm 패키지 세 개(`d3-array` 눈금 함수, `d3-dsv` CSV 읽기, Fontsource 글꼴) 연결, 빌드 때 분석 출력을 HTML에 넣고 본문 숫자를 대조하는 플러그인, `catalog.json`으로 허브 목록 만들기, 개발 서버.
- 2026-10-06 (변경) — 사용자 요청으로 Vite를 걷어냈다. 판단 근거: 위 네 가지 중 셋은 몇십 줄로 대체되고(눈금 함수 이식, 작은 CSV 파서, Google Fonts 링크), 허브 목록은 손으로 적는 편이 단순하다. 남는 하나(데이터 채우기·숫자 검사)는 외부 패키지 없는 Node 스크립트 [site/scripts/generate.mjs](../../site/scripts/generate.mjs)로 옮겼다. 또 모듈 스크립트는 파일로 연 페이지에서 막혀 차트가 그려지지 않았다(헤드리스 Chrome에서 0개). 일반 스크립트로 바꿔 파일을 더블클릭해도 동작하게 했다.
- 2026-10-06 — 보고서 수치는 [site/reports/digital-inclusion/report.config.mjs](../../site/reports/digital-inclusion/report.config.mjs)가 `analyses/digital-inclusion`의 입력·출력에서 계산한다. 생성 스크립트가 그 결과를 HTML의 짝 표식 사이(표 19개, 조각 7개, 차트 데이터 1개)에 채운다. 해석 문장은 아키텍처 규칙대로 사람이 쓰고, 본문 숫자 132곳(고유 키 121개)에 `data-check`를 붙여 계산값과 대조한다. 출력 사이의 합계(월 합계와 요약 JSON, 기관·제품 분해와 주 비교 등)도 함께 검사한다.
- 2026-10-06 — 표를 별도 데이터 파일이 아니라 HTML 안에 정적으로 넣었다. 페이지 하나가 한 파일로 끝나고, 자바스크립트 없이도 표를 읽을 수 있다. 표식 사이는 사람이 고치지 않는다.
- 2026-10-06 — 차트 라이브러리 대신 작은 SVG 차트 모음을 직접 만들었다([site/assets/js/chart/](../../site/assets/js/chart/)). 차트마다 탭 정지점 하나, 화살표·Home·End 탐색, 포커스 고리와 툴팁, `role="img"` 이름이 있는 값 단위를 둔다. 기존 라이브러리의 포인터 전용 툴팁으로는 키보드에서 같은 정보를 줄 수 없어서다. 눈금 계산은 d3-array 3.2.4의 `ticks`·`nice`를 ISC 고지와 함께 옮겼다.
- 2026-10-06 — 참고 저장소에서 판정 3단계(효과 근거 있음·조건부·판단 불가)와 ‘질문 → 판정 → 근거 → 한계 → 재현’ 흐름을 빌렸다. 첫 화면에 판정 상태를 두고, 자료별 관측 시점과 시행일을 한 축에 놓는 그림 1을 새로 만들었다. 원문에 없는 문장은 그림 1 설명과 월별 차트의 최대 두 달 관찰뿐이며 둘 다 검사 대상이다.
- 2026-10-06 (변경) — 처음에는 세리프 제목(Hahmlet), 본문 IBM Plex Sans KR, 따뜻한 종이색 바탕, 기울어진 ‘판단 불가’ 도장과 등장 애니메이션을 썼다. 사용자 요청으로 글꼴을 Pretendard 하나로 줄이고(jsDelivr의 가변 다이나믹 서브셋, 코드와 명령도 Pretendard), 도장·애니메이션·카드 그림자를 없앴다. 바탕은 중립 회색과 흰 카드(어두운 화면은 `#0f1115`·`#171a1f`)로 바꾸고, 판정은 아이콘·굵은 글자·3단계 표시로만 보여 준다. 차트 팔레트는 새 카드 면에서 다시 검사해 통과했다. 기준은 [docs/design.md](../design.md)에 옮겼다.
- 2026-10-06 — 글꼴 CSS는 첫 화면을 막지 않게 늦게 적용하고, 글꼴이 도착하면 차트를 한 번 다시 그려 라벨 폭을 맞춘다. 외부 요청(jsDelivr)이 하나 생기는 것이 대가다.
- 2026-10-06 — 링크는 상대경로로 `index.html`까지 적는다. 파일로 열어도, `/<저장소>/` 하위 경로에서도 맞는다.
- 2026-10-06 — 배포는 [.github/workflows/pages.yml](../../.github/workflows/pages.yml)로 한다. 브랜치 배포는 루트나 `/docs`만 고를 수 있어 `site/`를 올리려면 워크플로가 필요하다. `node site/scripts/generate.mjs --check`가 통과하면 `site/`를 그대로 올린다. PR에서는 검사만 한다.

### 검증

Vite 제거와 디자인 변경 뒤 다시 실행한 결과다.

- 출력 동일성 — 통과. 제거 전 Vite 플러그인이 만든 데이터·표·조각·검사값(JSON)과 새 스크립트의 결과가 바이트 단위로 같다. 새 CSV 파서를 포함한다.
- `node site/scripts/generate.mjs` · `--check` — 통과. Node 20.19.0, macOS. 생성 구역 27개, 본문 숫자 132곳 일치. 다시 실행해도 바뀌는 것이 없다.
- 실패 검사 — 통과. 본문 숫자 하나와 표 칸 하나를 일부러 바꾸면 `--check`가 두 문제를 보고하고 종료 코드 1을 낸다.
- 파일로 열기 — 통과. 헤드리스 Chrome으로 `file://`의 보고서를 열면 차트 15개, 이름 있는 값 단위 114개, 표 22개가 나온다(제거 전 모듈 방식은 차트 0개).
- 하위 경로 서빙 — 통과. `site/`를 `/a11y/`로 연결한 로컬 정적 서버에서 허브 → 보고서 → 허브 이동, 자산 경로, 글꼴 로드, 콘솔 오류 없음 확인.
- 키보드 — 통과. 차트 15개 각각 탭 정지점 1개, 화살표로 월 이동과 툴팁 확인. 브라우저 창에 초점이 있어야 키 입력이 전달된다는 점은 테스트 도구의 제약이었다.
- 글꼴 도착 후 다시 그리기 — 통과. 헤드리스 Chrome에서 글꼴 로드 이벤트 한 번에 차트 15개가 한 번씩만 다시 그려지고 반복되지 않았다. `requestAnimationFrame`은 숨은 탭에서 멈춰 타이머로 바꿨다.
- axe-core 4.10.2(WCAG 2.0~2.2 A·AA, best-practice, 표 보기 모두 펼침) — 디자인 변경 뒤 보고서·허브 모두 밝은·어두운 테마에서 위반 0. 보고서의 미확정 항목은 SVG 글자의 대비 계산 불가로, 색 토큰은 따로 4.5:1 이상을 계산해 확인했다.
- 색 검사 — dataviz `validate_palette.js`로 5계열(인접)·3계열(전체 쌍)을 새 카드 면 `#ffffff`·`#171a1f`에서 검사해 통과. 밝은 테마 3~5번 계열은 3:1 미만이라 직접 라벨과 표 보기를 함께 둔다. 글자 토큰은 바탕·카드·옅은 면에서 모두 4.5:1 이상으로 계산했다.
- 화면 확인 — 통과. 디자인 변경 뒤 1440px 밝은·어두운 테마, 390px·320px 폭(iframe)에서 허브와 보고서 확인. 가로 넘침 없음(표는 자체 스크롤). 320px에서 맞닿던 폭포 차트 라벨은 칸이 좁을 때만 작게 쓰도록 고쳤다.
- GitHub Actions 실행·Pages 배포 — 미실행. 저장소 설정과 푸시가 필요하다.

### 세션 메모

- 2026-10-06 · Claude Code — Vite로 사이트·보고서·워크플로·문서를 만들고 로컬 검증을 마쳤다.
- 2026-10-06 · Claude Code — 사용자 판단에 따라 Vite와 npm 의존성을 걷어내고 정적 파일과 생성 스크립트로 바꿨다. 이어서 Pretendard 단일 글꼴과 장식 없는 디자인으로 바꿨다. 커밋하지 않았다. 다음 행동은 Pages 설정 후 푸시해 배포를 확인하는 것이다.

## 남은 일

- [ ] 저장소 Settings → Pages → Source를 ‘GitHub Actions’로 바꾼다(사용자).
- [ ] 변경을 커밋·푸시하고 Actions 실행과 `https://gonasooc.github.io/a11y/` 화면을 확인한다.
- [ ] 실제 스크린리더(VoiceOver·NVDA·TalkBack)로 차트 탐색과 표 보기를 확인한다. 이번에는 접근성 트리와 axe-core까지만 확인했다.
- [ ] 분석 출력이 바뀌면 `node site/scripts/generate.mjs`를 실행하고, 실패 메시지가 가리키는 본문 문장과 숫자를 함께 고친다.
- [x] Vite 제거 후 390px·320px 폭 화면을 다시 확인한다.

재개에 필요한 코드 상태: `main` 브랜치, 기준 커밋 `8ee8db7`. `site/`, `.github/workflows/pages.yml`, 문서 변경이 모두 미커밋이다.

# site

GitHub Pages로 공개하는 정적 사이트다. 빌드 도구 없이 HTML·CSS·JavaScript 파일을 그대로 올린다. 메인 허브(`index.html`)에서 각 보고서와 도구 페이지로 이동한다. 구조와 결정 근거는 [docs/architecture.md](../docs/architecture.md)와 [docs/work/W-006-main-pages-site.md](../docs/work/W-006-main-pages-site.md)에 있다.

## 보기

- `site/index.html`을 브라우저로 열면 된다. 파일을 더블클릭해 열어도 차트와 표가 모두 동작한다.
- 웹 서버로 보고 싶으면 아무 정적 서버나 쓴다. 예: `python3 -m http.server 8000 -d site` 후 `http://localhost:8000/`.
- 글꼴은 Pretendard 하나만 쓰고 jsDelivr에서 받는다. 인터넷이 없으면 시스템 한글 글꼴로 보인다.

`main` 브랜치에 `site/`나 `analyses/` 변경이 반영되면 [.github/workflows/pages.yml](../.github/workflows/pages.yml)이 검사한 뒤 `site/`를 그대로 배포한다.

## 분석 출력이 바뀌었을 때

보고서의 표·HTML 조각·차트 데이터는 `analyses/`의 출력에서 만든 값이 HTML 안의 생성 구역에 들어 있다. 출력이 바뀌면 다시 만든다. Node 20 이상만 있으면 되고 설치할 패키지는 없다.

```sh
node site/scripts/generate.mjs          # 생성 구역을 다시 채우고 본문 숫자를 검사한다
node site/scripts/generate.mjs --check  # 파일을 바꾸지 않고 검사만 한다(CI가 쓰는 명령)
```

- 생성 구역은 `<!--table:키-->…<!--/table:키-->`, `<!--html:키-->…<!--/html:키-->`, `<!--report:data-->…<!--/report:data-->` 사이다. 이 사이는 직접 고치지 않는다.
- 본문 숫자에 붙인 `data-check="키"`는 계산값과 표시한 자릿수로 비교한다. 크기만 비교할 때는 `data-abs`를 함께 붙인다. 다르면 스크립트가 실패하고, 사람이 문장을 다시 읽고 고친다.

## 구조

```text
site/
├── index.html                  # 메인 허브. 각 페이지로 가는 링크를 손으로 적는다
├── favicon.svg
├── assets/
│   ├── css/                    # 디자인 토큰, 공통·차트·보고서·허브 스타일
│   └── js/                     # 숫자 형식, 접근 가능한 SVG 차트 모음(chart/)
├── reports/<이름>/
│   ├── index.html              # 사람이 쓴 본문과 생성 구역
│   ├── main.js                 # 생성 구역의 JSON으로 차트를 그린다
│   └── report.config.mjs       # 분석 출력을 읽어 표·조각·차트 데이터·검사값을 만든다(Node 전용)
└── scripts/
    ├── generate.mjs            # 생성 구역 채우기와 검사
    └── lib/                    # CSV 읽기, 표 HTML, 숫자 검사
```

브라우저 스크립트는 모듈(`type="module"`)이 아닌 일반 스크립트다. 파일로 연 페이지에서도 동작하게 하려는 것이다. 공통 함수는 `window.A11y`에 올리고, 페이지는 `<script defer>`를 정해진 순서로 불러온다.

`assets/js/format.js`는 브라우저와 생성 스크립트(Node)가 함께 쓴다. Node는 이 파일을 CommonJS로 읽으므로, `site/`나 저장소 루트에 `"type": "module"`인 `package.json`을 두면 생성 스크립트가 멈춘다.

## 새 페이지를 더할 때

1. `site/<영역>/<이름>/index.html`을 만든다. 보고서는 `reports`, 도구는 `tools`처럼 영역을 정한다. 기존 보고서의 `<head>`와 머리글·바닥글을 따라 쓴다.
2. 다른 페이지로 가는 링크는 상대경로로 `index.html`까지 적는다(`../../index.html`). 파일로 열었을 때도 이동하고, `https://<계정>.github.io/a11y/` 같은 하위 경로에서도 맞는다.
3. 허브 `site/index.html`의 페이지 목록에 항목을 하나 더한다.
4. 분석 출력이 필요하면 페이지 폴더에 `report.config.mjs`를 두고 `build({ repoRoot, repoUrl })`가 `{ data, tables, fragments, facts }`를 돌려주게 한 뒤 `node site/scripts/generate.mjs`를 실행한다.

## 접근성 기준

- 차트마다 같은 값을 담은 표를 두고(‘표로 보기’), 차트 안에서는 탭 한 번으로 들어가 화살표·Home·End로 값을 읽는다. 표는 HTML에 정적으로 들어 있어 자바스크립트 없이도 읽힌다.
- 화면은 밝은 버전 하나뿐이다. 차트 색은 dataviz 기준 팔레트를 쓰고 흰 카드 면에서 색각 구분과 대비를 검사했다. 글자는 모든 토큰에서 4.5:1 이상이다.
- 320px 폭에서 가로 스크롤 없이 읽히는지(표는 자체 스크롤), 키보드 초점이 보이는지, axe-core 위반이 없는지 확인한다. 세부 기준은 [docs/design.md](../docs/design.md)에 있다.

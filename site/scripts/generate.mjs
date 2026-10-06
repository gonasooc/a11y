// 보고서 페이지의 생성 구역(표·HTML 조각·차트 데이터)을 분석 출력으로 다시 채우고 본문 숫자를 검사한다.
// 외부 패키지가 필요 없다. 페이지를 보는 데는 이 스크립트가 필요 없고, 분석 출력이 바뀌었을 때만 실행한다.
//
//   node site/scripts/generate.mjs          생성 구역을 고쳐 쓰고 검사한다
//   node site/scripts/generate.mjs --check  파일을 바꾸지 않는다. 고칠 구역이 있거나 숫자가 다르면 실패한다(CI)
//
// 생성 구역은 <!--table:키-->…<!--/table:키-->, <!--html:키-->…<!--/html:키-->, <!--report:data-->…<!--/report:data-->다.
// 표식 사이는 직접 고치지 않는다. 다음 실행 때 덮어쓴다.
import { readdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { checkFacts } from './lib/check.mjs';
import { jsonForScript, renderTable } from './lib/html.mjs';

const REPO_URL = 'https://github.com/gonasooc/a11y';
const siteRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const repoRoot = resolve(siteRoot, '..');
const checkOnly = process.argv.includes('--check');

const OPEN_RE = /<!--(table|html|report):([\w.-]+)-->/g;
const REGION_RE = /<!--(table|html|report):([\w.-]+)-->[\s\S]*?<!--\/\1:\2-->/g;

async function findConfigs(dir) {
  const found = [];
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    if (entry.name.startsWith('.') || entry.name === 'assets' || entry.name === 'scripts') continue;
    const full = join(dir, entry.name);
    if (entry.isDirectory()) found.push(...(await findConfigs(full)));
    else if (entry.name === 'report.config.mjs') found.push(full);
  }
  return found.sort();
}

function fill(html, { data, tables = {}, fragments = {} }) {
  const problems = [];
  const warnings = [];
  const used = new Set();
  const out = html.replace(REGION_RE, (_, kind, key) => {
    let content = null;
    if (kind === 'table' && tables[key]) content = renderTable(tables[key]);
    if (kind === 'html' && key in fragments) content = fragments[key];
    if (kind === 'report' && key === 'data') content = `<script type="application/json" id="report-data">${jsonForScript(data)}</script>`;
    if (content === null) {
      problems.push(`데이터 설정에 없는 생성 구역: ${kind}:${key}`);
      content = '';
    }
    used.add(`${kind}:${key}`);
    return `<!--${kind}:${key}-->\n${content}\n<!--/${kind}:${key}-->`;
  });
  for (const [, kind, key] of html.matchAll(OPEN_RE)) {
    if (!used.has(`${kind}:${key}`)) problems.push(`닫는 표식이 없다: <!--/${kind}:${key}-->`);
  }
  for (const key of Object.keys(tables)) if (!used.has(`table:${key}`)) warnings.push(`페이지에서 쓰지 않는 표: ${key}`);
  for (const key of Object.keys(fragments)) if (!used.has(`html:${key}`)) warnings.push(`페이지에서 쓰지 않는 조각: ${key}`);
  return { out, problems, warnings, regions: used.size };
}

let failed = false;
const configs = await findConfigs(siteRoot);
for (const configFile of configs) {
  const pageFile = join(dirname(configFile), 'index.html');
  const name = relative(repoRoot, pageFile);
  const { build } = await import(pathToFileURL(configFile).href);
  const result = await build({ repoRoot, repoUrl: REPO_URL });
  const html = await readFile(pageFile, 'utf8');
  const { out, problems, warnings, regions } = fill(html, result);
  const facts = checkFacts(out, result.facts ?? {});
  problems.push(...facts.problems);
  const changed = out !== html;
  if (checkOnly && changed) problems.push('생성 구역이 분석 출력과 다르다. node site/scripts/generate.mjs로 다시 만든다.');
  if (!checkOnly && changed) await writeFile(pageFile, out);

  for (const warning of warnings) console.warn(`  경고: ${warning}`);
  if (problems.length) {
    failed = true;
    console.error(`✗ ${name}\n  - ${problems.join('\n  - ')}`);
  } else {
    const action = checkOnly ? '최신 상태' : changed ? '갱신함' : '바뀐 것 없음';
    console.log(`✓ ${name}: ${action}. 생성 구역 ${regions}개, 본문 숫자 ${facts.count}곳 일치`);
  }
}
if (!configs.length) console.log('report.config.mjs가 있는 페이지가 없다.');
process.exit(failed ? 1 : 0);

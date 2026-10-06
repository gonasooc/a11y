// 디지털포용법 보고서의 생성 구역 데이터. site/scripts/generate.mjs가 불러 쓴다.
// analyses/digital-inclusion의 입력·출력만 읽어 차트 JSON, 정적 표·조각, 본문 숫자 검사값(facts)을 만든다.
// 해석 문장은 index.html에 사람이 쓰고, 여기서는 계산과 형식만 맡는다.
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import format from '../../assets/js/format.js';
import { parseCsv } from '../../scripts/lib/csv.mjs';
import { escapeHtml, renderTable } from '../../scripts/lib/html.mjs';

const { fmt, fmtPct, fmtSigned, fmtSignedPct, monthLabel, pctChange, round, toEok } = format;

const ANALYSIS_DIR = 'analyses/digital-inclusion';
const SOURCES = {
  kosis: 'data/kosis_digital_divide_2026-10-03.csv',
  kosisGaps: 'outputs/kosis_latest_gaps_2026-10-03.csv',
  kosisCompare: 'outputs/kosis_report_comparison_2026-10-03.csv',
  baseline: 'data/baseline_indicators.csv',
  events: 'data/policy_events.csv',
  moisSummary: 'outputs/mois_summary_2026-10-03.json',
  moisRegions: 'outputs/mois_region_comparison_2026-10-03.csv',
  moisPairs: 'outputs/mois_feature_pairs_2026-10-03.csv',
  moisPatterns: 'outputs/mois_feature_patterns_2026-10-03.csv',
  ppsMonthly: 'outputs/pps_monthly.csv',
  ppsSummary: 'outputs/pps_summary.json',
  ppsCohorts: 'outputs/pps_institution_cohorts.csv',
  ppsInstitutions: 'outputs/pps_institutions_comparison.csv',
  ppsProducts: 'outputs/pps_products_comparison.csv',
  registry: 'outputs/registry_composition.csv',
  summary: 'outputs/summary.json',
};

const POPULATIONS = [
  { key: 'disabled', label: '장애인' },
  { key: 'older_adults', label: '고령층' },
  { key: 'low_income', label: '저소득층' },
  { key: 'farmers_fishers', label: '농어민' },
  { key: 'vulnerable_weighted', label: '취약계층 가중평균' },
];
const INDICATORS = [
  { key: 'overall', label: '종합' },
  { key: 'access', label: '접근' },
  { key: 'capability', label: '역량' },
  { key: 'utilization', label: '활용' },
];
const YEARS = Array.from({ length: 10 }, (_, i) => 2016 + i);

const FEATURE_LABELS = {
  FRBLND_KPD: { key: 'keypad', label: '시각장애인용 키패드' },
  FRBLND_VOICE_GD: { key: 'voice', label: '시각장애인용 음성안내' },
  FRDEAF_SCRN_GD: { key: 'deafScreen', label: '청각장애인용 화면안내' },
  BRL_LBL_ATCMNT: { key: 'braille', label: '점자라벨 부착' },
  EPHN_SCKT: { key: 'earphone', label: '이어폰 소켓' },
  TCTL_ELCTNC_MONITOR: { key: 'tactile', label: '촉각 전자모니터' },
  SCRN_EXPSN_FWK: { key: 'zoom', label: '화면 확대' },
  WHCHR_USER_MNPLT: { key: 'wheelchair', label: '휠체어 사용자 조작' },
};

// 정책 일정의 표시 문구와 비교 영향은 docs/digital-inclusion-analysis.md의 표를 따른다.
const EVENT_TEXT = {
  '2025-01-21': ['법 제정·공포', '시행 전에도 기업이 대응했을 수 있다'],
  '2025-03-27': ['기존 지능정보화 기본법의 설치·운영 의무 도입', '제조·임대 의무와 별도로 이어지는 정책'],
  '2025-10-20': ['검증기준 개정', '등록 수요·처리 일정에 영향을 줄 수 있는 경쟁 사건'],
  '2026-01-22': ['법 시행, 대기업·중견기업 제조·임대 의무', '1월 전체를 사후로 분류하면 시행 전 21일이 섞인다'],
  '2026-01-28': ['장애인차별금지법의 키오스크 편의 조치 전면 적용', '제조 의무 6일 뒤 수요 측 정책이 겹친다'],
  '2026-04-20': ['구 검증기준 적용 가능한 신청 마감', '발급 마감이 아니다. 이후 발급량에도 영향을 줄 수 있다'],
  '2026-04-22': ['대기업·중견기업 계도 종료', '법정 시행일과 행정 집행 일정을 구분해야 한다'],
  '2026-07-22': ['중기업 제조·임대 의무', '중소기업 전체를 미처치 비교군으로 둘 수 없다'],
  '2027-01-22': ['소기업·소상공인 제조·임대 의무 예정', '분석 기준일 현재 미래 사건이다'],
};
const ROLE_LABEL = {
  anticipation: '공포',
  preceding_policy: '선행 정책',
  competing_event: '경쟁 사건',
  treatment: '시행',
  enforcement: '집행 일정',
  staggered_treatment: '시차 적용',
  planned_treatment: '예정',
};

const COMPANY_TYPES = [
  { labels: ['large', 'mid_sized'], label: '대기업·중견기업' },
  { labels: ['sme'], label: '중소기업' },
  { labels: ['nonprofit_other'], label: '비영리·기타' },
  { labels: ['unclassified'], label: '기업유형 미분류' },
];
const PRODUCT_CLASSES = {
  parking_payment: '무인주차정산기',
  ordering: '무인주문기',
  financial: '금융자동화기기',
  library: '무인도서대여반납기',
  civil_service: '무인민원발급기',
  remaining_classes: '나머지 분류',
};
const FOCUS_PRODUCTS = ['24422601', '24362786', '24362785', '25202556'];

function fail(message) {
  throw new Error(`[digital-inclusion] ${message}`);
}
function assertClose(label, a, b, tolerance = 1e-6) {
  if (Math.abs(Number(a) - Number(b)) > tolerance) fail(`${label}: ${a} ≠ ${b}`);
}
const num = (value, label) => {
  const n = Number(value);
  if (value === '' || value == null || !Number.isFinite(n)) fail(`숫자가 아닌 값: ${label} = ${value}`);
  return n;
};
const sum = (values) => values.reduce((a, b) => a + b, 0);

async function loadSources(repoRoot, repoUrl) {
  const loaded = {};
  const provenance = [];
  for (const [key, rel] of Object.entries(SOURCES)) {
    const path = `${ANALYSIS_DIR}/${rel}`;
    const buffer = await readFile(resolve(repoRoot, path));
    const text = buffer.toString('utf8');
    const parsed = rel.endsWith('.json') ? JSON.parse(text) : parseCsv(text);
    loaded[key] = parsed;
    provenance.push({
      path,
      href: `${repoUrl}/blob/main/${path}`,
      shape: Array.isArray(parsed) ? `${fmt(parsed.length)}행` : 'JSON',
      sha256: createHash('sha256').update(buffer).digest('hex'),
    });
  }
  return { loaded, provenance };
}

/* ---------- HTML 조각 ---------- */

function meterList(rows, { label: listLabel }) {
  const items = rows
    .map(
      (row) => `<li class="meter${row.emphasis ? ' meter--emphasis' : ''}">
  <span class="meter__label">${escapeHtml(row.label)}</span>
  <span class="meter__track" aria-hidden="true"><span class="meter__fill" style="--v:${row.share.toFixed(4)}%"></span></span>
  <span class="meter__value"><strong>${escapeHtml(row.value)}</strong> <span class="meter__count">${escapeHtml(row.count)}</span></span>
</li>`,
    )
    .join('\n');
  return `<ul class="meter-list" role="list" aria-label="${escapeHtml(listLabel)}">\n${items}\n</ul>`;
}

function barCell(pct, national, text) {
  return `<span class="bar-cell"><span class="bar-cell__track" aria-hidden="true"><span class="bar-cell__fill" style="--v:${pct.toFixed(4)}%"></span><span class="bar-cell__ref" style="--v:${national.toFixed(4)}%"></span></span><span class="bar-cell__value">${escapeHtml(text)}</span></span>`;
}

/* ---------- 빌드 ---------- */

export async function build({ repoRoot, repoUrl }) {
  const { loaded: src, provenance } = await loadSources(repoRoot, repoUrl);
  const facts = {};
  const tables = {};
  const fragments = {};
  const data = {};

  /* KOSIS 디지털정보격차 */
  if (src.kosis.length !== 240) fail(`KOSIS 셀 수가 240이 아니다: ${src.kosis.length}`);
  const kosis = new Map();
  for (const row of src.kosis) {
    const indicator = row.indicator.replace('digital_informatization_', '');
    kosis.set(`${indicator}|${row.population}|${row.survey_year}`, num(row.value, `${row.indicator} ${row.population} ${row.survey_year}`));
  }
  const kv = (indicator, population, year) => {
    const value = kosis.get(`${indicator}|${population}|${year}`);
    if (value === undefined) fail(`KOSIS 값 없음: ${indicator} ${population} ${year}`);
    return value;
  };

  data.kosis = {
    years: YEARS,
    overall: POPULATIONS.map((p) => ({ key: p.key, label: p.label, values: YEARS.map((y) => kv('overall', p.key, y)) })),
    disabled: INDICATORS.map((i) => ({ key: i.key, label: i.label, values: YEARS.map((y) => kv(i.key, 'disabled', y)) })),
    gaps: POPULATIONS.map((p) => ({
      key: p.key,
      label: p.label,
      access: kv('access', p.key, 2025),
      capability: kv('capability', p.key, 2025),
      utilization: kv('utilization', p.key, 2025),
    })),
  };

  for (const row of src.kosisGaps) {
    const indicator = row.indicator.replace('digital_informatization_', '');
    assertClose(`격차 ${indicator} ${row.population}`, round(100 - kv(indicator, row.population, 2025), 1), row.gap_index_points, 0.05);
  }

  for (const i of INDICATORS) {
    for (const y of [2016, 2021, 2024, 2025]) facts[`kosis.disabled.${i.key}.${y}`] = kv(i.key, 'disabled', y);
    facts[`kosis.disabled.${i.key}.diff1625`] = kv(i.key, 'disabled', 2025) - kv(i.key, 'disabled', 2016);
    facts[`kosis.disabled.${i.key}.diff1621`] = kv(i.key, 'disabled', 2021) - kv(i.key, 'disabled', 2016);
    facts[`kosis.disabled.${i.key}.diff2125`] = kv(i.key, 'disabled', 2025) - kv(i.key, 'disabled', 2021);
    facts[`kosis.gap.disabled.${i.key}`] = 100 - kv(i.key, 'disabled', 2025);
  }
  for (const p of POPULATIONS) {
    facts[`kosis.gap.${p.key}.capability`] = 100 - kv('capability', p.key, 2025);
    facts[`kosis.overall.${p.key}.diff1625`] = kv('overall', p.key, 2025) - kv('overall', p.key, 2016);
  }
  facts['kosis.access2025.min'] = Math.min(...POPULATIONS.map((p) => kv('access', p.key, 2025)));
  facts['kosis.cells'] = src.kosis.length;
  facts['kosis.primaryCells'] = src.kosis.filter((r) => Number(r.survey_year) >= 2016).length;
  facts['kosis.excludedCells'] = src.kosis.filter((r) => Number(r.survey_year) < 2016).length;

  const valueTable = (caption, series) => ({
    caption,
    columns: [{ label: '조사연도' }, ...series.map((s) => ({ label: s.label, numeric: true }))],
    rows: YEARS.map((y, i) => [String(y), ...series.map((s) => fmt(s.values[i], 1))]),
  });
  tables['kosis-overall-years'] = valueTable('집단별 디지털정보화 종합지수, 2016~2025년 (해당 연도 일반국민 = 100)', data.kosis.overall);
  tables['kosis-overall-change'] = {
    caption: '집단별 종합지수의 변화 요약 (지수 포인트)',
    columns: ['집단·집계', '2016', '2021', '2024', '2025', '2016→2025 차이', '연평균 포인트 변화', '2024→2025 차이'].map((label, i) => ({ label, numeric: i > 0 })),
    rows: POPULATIONS.map((p) => {
      const v = (y) => kv('overall', p.key, y);
      return [p.label, fmt(v(2016), 1), fmt(v(2021), 1), fmt(v(2024), 1), fmt(v(2025), 1), fmtSigned(v(2025) - v(2016), 1), fmtSigned((v(2025) - v(2016)) / 9, 2), fmtSigned(v(2025) - v(2024), 1)];
    }),
    note: '연평균 변화 = (2025년 값 − 2016년 값) ÷ 9년. 복리 증가율이나 회귀 추세 계수가 아니다.',
  };
  tables['kosis-disabled-years'] = valueTable('장애인의 디지털정보화 지표, 2016~2025년 (해당 연도 일반국민 = 100)', data.kosis.disabled);
  tables['kosis-disabled-change'] = {
    caption: '장애인 지표의 변화 요약 (지수 포인트)',
    columns: ['지표', '2016', '2021', '2024', '2025', '2016→2025', '2021→2025', '2024→2025'].map((label, i) => ({ label, numeric: i > 0 })),
    rows: INDICATORS.map((ind) => {
      const v = (y) => kv(ind.key, 'disabled', y);
      return [ind.label, fmt(v(2016), 1), fmt(v(2021), 1), fmt(v(2024), 1), fmt(v(2025), 1), fmtSigned(v(2025) - v(2016), 1), fmtSigned(v(2025) - v(2021), 1), fmtSigned(v(2025) - v(2024), 1)];
    }),
  };
  tables['kosis-gaps'] = {
    caption: '2025년 집단별 접근·역량·활용 지수와 역량의 일반국민 기준과 차이',
    columns: ['집단·집계', '접근 지수', '역량 지수', '활용 지수', '역량의 일반국민 기준과 차이'].map((label, i) => ({ label, numeric: i > 0 })),
    rows: data.kosis.gaps.map((g) => [g.label, fmt(g.access, 1), fmt(g.capability, 1), fmt(g.utilization, 1), fmt(100 - g.capability, 1)]),
  };

  /* 민간 웹 접근성 */
  const web = src.baseline
    .filter((r) => r.indicator === 'web_accessibility_score')
    .map((r) => ({ year: Number(r.survey_year), value: num(r.value, `web ${r.survey_year}`) }))
    .sort((a, b) => a.year - b.year);
  if (web.length !== 7 || web[0].year !== 2019 || web.at(-1).year !== 2025) fail('웹 접근성 연도 범위가 2019~2025가 아니다');
  data.web = web;
  for (const w of web) facts[`web.${w.year}`] = w.value;
  facts['web.diff2425'] = web.at(-1).value - web.at(-2).value;
  tables['web-scores'] = {
    caption: '민간 웹 접근성 실태조사 평균점수, 2019~2025년',
    columns: [{ label: '조사연도' }, { label: '평균점수', numeric: true }, { label: '전년 대비', numeric: true }],
    rows: web.map((w, i) => [String(w.year), fmt(w.value, 1), i ? fmtSigned(w.value - web[i - 1].value, 1) : '—']),
  };

  /* 행안부 무인민원발급기 */
  const flow = src.moisSummary.record_flow;
  facts['mois.received'] = flow.received_rows;
  facts['mois.inUse'] = flow.explicitly_in_use_records;
  facts['mois.notInUse'] = flow.explicitly_not_in_use_records;
  facts['mois.unknownUse'] = flow.unknown_use_records;
  facts['mois.sggCodes'] = src.moisSummary.data_quality.observed_installation_sgg_codes_n;
  const integrity = src.moisSummary.integrity;
  facts['mois.integrity.initialUnique'] = integrity.initial_paginated_unique_keys;
  facts['mois.integrity.repeated'] = integrity.initial_repeated_rows;
  facts['mois.integrity.groups'] = integrity.authority_partition_groups;
  facts['mois.integrity.leaves'] = integrity.leaf_partition_queries;
  facts['mois.integrity.queries'] = integrity.partition_queries_including_split_parents;
  facts['mois.integrity.total'] = integrity.global_total_rechecked;
  facts['mois.date.older365'] = src.moisSummary.data_quality.date_fields_in_use.LAST_MDFCN_PNT.older_than_365_days_n;
  const allYes = src.moisPatterns.find((row) => Object.keys(FEATURE_LABELS).every((field) => row[field] === 'yes'));
  facts['mois.allYes'] = allYes ? num(allYes.count, 'all yes') : 0;
  const features = src.moisSummary.national_features.map((f) => {
    const meta = FEATURE_LABELS[f.feature];
    if (!meta) fail(`알 수 없는 기능 필드: ${f.feature}`);
    if (f.yes + f.no + f.unknown !== f.in_use_records_n) fail(`기능 합계 불일치: ${f.feature}`);
    return { ...meta, field: f.feature, yes: f.yes, no: f.no, unknown: f.unknown, n: f.in_use_records_n, pct: (f.yes / f.in_use_records_n) * 100 };
  });
  for (const f of features) {
    facts[`mois.f.${f.key}.yes`] = f.yes;
    facts[`mois.f.${f.key}.no`] = f.no;
    facts[`mois.f.${f.key}.pct`] = f.pct;
  }
  facts['mois.f.unknownTotal'] = sum(features.map((f) => f.unknown));
  facts['mois.f.full'] = features.filter((f) => f.yes === f.n).length;
  const featureOrder = [...features].sort((a, b) => b.pct - a.pct || a.label.localeCompare(b.label, 'ko'));
  fragments['mois-features'] = meterList(
    featureOrder.map((f) => ({
      label: f.label,
      share: f.pct,
      value: fmtPct(f.pct, 2),
      count: `${fmt(f.yes)} / ${fmt(f.n)}건`,
      emphasis: f.pct < 100,
    })),
    { label: '기능별 제공 표시 비율, 사용 기재 5,800건 기준' },
  );
  tables['mois-features'] = {
    caption: '무인민원발급기 기능별 제공 표시 (분모: 사용 기재 기록)',
    columns: ['기능', '제공·가능', '미제공·불가능', '미상', '제공 비율'].map((label, i) => ({ label, numeric: i > 0 })),
    rows: features.map((f) => [f.label, fmt(f.yes), fmt(f.no), fmt(f.unknown), fmtPct(f.pct, 2)]),
  };

  const regions = src.moisRegions.map((r) => ({
    code: r.geography_code,
    label: r.display_label,
    n: num(r.in_use_records_n, 'region n'),
    wheelchairYes: num(r.wheelchair_yes, 'wheelchair yes'),
    wheelchairNo: num(r.wheelchair_no, 'wheelchair no'),
    wheelchairUnknown: num(r.wheelchair_unknown, 'wheelchair unknown'),
    tactileYes: num(r.tactile_yes, 'tactile yes'),
    tactileNo: num(r.tactile_no, 'tactile no'),
    tactileUnknown: num(r.tactile_unknown, 'tactile unknown'),
  }));
  if (sum(regions.map((r) => r.n)) !== flow.explicitly_in_use_records) fail('지역 합계가 사용 기재 수와 다르다');
  for (const r of regions) {
    r.wheelchairPct = (r.wheelchairYes / r.n) * 100;
    r.tactilePct = (r.tactileYes / r.n) * 100;
    facts[`mois.r.${r.code}.n`] = r.n;
    facts[`mois.r.${r.code}.wheelchairYes`] = r.wheelchairYes;
    facts[`mois.r.${r.code}.wheelchairNo`] = r.wheelchairNo;
    facts[`mois.r.${r.code}.wheelchairPct`] = r.wheelchairPct;
    facts[`mois.r.${r.code}.tactilePct`] = r.tactilePct;
  }
  facts['mois.regions'] = regions.length;
  const wheelchair = features.find((f) => f.key === 'wheelchair');
  const tactile = features.find((f) => f.key === 'tactile');
  const regionRows = [...regions].sort((a, b) => b.wheelchairPct - a.wheelchairPct || a.code.localeCompare(b.code));
  fragments['mois-regions'] = renderTable({
    caption: '지역 표시명 묶음별 휠체어 사용자 조작 가능·촉각 모니터 제공 표시 비율 (휠체어 조작 가능 비율이 높은 순)',
    className: 'bar-table',
    columns: [
      { label: '지역 표시명 (사용 기록)' },
      { label: `휠체어 사용자 조작 가능 · 전국 ${fmtPct(wheelchair.pct, 2)}` },
      { label: `촉각 모니터 제공 · 전국 ${fmtPct(tactile.pct, 2)}` },
    ],
    rows: regionRows.map((r) => [
      { text: r.label, sub: `${fmt(r.n)}건` },
      { text: '', cls: 'bar-td', html: true, raw: barCell(r.wheelchairPct, wheelchair.pct, fmtPct(r.wheelchairPct, 2)) },
      { text: '', cls: 'bar-td', html: true, raw: barCell(r.tactilePct, tactile.pct, fmtPct(r.tactilePct, 2)) },
    ]),
  }).replace(/<span class="cell-main"><\/span>/g, '');
  // barCell 마크업은 신뢰할 수 있는 내부 문자열이므로 표를 만든 뒤 자리를 채운다.
  {
    let i = 0;
    const cells = regionRows.flatMap((r) => [
      barCell(r.wheelchairPct, wheelchair.pct, fmtPct(r.wheelchairPct, 2)),
      barCell(r.tactilePct, tactile.pct, fmtPct(r.tactilePct, 2)),
    ]);
    fragments['mois-regions'] = fragments['mois-regions'].replace(/<td class="bar-td"><\/td>/g, () => `<td class="bar-td">${cells[i++]}</td>`);
    if (i !== cells.length) fail('지역 막대 셀 수가 맞지 않는다');
  }
  tables['mois-regions'] = {
    caption: '지역 표시명 묶음별 기능 표시 건수 (설치 시군구 코드 앞 두 자리 기준)',
    columns: ['코드', '지역 표시명', '사용 기록', '휠체어 가능', '휠체어 불가능', '휠체어 가능 비율', '촉각 제공', '촉각 미제공', '촉각 제공 비율'].map((label, i) => ({ label, numeric: i > 1 })),
    rows: regions.map((r) => [r.code, r.label, fmt(r.n), fmt(r.wheelchairYes), fmt(r.wheelchairNo), fmtPct(r.wheelchairPct, 2), fmt(r.tactileYes), fmt(r.tactileNo), fmtPct(r.tactilePct, 2)]),
    note: '두 기능의 미상은 모든 지역에서 0건이다. 비율의 분모는 지역별 사용 기재 기록이다.',
  };

  const pair = (w, t) => {
    const row = src.moisPairs.find((p) => p.wheelchair === w && p.tactile === t);
    if (!row) fail(`기능 조합 없음: ${w}/${t}`);
    return num(row.count, 'pair count');
  };
  const pairs = { yy: pair('yes', 'yes'), yn: pair('yes', 'no'), ny: pair('no', 'yes'), nn: pair('no', 'no') };
  const pairUnknown = sum(src.moisPairs.filter((p) => p.wheelchair === 'unknown' || p.tactile === 'unknown').map((p) => num(p.count, 'pair')));
  if (pairs.yy + pairs.yn + pairs.ny + pairs.nn + pairUnknown !== flow.explicitly_in_use_records) fail('기능 조합 합계 불일치');
  for (const [k, v] of Object.entries(pairs)) {
    facts[`mois.p.${k}`] = v;
    facts[`mois.p.${k}.pct`] = (v / flow.explicitly_in_use_records) * 100;
  }
  facts['mois.p.unknown'] = pairUnknown;
  const heat = (v) => {
    const share = v / flow.explicitly_in_use_records;
    const bin = share >= 0.5 ? 4 : share >= 0.2 ? 3 : share >= 0.05 ? 2 : 1;
    return { text: `${fmt(v)}건`, sub: fmtPct((v / flow.explicitly_in_use_records) * 100, 1), cls: `heat heat-${bin}` };
  };
  fragments['mois-pairs'] = renderTable({
    caption: '휠체어 사용자 조작 × 촉각 모니터, 사용 기재 5,800건의 동시 기재',
    className: 'heat-table',
    columns: [{ label: '휠체어 사용자 조작' }, { label: '촉각 모니터 제공' }, { label: '촉각 모니터 미제공' }],
    rows: [
      ['가능', heat(pairs.yy), heat(pairs.yn)],
      ['불가능', heat(pairs.ny), { ...heat(pairs.nn), cls: `${heat(pairs.nn).cls} heat--flag` }],
    ],
  });

  /* 조달청 납품요구 */
  const months = src.ppsMonthly
    .filter((r) => r.scope === 'core_kiosks')
    .map((r) => ({
      month: r.month,
      qty: num(r.representative_device_net_quantity, `qty ${r.month}`),
      amount: num(r.net_request_amount_krw, `amount ${r.month}`),
      requests: num(r.request_ids_with_changes, 'requests'),
      institutions: num(r.requesting_institutions, 'institutions'),
    }));
  const expectedMonths = [];
  for (let y = 2025, m = 1; y < 2026 || (y === 2026 && m <= 9); m === 12 ? ((y += 1), (m = 1)) : (m += 1)) {
    expectedMonths.push(`${y}-${String(m).padStart(2, '0')}`);
  }
  if (months.map((m) => m.month).join() !== expectedMonths.join()) fail('조달 월 범위가 2025-01~2026-09 연속이 아니다');
  const windowQty = (year, from, to) => sum(months.filter((m) => m.month.startsWith(`${year}-`) && Number(m.month.slice(5)) >= from && Number(m.month.slice(5)) <= to).map((m) => m.qty));
  const windowAmount = (year, from, to) => sum(months.filter((m) => m.month.startsWith(`${year}-`) && Number(m.month.slice(5)) >= from && Number(m.month.slice(5)) <= to).map((m) => m.amount));

  const S = src.ppsSummary;
  const cmp = S.same_month_comparisons;
  const windowDefs = [
    { key: 'febSep', label: '2~9월 · 주 비교', note: '전환월(1월) 제외', from: 2, to: 9, summary: cmp.feb_sep_primary },
    { key: 'sameDates', label: '1/22~9/30 · 같은 날짜 범위', note: '법정 시행일부터', summary: S.same_calendar_dates_from_legal_start },
    { key: 'janSep', label: '1~9월 · 전환월 포함', note: '1월 전체 포함', from: 1, to: 9, summary: cmp.jan_sep_including_transition_month },
    { key: 'febJun', label: '2~6월 · 중기업 의무 적용 전', note: '7/22 이전 구간', from: 2, to: 6, summary: cmp.feb_jun_before_medium_firm_phase },
  ];
  const windows = windowDefs.map((w) => {
    const q2025 = num(w.summary.before_2025.representative_device_net_quantity, 'q2025');
    const q2026 = num(w.summary.after_2026.representative_device_net_quantity, 'q2026');
    const a2025 = num(w.summary.before_2025.net_request_amount_krw, 'a2025');
    const a2026 = num(w.summary.after_2026.net_request_amount_krw, 'a2026');
    if (w.from) {
      assertClose(`${w.key} 2025 월 합계`, windowQty(2025, w.from, w.to), q2025);
      assertClose(`${w.key} 2026 월 합계`, windowQty(2026, w.from, w.to), q2026);
      assertClose(`${w.key} 2025 금액`, windowAmount(2025, w.from, w.to), a2025);
      assertClose(`${w.key} 2026 금액`, windowAmount(2026, w.from, w.to), a2026);
    }
    const reported = w.summary.changes?.representative_device_net_quantity?.percent_change;
    if (reported !== undefined) assertClose(`${w.key} 변화율`, round(pctChange(q2025, q2026), 1), reported, 0.05);
    facts[`pps.${w.key}.q2025`] = q2025;
    facts[`pps.${w.key}.q2026`] = q2026;
    facts[`pps.${w.key}.diff`] = q2026 - q2025;
    facts[`pps.${w.key}.pct`] = pctChange(q2025, q2026);
    facts[`pps.${w.key}.eok2025`] = toEok(a2025);
    facts[`pps.${w.key}.eok2026`] = toEok(a2026);
    facts[`pps.${w.key}.eokDiff`] = toEok(a2026 - a2025);
    facts[`pps.${w.key}.eokPct`] = pctChange(a2025, a2026);
    return { key: w.key, label: w.label, note: w.note, q2025, q2026, pct: pctChange(q2025, q2026), requests2025: w.summary.before_2025.request_ids_with_changes, requests2026: w.summary.after_2026.request_ids_with_changes, inst2025: w.summary.before_2025.requesting_institutions, inst2026: w.summary.after_2026.requesting_institutions, a2025, a2026 };
  });
  const main = windows[0];
  facts['pps.febSep.requests2025'] = main.requests2025;
  facts['pps.febSep.requests2026'] = main.requests2026;
  facts['pps.febSep.requestsDiff'] = main.requests2026 - main.requests2025;
  facts['pps.febSep.inst2025'] = main.inst2025;
  facts['pps.febSep.inst2026'] = main.inst2026;
  facts['pps.febSep.instDiff'] = main.inst2026 - main.inst2025;

  const cat = S.category_feb_sep_comparisons;
  facts['pps.cat.cert2025'] = num(cat['증명발급기'].before_2025.representative_device_net_quantity, 'cert');
  facts['pps.cat.cert2026'] = num(cat['증명발급기'].after_2026.representative_device_net_quantity, 'cert');
  facts['pps.cat.guide2025'] = num(cat['무인안내시스템'].before_2025.representative_device_net_quantity, 'guide');
  facts['pps.cat.guide2026'] = num(cat['무인안내시스템'].after_2026.representative_device_net_quantity, 'guide');
  if (facts['pps.cat.cert2025'] + facts['pps.cat.guide2025'] !== main.q2025) fail('품목별 합계(2025)가 주 비교와 다르다');
  if (facts['pps.cat.cert2026'] + facts['pps.cat.guide2026'] !== main.q2026) fail('품목별 합계(2026)가 주 비교와 다르다');

  const jan = S.january_transition_detail;
  const january = ['2025', '2026'].map((year) => {
    const early = num(jan[year].days_01_21.representative_device_net_quantity, 'jan early');
    const late = num(jan[year].days_22_31.representative_device_net_quantity, 'jan late');
    const monthRow = months.find((m) => m.month === `${year}-01`);
    if (early + late !== monthRow.qty) fail(`${year}년 1월 분할 합계가 월 합계와 다르다`);
    facts[`pps.jan.${year}.total`] = monthRow.qty;
    facts[`pps.jan.${year}.early`] = early;
    facts[`pps.jan.${year}.late`] = late;
    return { year, early, late, total: monthRow.qty };
  });
  const byQty = [...months].sort((a, b) => b.qty - a.qty);
  const peak = byQty[0];
  facts['pps.peak.qty'] = peak.qty;
  facts['pps.second.qty'] = byQty[1].qty;
  if (peak.month !== '2025-12' || byQty[1].month !== '2026-01') fail('월별 최대 두 달이 본문(2025-12, 2026-01)과 다르다');
  facts['pps.2025-12.qty'] = months.find((m) => m.month === '2025-12').qty;

  const reg = S.registrations;
  facts['pps.reg.all.rows'] = reg.all_class.contract_product_registration_rows;
  facts['pps.reg.all.ids'] = reg.all_class.distinct_product_ids;
  facts['pps.reg.core.rows'] = reg.core.contract_product_registration_rows;
  facts['pps.reg.core.ids'] = reg.core.distinct_product_ids;
  facts['pps.reg.febSep.2025'] = reg.core_feb_sep_by_year['2025'].distinct_product_ids;
  facts['pps.reg.febSep.2026'] = reg.core_feb_sep_by_year['2026'].distinct_product_ids;
  facts['pps.callsReg'] = S.quality.registration_calls;
  facts['pps.callsDel'] = S.quality.delivery_calls;
  facts['pps.deliveryRows'] = S.quality.delivery_rows;

  const policyEvents = src.events.map((e, i) => {
    const text = EVENT_TEXT[e.event_date];
    if (!text) fail(`정책 일정 문구가 없다: ${e.event_date} ${e.event}`);
    if (!ROLE_LABEL[e.role]) fail(`알 수 없는 사건 역할: ${e.role}`);
    return { n: i + 1, date: e.event_date, label: text[0], impact: text[1], role: e.role, roleLabel: ROLE_LABEL[e.role], source: e.source_url };
  });
  if (policyEvents.length !== Object.keys(EVENT_TEXT).length) fail('정책 일정 수가 문서 표와 다르다');
  facts['events.count'] = policyEvents.length;

  data.pps = {
    months: months.map((m) => ({ month: m.month, qty: m.qty, eok: round(toEok(m.amount), 2), requests: m.requests, institutions: m.institutions })),
    windows: windows.map((w) => ({ key: w.key, label: w.label, note: w.note, q2025: w.q2025, q2026: w.q2026, pct: round(w.pct, 1) })),
    january,
    events: policyEvents.filter((e) => e.date <= '2026-09-30').map(({ n, date, label, role, roleLabel }) => ({ n, date, label, role, roleLabel })),
  };

  fragments['policy-timeline'] = `<ol class="timeline" role="list">
${policyEvents
  .map(
    (e) => `<li class="timeline__item timeline__item--${escapeHtml(e.role)}">
  <span class="timeline__n" aria-hidden="true">${e.n}</span>
  <div class="timeline__body">
    <p class="timeline__head"><time datetime="${escapeHtml(e.date)}">${escapeHtml(e.date)}</time> <span class="tag tag--${escapeHtml(e.role)}">${escapeHtml(e.roleLabel)}</span></p>
    <p class="timeline__event">${escapeHtml(e.label)}</p>
    <p class="timeline__impact">${escapeHtml(e.impact)}</p>
  </div>
</li>`,
  )
  .join('\n')}
</ol>`;

  tables['pps-monthly'] = {
    caption: '월별 납품요구 순증, 증명발급기·무인안내시스템 (접수월 기준)',
    columns: ['접수월', '순증 수량(대)', '순증 금액(억원)', '변경이 관측된 요구번호', '관련 수요기관'].map((label, i) => ({ label, numeric: i > 0 })),
    rows: months.map((m) => [monthLabel(m.month), fmt(m.qty), fmt(toEok(m.amount), 2), fmt(m.requests), fmt(m.institutions)]),
  };
  tables['pps-main'] = {
    caption: '같은 2~9월 비교: 증명발급기·무인안내시스템 납품요구',
    columns: ['주 분석 품목', '2025년 2~9월', '2026년 2~9월', '차이'].map((label, i) => ({ label, numeric: i > 0 })),
    rows: [
      ['납품요구 순증 수량', `${fmt(main.q2025)}대`, `${fmt(main.q2026)}대`, `${fmtSigned(main.q2026 - main.q2025)}대, ${fmtSignedPct(main.pct, 1)}`],
      ['납품요구 순증 금액', `${fmt(toEok(main.a2025), 2)}억원`, `${fmt(toEok(main.a2026), 2)}억원`, `${fmtSigned(toEok(main.a2026 - main.a2025), 2)}억원, ${fmtSignedPct(pctChange(main.a2025, main.a2026), 1)}`],
      ['변경이 관측된 요구번호', `${fmt(main.requests2025)}개`, `${fmt(main.requests2026)}개`, `${fmtSigned(main.requests2026 - main.requests2025)}개`],
      ['관련 요구가 있는 수요기관', `${fmt(main.inst2025)}곳`, `${fmt(main.inst2026)}곳`, `${fmtSigned(main.inst2026 - main.inst2025)}곳`],
    ],
  };
  tables['pps-windows'] = {
    caption: '비교 기간별 납품요구 순증 수량',
    columns: ['비교 기간', '2025년 순증 수량', '2026년 순증 수량', '변화율'].map((label, i) => ({ label, numeric: i > 0 })),
    rows: windows.map((w) => [w.label, `${fmt(w.q2025)}대`, `${fmt(w.q2026)}대`, fmtSignedPct(w.pct, 1)]),
  };
  tables['pps-january'] = {
    caption: '1월 납품요구 순증의 날짜별 구분',
    columns: ['연도', '1~21일', '22~31일', '1월 전체'].map((label, i) => ({ label, numeric: i > 0 })),
    rows: january.map((j) => [`${j.year}년`, `${fmt(j.early)}대`, `${fmt(j.late)}대`, `${fmt(j.total)}대`]),
  };
  const byCat = reg.by_product_category;
  tables['pps-registrations'] = {
    caption: '2025-01~2026-09 계약·물품 등록 자료',
    columns: ['품목', '계약·물품 등록 행', '고유 물품 ID'].map((label, i) => ({ label, numeric: i > 0 })),
    rows: [
      ['컴퓨터키오스크 전체', fmt(reg.all_class.contract_product_registration_rows), fmt(reg.all_class.distinct_product_ids)],
      ...['증명발급기', '무인안내시스템', '버스및차량정보안내장치'].map((name) => [name, fmt(byCat[name].contract_product_registration_rows), fmt(byCat[name].distinct_product_ids)]),
    ],
  };

  /* 기관·제품별 분해 (2026-10-04 추가) */
  const cohortLabel = { both: '두 해 모두 기록', '2025_only': '2025년에만 기록', '2026_only': '2026년에만 기록' };
  const cohorts = src.ppsCohorts.map((c) => ({
    key: c.presence,
    label: cohortLabel[c.presence] ?? fail(`알 수 없는 기관 구분: ${c.presence}`),
    institutions: num(c.institutions, 'institutions'),
    q2025: num(c.quantity_2025, 'q2025'),
    q2026: num(c.quantity_2026, 'q2026'),
    diff: num(c.quantity_difference, 'diff'),
  }));
  if (sum(cohorts.map((c) => c.q2025)) !== main.q2025 || sum(cohorts.map((c) => c.q2026)) !== main.q2026) fail('기관 구분 합계가 주 비교와 다르다');
  for (const c of cohorts) {
    facts[`cohort.${c.key}.institutions`] = c.institutions;
    facts[`cohort.${c.key}.q2025`] = c.q2025;
    facts[`cohort.${c.key}.q2026`] = c.q2026;
    facts[`cohort.${c.key}.diff`] = c.diff;
  }
  facts['cohort.institutionsTotal'] = sum(cohorts.map((c) => c.institutions));
  data.cohorts = { start: main.q2025, end: main.q2026, steps: cohorts.map(({ key, label, institutions, diff }) => ({ key, label, institutions, diff })) };

  const institutions = src.ppsInstitutions.map((r) => ({
    id: r.id,
    name: r.names,
    q2025: num(r.quantity_2025, 'inst q2025'),
    q2026: num(r.quantity_2026, 'inst q2026'),
    diff: num(r.quantity_difference, 'inst diff'),
  }));
  const decreases = institutions.filter((r) => r.diff < 0).sort((a, b) => a.diff - b.diff || a.id.localeCompare(b.id));
  const increases = institutions.filter((r) => r.diff > 0).sort((a, b) => b.diff - a.diff || a.id.localeCompare(b.id));
  const top5 = decreases.slice(0, 5);
  const decreaseTotal = sum(decreases.map((r) => r.diff));
  const increaseTotal = sum(increases.map((r) => r.diff));
  if (decreaseTotal + increaseTotal !== main.q2026 - main.q2025) fail('기관별 증감 합계가 순감소와 다르다');
  const shortName = (name) => name.replace(/^서울특별시 /, '').replace(/^경기도 /, '');
  top5.forEach((r, i) => {
    facts[`inst.top${i + 1}.q2025`] = r.q2025;
    facts[`inst.top${i + 1}.q2026`] = r.q2026;
    facts[`inst.top${i + 1}.diff`] = r.diff;
  });
  increases.slice(0, 2).forEach((r, i) => {
    facts[`inst.inc${i + 1}.q2025`] = r.q2025;
    facts[`inst.inc${i + 1}.q2026`] = r.q2026;
  });
  facts['inst.top5.sum'] = sum(top5.map((r) => r.diff));
  facts['inst.decreaseTotal'] = decreaseTotal;
  facts['inst.increaseTotal'] = increaseTotal;
  facts['inst.top5.shareOfDecrease'] = (sum(top5.map((r) => r.diff)) / decreaseTotal) * 100;
  facts['inst.top5.shareOfNet'] = (sum(top5.map((r) => r.diff)) / (main.q2026 - main.q2025)) * 100;
  data.institutions = {
    decreases: top5.map((r) => ({ label: shortName(r.name), full: r.name, q2025: r.q2025, q2026: r.q2026 })),
    increases: increases.slice(0, 2).map((r) => ({ label: shortName(r.name), full: r.name, q2025: r.q2025, q2026: r.q2026 })),
  };

  const products = FOCUS_PRODUCTS.map((id) => {
    const row = src.ppsProducts.find((p) => p.id === id) ?? fail(`제품 ID 없음: ${id}`);
    const [category, maker, model, desc] = row.names.split(',').map((s) => s.trim());
    return { id, category, maker, model, desc, q2025: num(row.quantity_2025, 'p q2025'), q2026: num(row.quantity_2026, 'p q2026') };
  });
  products.forEach((p) => {
    facts[`product.${p.id}.q2025`] = p.q2025;
    facts[`product.${p.id}.q2026`] = p.q2026;
    facts[`product.${p.id}.diff`] = p.q2026 - p.q2025;
  });
  data.products = products.map((p) => ({ label: p.model, sub: `${p.maker} · ${p.desc}`, q2025: p.q2025, q2026: p.q2026 }));

  tables.cohorts = {
    caption: '기간 내 기록 존재별 기관 수와 순증 수량 (2~9월)',
    columns: ['기간 내 기록 존재', '기관 수', '2025년 순증 수량', '2026년 순증 수량', '차이'].map((label, i) => ({ label, numeric: i > 0 })),
    rows: [
      ...cohorts.map((c) => [c.label, `${fmt(c.institutions)}곳`, fmt(c.q2025), fmt(c.q2026), fmtSigned(c.diff)]),
      ['전체', `${fmt(facts['cohort.institutionsTotal'])}개 코드의 합집합`, fmt(main.q2025), fmt(main.q2026), fmtSigned(main.q2026 - main.q2025)],
    ],
  };
  tables.institutions = {
    caption: '순증 수량 감소 상위 5개 기관과 증가 사례 (2~9월)',
    columns: ['기관', '2025년', '2026년', '차이'].map((label, i) => ({ label, numeric: i > 0 })),
    rows: [...top5, ...increases.slice(0, 2)].map((r) => [r.name, fmt(r.q2025), fmt(r.q2026), fmtSigned(r.diff)]),
  };
  tables.products = {
    caption: '제품 식별번호별 순증 수량 (2~9월)',
    columns: ['제품 식별번호', '모델 · 제조사', '2025년', '2026년', '차이'].map((label, i) => ({ label, numeric: i > 1 })),
    rows: products.map((p) => [p.id, `${p.model} · ${p.maker}`, fmt(p.q2025), fmt(p.q2026), fmtSigned(p.q2026 - p.q2025)]),
    rowHeader: true,
  };

  /* 과거 NIA 검증 목록 (재계산 집계) */
  const composition = (dimension) => src.registry.filter((r) => r.dimension === dimension).map((r) => ({ label: r.label, count: num(r.count, 'registry'), denominator: num(r.denominator_models, 'den') }));
  const yearsRegistry = composition('registration_number_year');
  const total = yearsRegistry[0].denominator;
  if (sum(yearsRegistry.map((r) => r.count)) !== total) fail('등록번호 연도별 합계가 771이 아니다');
  facts['registry.total'] = total;
  for (const r of yearsRegistry) {
    facts[`registry.y${r.label}`] = r.count;
    facts[`registry.y${r.label}.share`] = (r.count / total) * 100;
  }
  const yr = Object.fromEntries(yearsRegistry.map((r) => [r.label, r.count]));
  facts['registry.diff2526'] = yr['2026'] - yr['2025'];
  facts['registry.pct2526'] = pctChange(yr['2025'], yr['2026']);
  facts['registry.diff2425'] = yr['2025'] - yr['2024'];
  data.registry = { years: yearsRegistry.map((r) => ({ label: r.label, value: r.count, partial: r.label === '2026' })) };

  const companies = composition('company_type');
  const companyRows = COMPANY_TYPES.map((t) => {
    const count = sum(t.labels.map((l) => (companies.find((c) => c.label === l) ?? fail(`기업유형 없음: ${l}`)).count));
    return { label: t.label, count, share: (count / total) * 100 };
  });
  if (sum(companyRows.map((r) => r.count)) !== total) fail('기업유형 합계가 771이 아니다');
  companyRows.forEach((r, i) => {
    facts[`registry.company${i}`] = r.count;
    facts[`registry.company${i}.share`] = r.share;
  });
  const productRows = composition('product_class').map((r) => ({ label: PRODUCT_CLASSES[r.label] ?? fail(`제품분류 없음: ${r.label}`), key: r.label, count: r.count, share: (r.count / total) * 100 }));
  if (sum(productRows.map((r) => r.count)) !== total) fail('제품분류 합계가 771이 아니다');
  for (const r of productRows) {
    facts[`registry.product.${r.key}`] = r.count;
    facts[`registry.product.${r.key}.share`] = r.share;
  }
  const top5Classes = productRows.filter((r) => r.key !== 'remaining_classes');
  facts['registry.product.top5'] = sum(top5Classes.map((r) => r.count));
  facts['registry.product.top5.share'] = (sum(top5Classes.map((r) => r.count)) / total) * 100;
  const shareList = (rows, label) =>
    meterList(rows.map((r) => ({ label: r.label, share: r.share, value: fmtPct(r.share, 1), count: `${fmt(r.count)}개 모델` })), { label });
  fragments['registry-company'] = shareList(companyRows, '기업유형별 모델 수, 771개 모델 기준');
  fragments['registry-product'] = shareList(productRows, '제품분류별 모델 수, 771개 모델 기준');
  tables['registry-years'] = {
    caption: '등록번호 연도별 당시 목록의 모델 수 (2026-09-30 기록, 771개 모델)',
    columns: ['등록번호의 연도', '모델 수', '전체 771건 중 비중'].map((label, i) => ({ label, numeric: i > 0 })),
    rows: yearsRegistry.map((r) => [r.label === '2026' ? '2026 (7/30 발급분까지)' : r.label, fmt(r.count), fmtPct((r.count / total) * 100, 1)]),
  };

  /* 보고서와 KOSIS 대조 */
  const compare = src.kosisCompare;
  const statusCount = (s) => compare.filter((r) => r.status === s).length;
  facts['rc.cells'] = compare.length;
  facts['rc.match'] = statusCount('match');
  facts['rc.diff'] = compare.length - statusCount('match');
  const mismatches = compare.filter((r) => r.status !== 'match');
  if (mismatches.length !== 1) fail(`대조 불일치 셀이 1개가 아니다: ${mismatches.length}`);
  facts['rc.report'] = num(mismatches[0].report_value, 'report');
  facts['rc.api'] = num(mismatches[0].api_value, 'api');
  facts['rc.delta'] = num(mismatches[0].api_minus_report_index_points, 'delta');
  const rcYears = [...new Set(compare.map((r) => r.survey_year))].sort();
  const rcRows = [];
  for (const ind of INDICATORS) {
    for (const p of POPULATIONS) {
      const cells = rcYears.map((y) => {
        const row = compare.find((r) => r.indicator === `digital_informatization_${ind.key}` && r.population === p.key && r.survey_year === y);
        if (!row) fail(`대조 셀 없음: ${ind.key} ${p.key} ${y}`);
        return row.status === 'match'
          ? { text: fmt(num(row.api_value, 'api'), 1), cls: 'rc rc--match' }
          : { text: fmt(num(row.api_value, 'api'), 1), sub: `보고서 ${fmt(num(row.report_value, 'rep'), 1)}`, cls: 'rc rc--diff' };
      });
      rcRows.push([`${ind.label} · ${p.label}`, ...cells]);
    }
  }
  fragments['rc-matrix'] = renderTable({
    caption: '디지털정보화 지표 100개 셀의 KOSIS 응답값 (2021~2025년, 보고서와 다른 셀은 보고서 값을 함께 표시)',
    className: 'rc-matrix',
    columns: [{ label: '지표 · 집단' }, ...rcYears.map((y) => ({ label: y, numeric: true }))],
    rows: rcRows,
  });

  /* 이 페이지가 읽은 파일 */
  tables.provenance = {
    caption: '이 페이지를 생성할 때 읽은 분석 파일',
    columns: [{ label: '파일' }, { label: '형식' }, { label: 'SHA-256 앞 12자리' }],
    rows: provenance.map((p) => [{ text: p.path, href: p.href }, p.shape, p.sha256.slice(0, 12)]),
  };

  /* 자료별 관측 시점 (1장 그림) */
  const registryObserved = src.summary.registry_observed_on;
  const moisSnapshot = src.moisSummary.snapshot_date_kst;
  const [ppsStart, ppsEnd] = S.period;
  facts['coverage.registryObserved'] = Number(registryObserved.slice(0, 4));
  data.coverage = {
    law: { date: '2026-01-22', label: '디지털포용법 시행 2026-01-22' },
    domain: ['2016-01-01', '2027-01-01'],
    rows: [
      { label: 'KOSIS 디지털정보격차', years: YEARS, span: `조사연도 ${YEARS[0]}~${YEARS.at(-1)}, 연 1회`, after: '없음' },
      { label: '민간 웹 접근성 실태조사', years: web.map((w) => w.year), span: `조사연도 ${web[0].year}~${web.at(-1).year}, 연 1회`, after: '없음' },
      { label: '과거 NIA 검증 목록', start: '2023-01-01', end: '2026-07-30', partial: true, point: registryObserved, span: `등록번호 연도 2023~2026(2026년은 7/30 발급분까지), ${registryObserved} 기록`, after: '2026년 표기 부분집계, 최초 발급 이력 미검증' },
      { label: '조달청 납품요구', start: ppsStart, end: ppsEnd, span: `${ppsStart.slice(0, 7)}~${ppsEnd.slice(0, 7)} 접수월`, after: '있음 (구매 요청·변경 기록)' },
      { label: '행안부 무인민원발급기', point: moisSnapshot, span: `${moisSnapshot} 수집, 현재 상태 1회`, after: '현재 상태만, 과거 이력 없음' },
    ],
  };

  tables.coverage = {
    caption: '자료별 관측 범위와 시행 후 관측 여부',
    columns: [{ label: '자료' }, { label: '관측 범위' }, { label: '시행 후 관측' }],
    rows: data.coverage.rows.map((r) => [r.label, r.span, r.after]),
  };

  data.hero = {
    disabledOverall: data.kosis.disabled[0].values,
    wheelchairNoShare: (wheelchair.no / wheelchair.n) * 100,
    months: months.map((m) => ({ month: m.month, qty: m.qty })),
  };
  data.meta = { repoUrl };

  return { data, tables, fragments, facts };
}

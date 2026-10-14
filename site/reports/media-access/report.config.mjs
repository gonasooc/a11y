// 영상 접근성 보고서의 생성 구역 데이터. site/scripts/generate.mjs가 불러 쓴다.
// analyses/media-access의 입력·출력만 읽어 차트 JSON, 정적 표, 본문 숫자 검사값(facts)을 만든다.
// 해석 문장은 index.html에 사람이 쓰고, 여기서는 계산과 형식만 맡는다.
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import format from '../../assets/js/format.js';
import { parseCsv } from '../../scripts/lib/csv.mjs';

const { fmt } = format;

const ANALYSIS_DIR = 'analyses/media-access';
const SOURCES = {
  compliance: 'outputs/broadcast_compliance_by_year.csv',
  groups: 'outputs/broadcast_group_summary.csv',
  official: 'outputs/broadcast_official_check.csv',
  summary: 'outputs/broadcast_summary.json',
  rerun: 'data/broadcast_ad_rerun.csv',
  operators: 'data/broadcast_operator_years.csv',
  context: 'data/context_facts_2026-10-13.csv',
};
const SERVICES = [
  { key: 'cc', label: '폐쇄자막', who: '청각장애인' },
  { key: 'ad', label: '화면해설', who: '시각장애인' },
  { key: 'ksl', label: '한국수어', who: '수어를 쓰는 농인' },
];
const YEARS = Array.from({ length: 9 }, (_, i) => 2017 + i);
const LATEST = 2025;
const CTX_GRADES = { research_grade_A: 'A', research_grade_B: 'B' };
const CTX_UNITS = { persons: '명', percent: '%', apps: '곳', operators: '곳', works: '개 작품', hours: '시간', seats: '석' };

function fail(message) {
  throw new Error(`[media-access] ${message}`);
}
const num = (value, label) => {
  const n = Number(value);
  if (value === '' || value == null || !Number.isFinite(n)) fail(`숫자가 아닌 값: ${label} = ${value}`);
  return n;
};

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

export async function build({ repoRoot, repoUrl }) {
  const { loaded: src, provenance } = await loadSources(repoRoot, repoUrl);
  const facts = {};
  const tables = {};
  const fragments = {};
  const data = {};

  /* 연도별 미달 사업자 */
  const comp = new Map(src.compliance.map((r) => [`${r.year}.${r.service}`, r]));
  const c = (year, service) => comp.get(`${year}.${service}`) ?? fail(`미달 요약 없음: ${year} ${service}`);
  for (const year of YEARS) {
    for (const s of SERVICES) {
      const row = c(year, s.key);
      facts[`bc.${s.key}.below.${year}`] = num(row.below_target, `${year} ${s.key} below`);
      facts[`bc.${s.key}.operators.${year}`] = num(row.operators, `${year} operators`);
    }
    const cc = c(year, 'cc');
    facts[`bc.cc.under01.${year}`] = num(cc.shortfall_under_0_1pctp, `${year} under01`);
    facts[`bc.cc.over1.${year}`] = num(cc.shortfall_1pctp_or_more, `${year} over1`);
    if (cc.largest_shortfall_pctp) facts[`bc.cc.maxGap.${year}`] = num(cc.largest_shortfall_pctp, `${year} maxGap`);
  }
  const ccBelow = YEARS.map((y) => facts[`bc.cc.below.${y}`]);
  const since2018 = ccBelow.slice(1);
  facts['bc.cc.belowMin1825'] = Math.min(...since2018);
  facts['bc.cc.belowMax1825'] = Math.max(...since2018);
  facts['bc.adksl.below2225'] = [2022, 2023, 2024, 2025].reduce((sum, y) => sum + facts[`bc.ad.below.${y}`] + facts[`bc.ksl.below.${y}`], 0);
  if (facts['bc.adksl.below2225'] !== 0) fail('2022~2025년 화면해설·한국수어 미달이 0이 아니다. 본문 문장을 다시 쓴다');

  // 본문에 쓰는 기준값. analyses/media-access/broadcast_analyze.py의 미달 폭 구간과 같다.
  facts['bc.small'] = 0.1;
  facts['bc.large'] = 1;

  data.ccBelow = YEARS.map((y) => ({
    key: String(y),
    label: String(y),
    shortLabel: `’${String(y).slice(2)}`,
    value: facts[`bc.cc.below.${y}`],
    note: y <= 2018 ? '원문이 소수 첫째 자리까지만 공개' : `0.1%p 미만 미달 ${fmt(facts[`bc.cc.under01.${y}`])}곳`,
  }));
  tables['cc-below'] = {
    caption: '폐쇄자막 의무에 못 미친 방송사, 2017~2025년',
    columns: [
      { label: '연도' },
      { label: '의무 방송사', numeric: true },
      { label: '미달', numeric: true },
      { label: '그중 0.1%p 미만', numeric: true },
      { label: '그중 1%p 이상', numeric: true },
      { label: '가장 크게 모자란 폭', numeric: true },
    ],
    rows: YEARS.map((y) => [
      String(y),
      `${fmt(facts[`bc.cc.operators.${y}`])}곳`,
      `${fmt(facts[`bc.cc.below.${y}`])}곳`,
      y <= 2018 ? '—' : `${fmt(facts[`bc.cc.under01.${y}`])}곳`,
      `${fmt(facts[`bc.cc.over1.${y}`])}곳`,
      facts[`bc.cc.maxGap.${y}`] == null ? '—' : `${src.compliance.find((r) => r.year === String(y) && r.service === 'cc').largest_shortfall_pctp}%p`,
    ]),
    note: '2017·2018년 원문은 실적을 소수 첫째 자리까지만 실어 0.1%p 미만의 미달이 드러나지 않는다(—). 미달은 실적이 목표보다 작은 경우다.',
  };

  /* 2025년 사업자군 평균 */
  const group = (year, name) => src.groups.find((g) => g.year === String(year) && g.group === name) ?? fail(`사업자군 없음: ${year} ${name}`);
  const terr = group(LATEST, '지상파');
  for (const s of SERVICES) {
    facts[`bc.terr.${s.key}.mean`] = num(terr[`${s.key}_actual_mean`], `terr ${s.key}`);
    facts[`bc.terr.${s.key}.target`] = num(terr[`${s.key}_targets`], `terr ${s.key} target`);
  }
  facts['bc.terr.operators'] = num(terr.operators, 'terr operators');
  data.terrestrial = SERVICES.map((s) => ({
    key: s.key,
    label: s.label,
    value: facts[`bc.terr.${s.key}.mean`],
    cls: 's1',
  }));
  tables['terrestrial'] = {
    caption: `지상파 ${fmt(facts['bc.terr.operators'])}곳의 장애인방송 의무 비율과 실적 평균, ${LATEST}년 (방송시간 대비 %)`,
    columns: [{ label: '서비스' }, { label: '주로 필요한 사람' }, { label: '의무 비율', numeric: true }, { label: '실적 평균', numeric: true }],
    rows: SERVICES.map((s) => [s.label, s.who, `${fmt(facts[`bc.terr.${s.key}.target`])}%`, `${fmt(facts[`bc.terr.${s.key}.mean`], 2)}%`]),
    note: '실적 평균은 방송사별 실적의 단순 평균이다(소수 둘째 자리 반올림).',
  };

  /* 2025년 미달 12곳 */
  const latestOps = src.operators.filter((r) => r.year === String(LATEST) && r.row_kind === 'operator');
  facts['bc.operators.latest'] = latestOps.length;
  const ccMiss = latestOps.filter((r) => Number(r.cc_actual) < Number(r.cc_target));
  if (ccMiss.length !== facts[`bc.cc.below.${LATEST}`]) fail('2025년 폐쇄자막 미달 수가 요약과 다르다');
  facts['bc.cc.missMinActual'] = Math.min(...ccMiss.map((r) => Number(r.cc_actual)));
  facts['bc.cc.missMaxActual'] = Math.max(...ccMiss.map((r) => Number(r.cc_actual)));
  if (!ccMiss.every((r) => r.group === '지상파' && Number(r.cc_target) === 100)) fail('2025년 폐쇄자막 미달이 모두 목표 100%인 지상파가 아니다');

  /* 화면해설 재방송 */
  const rerunLatest = src.rerun.filter((r) => r.year === String(LATEST));
  data.rerun = rerunLatest
    .map((r) => ({ key: r.operator, label: r.operator, value: num(r.rerun_share_pct, `rerun ${r.operator}`) }))
    .sort((a, b) => b.value - a.value)
    .map((d) => ({ ...d, cls: d.value >= 20 ? 's1' : 'muted' }));
  facts['rr.limit'] = 25;
  facts['rr.threshold'] = 20;
  facts['rr.max'] = Math.max(...data.rerun.map((d) => d.value));
  facts['rr.at20'] = data.rerun.filter((d) => d.value >= 20).length;
  facts['rr.zero'] = data.rerun.filter((d) => d.value === 0).length;
  facts['rr.operators'] = data.rerun.length;
  const kbs = rerunLatest.find((r) => r.operator === 'KBS') ?? fail('2025년 KBS 재방송 행 없음');
  facts['rr.kbs.required'] = num(kbs.required_minutes, 'kbs required');
  facts['rr.kbs.rerun'] = num(kbs.rerun_minutes, 'kbs rerun');
  facts['rr.kbs.share'] = num(kbs.rerun_share_pct, 'kbs share');
  const byYear = src.summary.ad_rerun;
  facts['rr.at20.min'] = Math.min(...Object.values(byYear).map((y) => y.at_least_20_pct));
  facts['rr.at20.max'] = Math.max(...Object.values(byYear).map((y) => y.at_least_20_pct));
  facts['rr.overLimit'] = Object.values(byYear).reduce((sum, y) => sum + y.over_limit, 0);
  tables['rerun'] = {
    caption: `화면해설 의무 편성 가운데 재방송 비율, ${LATEST}년 (상한 25%)`,
    columns: [{ label: '방송사' }, { label: '의무 편성(분)', numeric: true }, { label: '재방송(분)', numeric: true }, { label: '재방송 비율', numeric: true }],
    rows: [...rerunLatest]
      .sort((a, b) => Number(b.rerun_share_pct) - Number(a.rerun_share_pct))
      .map((r) => [r.operator, fmt(num(r.required_minutes, 'req')), r.rerun_minutes === 'NA' ? '없음' : fmt(num(r.rerun_minutes, 'rerun')), `${r.rerun_share_pct}%`]),
    note: '상한은 장애인방송 고시 제6조⑥이 지상파 중앙 4사와 종편·보도 PP에 적용한다.',
  };

  /* 공식 발표와의 대조 */
  const official = src.summary.official_group_means;
  facts['oc.2025.checked'] = official['2025'].checked;
  facts['oc.2025.match'] = official['2025'].match_truncated + official['2025'].match_rounded;
  facts['oc.2023.checked'] = official['2023'].checked;
  facts['oc.2023.differ'] = official['2023'].differ;
  const pp = src.official.find((r) => r.year === '2023' && r.official_group === '일반PP(10개사)' && r.service === 'ad') ?? fail('2023 일반PP 화면해설 대조 없음');
  facts['oc.2023.ppAd.official'] = num(pp.official_actual, 'pp official');
  facts['oc.2023.ppAd.computed'] = num(pp.computed_rounded, 'pp computed');
  tables['official'] = {
    caption: '공식 사업자군 평균과 방송사별 파일 계산의 대조',
    columns: [{ label: '연도' }, { label: '대조한 값', numeric: true }, { label: '일치', numeric: true }, { label: '다름', numeric: true }],
    rows: ['2023', '2025'].map((y) => [y, fmt(official[y].checked), fmt(official[y].match_truncated + official[y].match_rounded), fmt(official[y].differ)]),
    note: '공식 표는 단순 평균을 소수 둘째 자리에서 버린 값이다. 2023년 차이의 원인은 확인하지 못했다.',
  };

  /* 조사 문서에서 가져온 숫자 (docs/media-access·docs/digital-inclusion, A·B 등급) */
  const ctx = new Map();
  for (const row of src.context) {
    const grade = CTX_GRADES[row.verification_status];
    if (!grade) fail(`본문에 쓸 수 없는 등급: ${row.indicator} ${row.population} = ${row.verification_status}`);
    if (!/^https:\/\//.test(row.source_url)) fail(`출처 주소가 없다: ${row.indicator} ${row.population}`);
    if (!CTX_UNITS[row.unit]) fail(`알 수 없는 단위: ${row.unit}`);
    const key = `${row.indicator}.${row.population}.${row.survey_year}`;
    if (ctx.has(key)) fail(`중복된 조사 숫자: ${key}`);
    const value = num(row.value, key);
    ctx.set(key, { ...row, key, value, grade, digits: (row.value.split('.')[1] ?? '').length });
    facts[`ctx.${key}`] = value;
  }
  const cv = (key) => (ctx.get(key) ?? fail(`조사 숫자 없음: ${key}`)).value;
  facts['ctx.hearing10k'] = cv('registered_by_type.hearing.2025') / 10000;
  facts['ctx.visual10k'] = cv('registered_by_type.visual.2025') / 10000;
  facts['ctx.visualNotSevereShare'] = (cv('registered_visual_not_severe.visual.2025') / cv('registered_by_type.visual.2025')) * 100;

  /* 방송 자막·수어를 주로 무엇으로 보나(국립국어원 2023, 하나만 응답) */
  data.tvService = [
    { key: 'caption', label: '한글 자막', value: cv('tv_main_service_caption.severe_hearing_20plus.2023'), cls: 's1' },
    { key: 'sign', label: '수어통역', value: cv('tv_main_service_sign.severe_hearing_20plus.2023'), cls: 's1' },
    { key: 'none', label: '이용 안 함', value: cv('tv_main_service_none.severe_hearing_20plus.2023'), cls: 's1' },
  ];
  const tvTotal = data.tvService.reduce((sum, d) => sum + d.value, 0);
  if (Math.abs(tvTotal - 100) > 0.11) fail(`하나만 고르는 문항의 합계가 100이 아니다: ${tvTotal}`);
  tables['tv-service'] = {
    caption: '방송을 볼 때 주로 쓰는 서비스, 2023년 (20세 이상 심한 청각장애인, 하나만 응답)',
    columns: [{ label: '서비스' }, { label: '비율', numeric: true }],
    rows: data.tvService.map((d) => [d.label, `${fmt(d.value, 1)}%`]),
    note: '국립국어원 「2023년 한국수어 활용 조사」 표 Ⅱ-163(국가승인통계, 가중치 적용, 응답자 482명). 보고서 본문 237쪽의 32.0%는 2020년 값이 잘못 들어간 것이라 표 값을 쓴다.',
  };

  /* 온라인 영상 의무 비교(법령 원문, docs/media-access/law.md §6) */
  const uk = (kind, phase) => fmt(cv(`uk_vod_quota_${kind}.${phase}.2026`), phase === 'tier1_year2' && kind === 'sign' ? 1 : 0);
  tables['foreign'] = {
    caption: '온라인 영상의 자막·화면해설·수어 의무: 한국·영국·미국 (2026-10-13 기준)',
    columns: [{ label: '나라' }, { label: '대상' }, { label: '요구' }, { label: '상태' }],
    rows: [
      ['한국', 'OTT가 직접 만든 영상', '한국수어·폐쇄자막·화면해설 제공에 노력. 수치와 실적 제출 없음', '2024년 1월부터 시행'],
      ['영국', '이용자가 많은 주문형 서비스(Tier 1)', `작품 재생시간 기준 자막 ${uk('subtitles', 'tier1_year4')}%·화면해설 ${uk('audio_description', 'tier1_year4')}%·수어 ${uk('sign', 'tier1_year4')}% 이상. 처음 두 해는 ${uk('subtitles', 'tier1_year2')}%·${uk('audio_description', 'tier1_year2')}%·${uk('sign', 'tier1_year2')}%`, '세부 규칙(Ofcom 코드) 확정 전이라 아직 발효 전'],
      ['미국', 'TV에서 자막과 함께 방영한 프로그램의 인터넷 영상', '폐쇄자막 의무. 화면해설·수어 규정 없음', '시행 중'],
    ],
    note: '근거: 전기통신사업법 제22조의10, 영국 Communications Act 2003 s.368HL(Media Act 2024 별표 5), 미국 47 CFR §79.4.',
  };
  tables['context-facts'] = {
    caption: '조사 문서에서 가져와 본문에 쓴 숫자와 출처 (A·B 등급만)',
    columns: [{ label: '내용과 위치' }, { label: '값', numeric: true }, { label: '기준연도', numeric: true }, { label: '출처' }, { label: '등급' }],
    rows: [...ctx.values()].map((row) => [
      row.source_locator,
      `${fmt(row.value, row.digits)}${CTX_UNITS[row.unit]}`,
      row.survey_year,
      { text: new URL(row.source_url).hostname.replace(/^www\./, ''), href: row.source_url },
      row.grade,
    ]),
  };
  facts['ctx.rows'] = ctx.size;

  tables['provenance'] = {
    caption: '이 페이지가 읽은 분석 파일',
    columns: [{ label: '파일' }, { label: '형태' }, { label: 'SHA-256 앞 12자리' }],
    rows: provenance.map((p) => [{ text: p.path, href: p.href }, p.shape, p.sha256.slice(0, 12)]),
  };

  data.meta = { repoUrl };
  return { data, tables, fragments, facts };
}

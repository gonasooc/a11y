// 디지털포용법 보고서: 생성 구역의 JSON으로 차트를 그리고 목차를 연결한다.
// 일반 스크립트(defer)다. 공통 스크립트가 window.A11y에 올려 둔 함수를 쓴다.
(function (A11y) {
  'use strict';
  const { coverageChart, columnChart, dotPlot, dumbbellChart, lineChart, monthlyChart, smallMultiples, sparkBars, sparkLine, sparkMeter, splitBars, waterfallChart } = A11y.charts;
  const { fmt, fmtSignedPct } = A11y.format;

  const data = JSON.parse(document.getElementById('report-data').textContent);

  /** 차트 하나가 실패해도 나머지는 그리고, 표로 보기를 안내한다. */
  function render(key, draw) {
    const el = document.querySelector(`[data-viz="${key}"]`);
    if (!el) return;
    try {
      draw(el, { labelledBy: el.dataset.labelledby, describedBy: el.dataset.describedby });
    } catch (error) {
      console.error(`[${key}] 차트를 그리지 못했다`, error);
      el.replaceChildren();
      const message = document.createElement('p');
      message.className = 'note';
      message.textContent = '차트를 그리지 못했다. 같은 값은 표로 보기에서 확인할 수 있다.';
      el.append(message);
    }
  }

  const inMainWindow = (month) => {
    const m = Number(month.slice(5));
    return m >= 2 && m <= 9;
  };

  render('heroKosis', (el) => sparkLine(el, data.hero.disabledOverall));
  render('heroMois', (el) => sparkMeter(el, data.hero.wheelchairNoShare));
  render('heroPps', (el) => sparkBars(el, data.hero.months.map((m) => m.qty), (i) => inMainWindow(data.hero.months[i].month)));

  render('coverage', (el, ids) => coverageChart(el, { ...data.coverage, ...ids }));

  render('kosisOverall', (el, ids) =>
    lineChart(el, { years: data.kosis.years, series: data.kosis.overall, yDomain: [50, 100], ref: 100, ...ids }),
  );
  render('kosisDisabled', (el) => smallMultiples(el, { years: data.kosis.years, panels: data.kosis.disabled, yDomain: [40, 100] }));
  render('kosisGaps', (el, ids) =>
    dotPlot(el, {
      rows: data.kosis.gaps.map((g) => ({ label: g.label, values: g })),
      series: [
        { key: 'access', label: '접근' },
        { key: 'capability', label: '역량' },
        { key: 'utilization', label: '활용' },
      ],
      xDomain: [50, 100],
      note: (row) => `역량의 일반국민 기준과 차이 ${fmt(100 - row.values.capability, 1)}`,
      ...ids,
    }),
  );

  render('web', (el, ids) =>
    columnChart(el, {
      items: data.web.map((w) => ({ key: String(w.year), label: String(w.year), value: w.value })),
      yMax: 100,
      digits: 1,
      unit: '점',
      tooltipNote: '공표 평균점수, 해마다 다른 표본',
      ...ids,
    }),
  );

  const main = data.pps.windows.find((w) => w.key === 'febSep');
  render('ppsMonthly', (el, ids) =>
    monthlyChart(el, {
      months: data.pps.months,
      windows: [
        { year: 2025, from: 2, to: 9, total: main.q2025 },
        { year: 2026, from: 2, to: 9, total: main.q2026 },
      ],
      transition: '2026-01',
      january: data.pps.january,
      events: data.pps.events,
      ...ids,
    }),
  );
  render('ppsWindows', (el, ids) =>
    dumbbellChart(el, {
      groups: [{ rows: data.pps.windows.map((w) => ({ label: w.label, sub: w.note, a: w.q2025, b: w.q2026, pct: w.pct })) }],
      aLabel: '2025년',
      bLabel: '2026년',
      unit: '대',
      diffText: (row) => fmtSignedPct(row.pct, 1),
      ...ids,
    }),
  );
  render('ppsJanuary', (el, ids) =>
    splitBars(el, {
      rows: data.pps.january.map((j) => ({ label: `${j.year}년 1월`, values: [j.early, j.late] })),
      parts: [
        { label: '1~21일', cls: 'before' },
        { label: '22~31일 (시행일 1/22부터)', cls: 'after' },
      ],
      ...ids,
    }),
  );

  const cohortLines = { both: ['두 해', '모두'], '2025_only': ['2025년', '에만'], '2026_only': ['2026년', '에만'] };
  const cohortNames = { both: '두 해 모두 기록', '2025_only': '2025년에만 기록', '2026_only': '2026년에만 기록' };
  render('cohorts', (el, ids) =>
    waterfallChart(el, {
      start: { lines: ['2025년', '2~9월'], name: '2025년 2~9월', value: data.cohorts.start },
      steps: data.cohorts.steps.map((s) => ({ lines: [...cohortLines[s.key], `${fmt(s.institutions)}곳`], name: `${cohortNames[s.key]} ${fmt(s.institutions)}곳`, value: s.diff })),
      end: { lines: ['2026년', '2~9월'], name: '2026년 2~9월', value: data.cohorts.end },
      ...ids,
    }),
  );
  render('institutions', (el, ids) =>
    dumbbellChart(el, {
      groups: [
        { title: '감소 상위 5곳', rows: data.institutions.decreases.map((r) => ({ label: r.label, a: r.q2025, b: r.q2026 })) },
        { title: '증가 사례', rows: data.institutions.increases.map((r) => ({ label: r.label, a: r.q2025, b: r.q2026 })) },
      ],
      aLabel: '2025년 2~9월',
      bLabel: '2026년 2~9월',
      unit: '대',
      ...ids,
    }),
  );
  render('products', (el, ids) =>
    dumbbellChart(el, {
      groups: [{ rows: data.products.map((p) => ({ label: p.label, sub: p.sub, a: p.q2025, b: p.q2026 })) }],
      aLabel: '2025년 2~9월',
      bLabel: '2026년 2~9월',
      unit: '대',
      ...ids,
    }),
  );
  render('registryYears', (el, ids) =>
    columnChart(el, {
      items: data.registry.years.map((r) => ({
        key: r.label,
        label: r.label,
        value: r.value,
        partial: r.partial,
        note: r.partial ? '7월 30일 발급분까지의 부분집계' : undefined,
      })),
      unit: '개 모델',
      ...ids,
    }),
  );

  /* 목차: 넓은 화면에서는 항상 펼치고, 읽는 위치를 표시한다. */
  const toc = document.querySelector('[data-toc]');
  if (toc) {
    const wide = matchMedia('(min-width: 74rem)');
    const syncOpen = () => {
      if (wide.matches) toc.open = true;
    };
    toc.open = wide.matches;
    wide.addEventListener('change', syncOpen);

    const links = [...toc.querySelectorAll('a[href^="#"]')];
    const byId = new Map(links.map((a) => [decodeURIComponent(a.hash.slice(1)), a]));
    const visible = new Map();
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) visible.set(entry.target.id, entry.isIntersecting);
        const current = [...byId.keys()].find((id) => visible.get(id));
        for (const [id, link] of byId) {
          if (id === current) link.setAttribute('aria-current', 'true');
          else link.removeAttribute('aria-current');
        }
      },
      { rootMargin: '-15% 0px -70% 0px' },
    );
    for (const id of byId.keys()) {
      const section = document.getElementById(id);
      if (section) observer.observe(section);
    }
    toc.addEventListener('click', (event) => {
      if (event.target.closest('a') && !wide.matches) toc.open = false;
    });
  }
})(window.A11y);

// 여러 계열의 연도별 선 차트. 끝 라벨은 넓은 화면에서만, 범례는 항상 둔다.
(function (A11y) {
  'use strict';
  const { fmt } = A11y.format;
  const { chartSvg, interact, legend, linear, measure, plotArea, point, responsive, spreadLabels, svgEl, svgText } = A11y.chart;

  function lineChart(mount, opts) {
    const { years, series, yDomain, ref, refLabel = '일반국민 = 100', digits = 1, labelledBy, describedBy } = opts;
    legend(mount, series.map((s, i) => ({ label: s.label, cls: `s${i + 1}`, shape: 'line' })), { label: '계열' });

    responsive(mount, (width) => {
      const plot = plotArea(mount);
      const wide = width >= 560;
      const height = Math.round(Math.max(250, Math.min(360, width * 0.48)));
      const margin = { top: 20, right: 18, bottom: 30, left: 34 };
      const svg = chartSvg(plot, { width, height, labelledBy, describedBy });

      const endText = (s) => `${s.label} ${fmt(s.values.at(-1), digits)}`;
      if (wide) {
        const longest = Math.max(...series.map((s) => measure(svg, endText(s), 'label')));
        margin.right = Math.ceil(longest) + 26;
      }

      const x = point(years, [margin.left + 10, width - margin.right]);
      const y = linear(yDomain, [height - margin.bottom, margin.top]);
      const right = width - margin.right + 6;
      const deco = svgEl('g', { 'aria-hidden': 'true' }, svg);

      for (const t of y.ticks(5)) {
        svgEl('line', { class: 'grid', x1: margin.left, x2: right, y1: y(t), y2: y(t) }, deco);
        svgText(deco, margin.left - 8, y(t), fmt(t), { class: 'axis-label', 'text-anchor': 'end', 'dominant-baseline': 'middle' });
      }
      const every = x.step >= 44 ? 1 : x.step >= 24 ? 2 : 3;
      years.forEach((year, i) => {
        if (i % every === 0 || i === years.length - 1) {
          svgText(deco, x(year), height - 8, String(year), { class: 'axis-label', 'text-anchor': 'middle' });
        }
      });

      if (ref !== undefined) {
        svgEl('line', { class: 'ref-line', x1: margin.left, x2: right, y1: y(ref), y2: y(ref) }, deco);
        svgText(deco, margin.left + 4, y(ref) - 7, refLabel, { class: 'ref-label' });
      }

      series.forEach((s, i) => {
        const d = s.values.map((v, j) => `${j ? 'L' : 'M'}${x(years[j]).toFixed(1)},${y(v).toFixed(1)}`).join('');
        svgEl('path', { class: `line s${i + 1}`, d }, deco);
        svgEl('circle', { class: `dot s${i + 1}`, cx: x(years.at(-1)), cy: y(s.values.at(-1)), r: 4 }, deco);
      });

      if (wide) {
        const labels = series.map((s, i) => ({ i, y: y(s.values.at(-1)), text: endText(s) }));
        spreadLabels(labels, 17, [margin.top, height - margin.bottom]);
        const lx = x(years.at(-1)) + 9;
        for (const label of labels) {
          if (Math.abs(label.labelY - label.y) > 2) {
            svgEl('polyline', { class: 'leader', points: `${lx - 3},${label.y} ${lx + 5},${label.labelY}` }, deco);
          }
          svgText(deco, lx + 9, label.labelY, label.text, { class: 'label', 'dominant-baseline': 'middle' });
        }
      }

      const layer = svgEl('g', { class: 'datums' }, svg);
      const half = Math.max(12, x.step / 2);
      const items = years.map((year, j) => {
        const g = svgEl('g', {}, layer);
        const x0 = Math.max(margin.left, x(year) - half);
        const x1 = Math.min(right, x(year) + half);
        svgEl('rect', { class: 'hit', x: x0, y: margin.top - 6, width: x1 - x0, height: height - margin.top - margin.bottom + 6 }, g);
        svgEl('line', { class: 'crosshair', x1: x(year), x2: x(year), y1: margin.top - 6, y2: height - margin.bottom }, g);
        series.forEach((s, i) => svgEl('circle', { class: `dot dot--hover s${i + 1}`, cx: x(year), cy: y(s.values[j]), r: 4.5 }, g));
        svgEl('rect', { class: 'focus-ring', x: x0 + 1, y: margin.top - 8, width: Math.max(4, x1 - x0 - 2), height: height - margin.top - margin.bottom + 10, rx: 6 }, g);
        const ordered = series.map((s, i) => ({ s, i, v: s.values[j] })).sort((a, b) => b.v - a.v);
        return {
          el: g,
          label: `${year}년: ${series.map((s) => `${s.label} ${fmt(s.values[j], digits)}`).join(', ')}`,
          tooltip: {
            title: `${year}년`,
            rows: ordered.map(({ s, i, v }) => ({ key: 'line', cls: `s${i + 1}`, value: fmt(v, digits), label: s.label })),
          },
          anchor: { x: x(year), y: Math.min(...series.map((s) => y(s.values[j]))) },
        };
      });
      interact(mount, svg, items);
    });
  }

  A11y.charts = Object.assign(A11y.charts || {}, { lineChart });
})((window.A11y = window.A11y || {}));

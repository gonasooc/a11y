// 행마다 여러 지표를 점으로 찍는 점 그림(2025년 격차). 계열은 3개 이하만 쓴다.
(function (A11y) {
  'use strict';
  const { fmt } = A11y.format;
  const { chartSvg, interact, legend, linear, measure, plotArea, responsive, svgEl, svgText } = A11y.chart;

  function dotPlot(mount, opts) {
    const { rows, series, xDomain, ref = 100, refLabel = '일반국민 = 100', digits = 1, labelledBy, describedBy, note } = opts;
    legend(mount, series.map((s, i) => ({ label: s.label, cls: `s${i + 1}`, shape: 'dot' })), { label: '지표' });

    responsive(mount, (width) => {
      const plot = plotArea(mount);
      const probe = chartSvg(plot, { width, height: 10, labelledBy, describedBy });
      const labelWidth = Math.max(...rows.map((r) => measure(probe, r.label, 'row-label')));
      probe.remove();
      const wide = width >= 520;
      const left = wide ? Math.ceil(labelWidth) + 20 : 16;
      const margin = { top: 46, right: 24, bottom: 30, left };
      const rowH = wide ? 44 : 58;
      const height = margin.top + rows.length * rowH + margin.bottom;
      const svg = chartSvg(plot, { width, height, labelledBy, describedBy });
      const x = linear(xDomain, [margin.left, width - margin.right]);
      const deco = svgEl('g', { 'aria-hidden': 'true' }, svg);
      const bottom = height - margin.bottom;

      for (const t of x.ticks(width >= 520 ? 6 : 4)) {
        svgEl('line', { class: 'grid', x1: x(t), x2: x(t), y1: margin.top - 8, y2: bottom }, deco);
        svgText(deco, x(t), bottom + 18, fmt(t), { class: 'axis-label', 'text-anchor': 'middle' });
      }
      svgEl('line', { class: 'ref-line', x1: x(ref), x2: x(ref), y1: margin.top - 14, y2: bottom }, deco);
      svgText(deco, x(ref), margin.top - 20, refLabel, { class: 'ref-label', 'text-anchor': 'end' });

      const layer = svgEl('g', { class: 'datums' }, svg);
      const items = rows.map((row, r) => {
        const top = margin.top + r * rowH;
        const cy = wide ? top + rowH / 2 : top + 36;
        if (wide) {
          svgText(deco, margin.left - 14, cy, row.label, { class: 'row-label', 'text-anchor': 'end', 'dominant-baseline': 'middle' });
        } else {
          svgText(deco, margin.left, top + 14, row.label, { class: 'row-label' });
        }
        const values = series.map((s) => row.values[s.key]);
        svgEl('line', { class: 'range', x1: x(Math.min(...values)), x2: x(Math.max(...values)), y1: cy, y2: cy }, deco);
        series.forEach((s, i) => {
          svgEl('circle', { class: `dot dot--lg s${i + 1}`, cx: x(row.values[s.key]), cy, r: 5.5 }, deco);
          if (r === 0) {
            // 첫 행에만 직접 라벨: 넓은 화면은 점 위, 좁은 화면은 점 아래(행 이름과 겹치지 않게)
            svgText(deco, x(row.values[s.key]), wide ? cy - 13 : cy + 19, s.label, { class: 'label label--series', 'text-anchor': 'middle' });
          }
        });

        const g = svgEl('g', {}, layer);
        svgEl('rect', { class: 'hit', x: 0, y: top, width, height: rowH }, g);
        svgEl('rect', { class: 'focus-ring', x: 2, y: top + 2, width: width - 4, height: rowH - 4, rx: 6 }, g);
        const detail = series.map((s) => `${s.label} ${fmt(row.values[s.key], digits)}`).join(', ');
        return {
          el: g,
          label: `${row.label}: ${detail}${note ? `. ${note(row)}` : ''}`,
          tooltip: {
            title: row.label,
            rows: series.map((s, i) => ({ key: 'dot', cls: `s${i + 1}`, value: fmt(row.values[s.key], digits), label: s.label })),
            note: note ? note(row) : undefined,
          },
          anchor: { x: x(Math.max(...values)), y: cy },
        };
      });
      interact(mount, svg, items);
    });
  }

  A11y.charts = Object.assign(A11y.charts || {}, { dotPlot });
})((window.A11y = window.A11y || {}));

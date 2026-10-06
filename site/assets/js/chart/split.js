// 가로 누적 막대(1월의 날짜 구분). 조각 사이는 2px 표면 간격으로 나눈다.
(function (A11y) {
  'use strict';
  const { fmt } = A11y.format;
  const { barPath, chartSvg, interact, legend, linear, measure, niceDomain, plotArea, responsive, svgEl, svgText } = A11y.chart;

  function splitBars(mount, opts) {
    const { rows, parts, unit = '대', labelledBy, describedBy } = opts;
    legend(mount, parts.map((p) => ({ label: p.label, cls: p.cls, shape: 'box' })), { label: '구분' });

    responsive(mount, (width) => {
      const plot = plotArea(mount);
      const wide = width >= 480;
      const margin = { top: 6, right: 70, bottom: 28, left: wide ? 92 : 12 };
      const rowH = wide ? 46 : 64;
      const barH = 22;
      const height = margin.top + rows.length * rowH + margin.bottom;
      const svg = chartSvg(plot, { width, height, labelledBy, describedBy });
      const max = niceDomain(0, Math.max(...rows.map((r) => r.values.reduce((a, b) => a + b, 0))), 4)[1];
      const x = linear([0, max], [margin.left, width - margin.right]);
      const deco = svgEl('g', { 'aria-hidden': 'true' }, svg);
      const bottom = height - margin.bottom;

      for (const t of x.ticks(4)) {
        svgEl('line', { class: t === 0 ? 'baseline' : 'grid', x1: x(t), x2: x(t), y1: margin.top, y2: bottom }, deco);
        svgText(deco, x(t), bottom + 18, fmt(t), { class: 'axis-label', 'text-anchor': 'middle' });
      }

      const layer = svgEl('g', { class: 'datums' }, svg);
      const overlay = svgEl('g', { 'aria-hidden': 'true' }, svg);
      const items = rows.map((row, r) => {
        const top = margin.top + r * rowH;
        const by = wide ? top + (rowH - barH) / 2 : top + rowH - barH - 10;
        if (wide) svgText(deco, margin.left - 12, by + barH / 2, row.label, { class: 'row-label', 'text-anchor': 'end', 'dominant-baseline': 'middle' });
        else svgText(deco, margin.left, top + 16, row.label, { class: 'row-label' });
        const g = svgEl('g', {}, layer);
        svgEl('rect', { class: 'hit', x: 0, y: top, width, height: rowH }, g);
        let acc = 0;
        row.values.forEach((value, i) => {
          const x0 = x(acc) + (i ? 1 : 0);
          const x1 = x(acc + value) - (i < row.values.length - 1 ? 1 : 0);
          const last = i === row.values.length - 1;
          const d = last ? barPath(x0, x1, by, barH) : `M${x0},${by}H${x1}V${by + barH}H${x0}Z`;
          svgEl('path', { class: `bar ${parts[i].cls}`, d }, g);
          const text = fmt(value);
          if (x1 - x0 >= measure(svg, text, 'label label--inside') + 12) {
            svgText(overlay, (x0 + x1) / 2, by + barH / 2, text, { class: `label label--inside on-${parts[i].cls}`, 'text-anchor': 'middle', 'dominant-baseline': 'central' });
          }
          acc += value;
        });
        const total = row.values.reduce((a, b) => a + b, 0);
        svgText(deco, x(total) + 8, by + barH / 2, `${fmt(total)}${unit}`, { class: 'label label--value', 'dominant-baseline': 'central' });
        svgEl('rect', { class: 'focus-ring', x: 2, y: top + 2, width: width - 4, height: rowH - 4, rx: 6 }, g);
        return {
          el: g,
          label: `${row.label}: ${parts.map((p, i) => `${p.label} ${fmt(row.values[i])}${unit}`).join(', ')}, 합계 ${fmt(total)}${unit}`,
          tooltip: {
            title: row.label,
            rows: [
              ...parts.map((p, i) => ({ key: 'box', cls: p.cls, value: `${fmt(row.values[i])}${unit}`, label: p.label })),
              { value: `${fmt(total)}${unit}`, label: '합계' },
            ],
          },
          anchor: { x: x(total), y: by + barH / 2 },
        };
      });
      interact(mount, svg, items);
    });
  }

  A11y.charts = Object.assign(A11y.charts || {}, { splitBars });
})((window.A11y = window.A11y || {}));

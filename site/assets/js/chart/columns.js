// 단일 계열 세로 막대(연도별 점수, 등록번호 연도). 값은 막대 끝에 쓴다.
(function (A11y) {
  'use strict';
  const { fmt } = A11y.format;
  const { band, chartSvg, columnPath, interact, linear, niceDomain, plotArea, responsive, svgEl, svgText } = A11y.chart;

  function columnChart(mount, opts) {
    const { items, yMax, digits = 0, unit = '', labelledBy, describedBy, tooltipNote } = opts;

    responsive(mount, (width) => {
      const plot = plotArea(mount);
      const height = Math.round(Math.max(220, Math.min(300, width * 0.42)));
      const margin = { top: 28, right: 12, bottom: 34, left: 40 };
      const svg = chartSvg(plot, { width, height, labelledBy, describedBy });
      const max = yMax ?? niceDomain(0, Math.max(...items.map((d) => d.value)), 5)[1];
      const y = linear([0, max], [height - margin.bottom, margin.top]);
      const x = band(items.map((d) => d.key), [margin.left, width - margin.right], { inner: 0.35, outer: 0.25 });
      const barW = Math.min(24, x.bandwidth);
      const deco = svgEl('g', { 'aria-hidden': 'true' }, svg);
      const base = y(0);

      for (const t of y.ticks(4)) {
        svgEl('line', { class: t === 0 ? 'baseline' : 'grid', x1: margin.left, x2: width - margin.right, y1: y(t), y2: y(t) }, deco);
        svgText(deco, margin.left - 8, y(t), fmt(t), { class: 'axis-label', 'text-anchor': 'end', 'dominant-baseline': 'middle' });
      }

      const layer = svgEl('g', { class: 'datums' }, svg);
      const marks = items.map((d) => {
        const cx = x.center(d.key);
        const g = svgEl('g', {}, layer);
        svgEl('rect', { class: 'hit', x: x(d.key) - (x.step - x.bandwidth) / 2, y: margin.top - 20, width: x.step, height: base - margin.top + 20 }, g);
        svgEl('path', { class: `bar ${d.partial ? 'bar--partial' : 's1'}`, d: columnPath(cx - barW / 2, barW, base, y(d.value)) }, g);
        svgEl('rect', { class: 'focus-ring', x: cx - barW / 2 - 6, y: y(d.value) - 24, width: barW + 12, height: base - y(d.value) + 28, rx: 6 }, g);
        svgText(deco, cx, y(d.value) - 8, `${fmt(d.value, digits)}${d.partial ? '*' : ''}`, { class: 'label label--value', 'text-anchor': 'middle' });
        svgText(deco, cx, height - 12, d.label, { class: 'axis-label', 'text-anchor': 'middle' });
        return {
          el: g,
          label: `${d.label}: ${fmt(d.value, digits)}${unit}${d.note ? `, ${d.note}` : ''}`,
          tooltip: {
            title: d.label,
            rows: [{ key: 'box', cls: d.partial ? 'partial' : 's1', value: `${fmt(d.value, digits)}${unit}` }],
            note: d.note ?? tooltipNote,
          },
          anchor: { x: cx + barW / 2, y: y(d.value) },
        };
      });
      interact(mount, svg, marks);
    });
  }

  A11y.charts = Object.assign(A11y.charts || {}, { columnChart });
})((window.A11y = window.A11y || {}));

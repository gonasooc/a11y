// 한 계열 가로 막대와 선택적 기준선(일반국민 100, 평균 등). 값은 막대 끝에 쓴다.
// 좁은 화면에서는 항목 이름을 막대 위에 두어 막대 길이를 지킨다.
(function (A11y) {
  'use strict';
  const { fmt } = A11y.format;
  const { barPath, chartSvg, interact, linear, measure, plotArea, responsive, svgEl, svgText } = A11y.chart;

  function refBars(mount, opts) {
    const { items, domain, ref, unit = '', digits = 1, ticks = 4, labelledBy, describedBy, tooltipNote } = opts;
    const valueText = (d) => `${fmt(d.value, digits)}${unit}`;

    responsive(mount, (width) => {
      const plot = plotArea(mount);
      const narrow = width < 520;
      const barH = 20;
      const rowH = narrow ? 50 : 36;
      const top = ref ? 34 : 8;
      const bottom = 24;
      const height = top + items.length * rowH + bottom;
      const svg = chartSvg(plot, { width, height, labelledBy, describedBy });

      const labelW = narrow ? 0 : Math.min(Math.round(width * 0.4), Math.ceil(Math.max(...items.map((d) => measure(svg, d.label, 'axis-label')))) + 14);
      const valueW = Math.ceil(Math.max(...items.map((d) => measure(svg, valueText(d), 'label')))) + 10;
      const left = narrow ? 2 : labelW;
      const right = width - Math.max(valueW, 14);
      const x = linear(domain, [left, right]);
      const deco = svgEl('g', { 'aria-hidden': 'true' }, svg);

      for (const t of x.ticks(ticks)) {
        svgEl('line', { class: t === domain[0] ? 'baseline' : 'grid', x1: x(t), x2: x(t), y1: top - 4, y2: height - bottom }, deco);
        svgText(deco, x(t), height - 8, fmt(t), { class: 'axis-label', 'text-anchor': 'middle' });
      }

      if (ref) {
        const rx = x(ref.value);
        svgEl('line', { class: 'ref-line', x1: rx, x2: rx, y1: top - 10, y2: height - bottom }, deco);
        const anchor = rx > width - 90 ? 'end' : rx < left + 90 ? 'start' : 'middle';
        svgText(deco, rx, top - 16, ref.label, { class: 'ref-label', 'text-anchor': anchor });
      }

      const layer = svgEl('g', { class: 'datums' }, svg);
      const marks = items.map((d, i) => {
        const rowTop = top + i * rowH;
        const barY = narrow ? rowTop + rowH - barH - 6 : rowTop + (rowH - barH) / 2;
        const end = x(d.value);
        const g = svgEl('g', {}, layer);
        svgEl('rect', { class: 'hit', x: 0, y: rowTop, width, height: rowH }, g);
        svgEl('path', { class: `bar ${d.cls ?? 's1'}`, d: barPath(x(domain[0]), end, barY, barH) }, g);
        svgEl('rect', { class: 'focus-ring', x: Math.max(0, left - (narrow ? 2 : labelW) + 1), y: rowTop + 1, width: Math.min(width - 2, end - left + (narrow ? 2 : labelW) + valueW), height: rowH - 2, rx: 6 }, g);
        if (narrow) svgText(deco, left, barY - 7, d.label, { class: 'axis-label axis-label--strong' });
        else svgText(deco, left - 10, barY + barH / 2, d.label, { class: 'axis-label axis-label--strong', 'text-anchor': 'end', 'dominant-baseline': 'middle' });
        // 값 글자가 기준선에 걸리면 기준선 오른쪽으로 비켜 쓴다.
        let lx = end + 6;
        if (ref) {
          const rx = x(ref.value);
          const lw = measure(svg, valueText(d), 'label');
          if (lx <= rx + 2 && lx + lw >= rx - 2) lx = rx + 6;
        }
        svgText(deco, lx, barY + barH / 2, valueText(d), { class: 'label label--value', 'dominant-baseline': 'middle' });
        const refText = ref ? `, ${ref.label}` : '';
        return {
          el: g,
          label: `${d.label}: ${valueText(d)}${d.note ? ` (${d.note})` : ''}${refText}`,
          tooltip: {
            title: d.label,
            rows: [{ key: 'box', cls: d.cls ?? 's1', value: valueText(d), label: d.note }],
            note: ref ? `${ref.label}${tooltipNote ? `. ${tooltipNote}` : ''}` : tooltipNote,
          },
          anchor: { x: end, y: barY },
        };
      });
      interact(mount, svg, marks);
    });
  }

  A11y.charts = Object.assign(A11y.charts || {}, { refBars });
})((window.A11y = window.A11y || {}));

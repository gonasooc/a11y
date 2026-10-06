// 같은 척도를 공유하는 작은 선 차트 묶음. 패널마다 한 계열이라 범례 대신 제목이 계열을 밝힌다.
(function (A11y) {
  'use strict';
  const { fmt } = A11y.format;
  const { chartSvg, htmlEl, interact, linear, plotArea, point, responsive, svgEl, svgText } = A11y.chart;

  let uid = 0;

  function smallMultiples(mount, opts) {
    const { years, panels, yDomain, ref = 100, digits = 1, refLabel = '일반국민 = 100' } = opts;
    const grid = htmlEl('ul', { className: 'viz-multiples', role: 'list' });
    mount.append(grid);

    for (const panel of panels) {
      uid += 1;
      const titleId = `mp-title-${uid}`;
      const descId = `mp-desc-${uid}`;
      const first = panel.values[0];
      const last = panel.values.at(-1);
      const plotMount = htmlEl('div', { className: 'viz-panel__plot viz' });
      grid.append(
        htmlEl(
          'li',
          { className: 'viz-panel' },
          htmlEl('h4', { className: 'viz-panel__title', id: titleId, text: panel.label }),
          htmlEl('p', {
            className: 'viz-panel__summary',
            id: descId,
            text: `${years[0]}년 ${fmt(first, digits)} → ${years.at(-1)}년 ${fmt(last, digits)} · 일반국민 기준과 ${fmt(ref - last, digits)}포인트 차이`,
          }),
          plotMount,
        ),
      );

      responsive(plotMount, (width) => {
        const plot = plotArea(plotMount);
        const height = 176;
        const margin = { top: 16, right: 40, bottom: 24, left: 30 };
        const svg = chartSvg(plot, { width, height, labelledBy: titleId, describedBy: descId });
        const x = point(years, [margin.left + 6, width - margin.right]);
        const y = linear(yDomain, [height - margin.bottom, margin.top]);
        const deco = svgEl('g', { 'aria-hidden': 'true' }, svg);

        for (const t of y.ticks(3)) {
          svgEl('line', { class: 'grid', x1: margin.left, x2: width - margin.right + 4, y1: y(t), y2: y(t) }, deco);
          svgText(deco, margin.left - 6, y(t), fmt(t), { class: 'axis-label', 'text-anchor': 'end', 'dominant-baseline': 'middle' });
        }
        [years[0], 2021, years.at(-1)].forEach((year) => {
          svgText(deco, x(year), height - 6, String(year), { class: 'axis-label', 'text-anchor': 'middle' });
        });

        const pts = panel.values.map((v, j) => [x(years[j]), y(v)]);
        const linePath = pts.map(([px, py], j) => `${j ? 'L' : 'M'}${px.toFixed(1)},${py.toFixed(1)}`).join('');
        const gapPath = `${linePath}L${x(years.at(-1)).toFixed(1)},${y(ref)}L${x(years[0]).toFixed(1)},${y(ref)}Z`;
        svgEl('path', { class: 'area s1', d: gapPath }, deco);
        svgEl('line', { class: 'ref-line', x1: margin.left, x2: width - margin.right + 4, y1: y(ref), y2: y(ref) }, deco);
        svgEl('path', { class: 'line s1', d: linePath }, deco);
        for (const j of [0, panel.values.length - 1]) {
          svgEl('circle', { class: 'dot s1', cx: pts[j][0], cy: pts[j][1], r: 4 }, deco);
        }
        svgText(deco, pts.at(-1)[0] + 8, pts.at(-1)[1], fmt(last, digits), { class: 'label label--value', 'dominant-baseline': 'middle' });
        // 시작값은 점 오른쪽 아래(선이 오르는 반대쪽)에 둔다. 바닥에 닿으면 위로 올린다.
        const startY = pts[0][1] + 16 <= height - margin.bottom - 2 ? pts[0][1] + 16 : pts[0][1] - 10;
        svgText(deco, pts[0][0] + 4, startY, fmt(first, digits), { class: 'label', 'text-anchor': 'start' });

        const layer = svgEl('g', { class: 'datums' }, svg);
        const half = Math.max(8, x.step / 2);
        const items = years.map((year, j) => {
          const g = svgEl('g', {}, layer);
          const x0 = Math.max(margin.left, x(year) - half);
          const x1 = Math.min(width - margin.right + 4, x(year) + half);
          svgEl('rect', { class: 'hit', x: x0, y: margin.top - 4, width: x1 - x0, height: height - margin.top - margin.bottom + 4 }, g);
          svgEl('line', { class: 'crosshair', x1: x(year), x2: x(year), y1: margin.top - 4, y2: height - margin.bottom }, g);
          svgEl('circle', { class: 'dot dot--hover s1', cx: x(year), cy: y(panel.values[j]), r: 4.5 }, g);
          svgEl('rect', { class: 'focus-ring', x: x0 + 1, y: margin.top - 6, width: Math.max(4, x1 - x0 - 2), height: height - margin.top - margin.bottom + 8, rx: 5 }, g);
          const value = panel.values[j];
          return {
            el: g,
            label: `${panel.label} ${year}년 ${fmt(value, digits)}, 일반국민 기준과 ${fmt(ref - value, digits)}포인트 차이`,
            tooltip: {
              title: `${year}년 · ${panel.label}`,
              rows: [
                { key: 'line', cls: 's1', value: fmt(value, digits), label: '장애인' },
                { value: fmt(ref - value, digits), label: '일반국민 기준과 차이' },
              ],
            },
            anchor: { x: x(year), y: y(value) },
          };
        });
        interact(plotMount, svg, items);
      });
    }
    // 첫 패널 아래에 기준선 설명을 한 번만 둔다.
    mount.append(htmlEl('p', { className: 'viz-footnote', text: `가로선은 ${refLabel}, 옅은 면은 그 기준과의 차이다.` }));
  }

  A11y.charts = Object.assign(A11y.charts || {}, { smallMultiples });
})((window.A11y = window.A11y || {}));

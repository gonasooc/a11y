// 자료별 관측 시점과 법 시행일을 한 시간축에 놓는다.
(function (A11y) {
  'use strict';
  const { chartSvg, interact, legend, linear, measure, plotArea, responsive, svgEl, svgText } = A11y.chart;

  const time = (date) => Date.parse(`${date}T00:00:00Z`);

  function coverageChart(mount, opts) {
    const { rows, law, domain, labelledBy, describedBy } = opts;
    legend(
      mount,
      [
        { label: '연 1회 조사', cls: 's1', shape: 'dot' },
        { label: '연속 기간', cls: 's1', shape: 'box' },
        { label: '한 시점의 기록', cls: 'after', shape: 'dot' },
      ],
      { label: '표식' },
    );

    responsive(mount, (width) => {
      const plot = plotArea(mount);
      const probe = chartSvg(plot, { width, height: 10, labelledBy, describedBy });
      const labelWidth = Math.max(...rows.map((r) => measure(probe, r.label, 'row-label')));
      probe.remove();
      const wide = width >= 640;
      const margin = { top: 34, right: 18, bottom: 30, left: wide ? Math.ceil(labelWidth) + 22 : 12 };
      const rowH = wide ? 44 : 62;
      const height = margin.top + rows.length * rowH + margin.bottom;
      const svg = chartSvg(plot, { width, height, labelledBy, describedBy });
      const x = linear([time(domain[0]), time(domain[1])], [margin.left, width - margin.right]);
      const deco = svgEl('g', { 'aria-hidden': 'true' }, svg);
      const bottom = height - margin.bottom;
      const lawX = x(time(law.date));

      svgEl('rect', { class: 'window-band', x: lawX, y: margin.top - 8, width: width - margin.right - lawX, height: bottom - margin.top + 8 }, deco);
      const startYear = Number(domain[0].slice(0, 4));
      const endYear = Number(domain[1].slice(0, 4));
      const stepYears = width >= 640 ? 1 : 2;
      for (let year = startYear; year <= endYear; year += 1) {
        const gx = x(time(`${year}-01-01`));
        svgEl('line', { class: 'grid', x1: gx, x2: gx, y1: margin.top - 8, y2: bottom }, deco);
        if ((year - startYear) % stepYears === 0) svgText(deco, gx, bottom + 18, String(year), { class: 'axis-label', 'text-anchor': 'middle' });
      }
      svgEl('line', { class: 'event-tick event-tick--main', x1: lawX, x2: lawX, y1: margin.top - 22, y2: bottom }, deco);
      svgText(deco, lawX - 6, margin.top - 18, law.label, { class: 'label label--value', 'text-anchor': 'end' });

      const layer = svgEl('g', { class: 'datums' }, svg);
      const items = rows.map((row, r) => {
        const top = margin.top + r * rowH;
        const cy = wide ? top + rowH / 2 : top + rowH - 20;
        if (wide) svgText(deco, margin.left - 14, cy, row.label, { class: 'row-label', 'text-anchor': 'end', 'dominant-baseline': 'middle' });
        else svgText(deco, margin.left, top + 16, row.label, { class: 'row-label' });

        if (row.years) {
          const xs = row.years.map((y) => x(time(`${y}-07-01`)));
          svgEl('line', { class: 'range', x1: xs[0], x2: xs.at(-1), y1: cy, y2: cy }, deco);
          xs.forEach((px) => svgEl('circle', { class: 'dot s1', cx: px, cy, r: 4 }, deco));
        }
        if (row.start) {
          const x0 = x(time(row.start));
          const x1 = x(time(row.end));
          svgEl('rect', { class: 'bar s1', x: x0, y: cy - 6, width: Math.max(3, x1 - x0), height: 12, rx: 4 }, deco);
        }
        if (row.point) {
          svgEl('circle', { class: 'dot dot--lg after', cx: x(time(row.point)), cy, r: 6 }, deco);
        }

        const g = svgEl('g', {}, layer);
        svgEl('rect', { class: 'hit', x: 0, y: top, width, height: rowH }, g);
        svgEl('rect', { class: 'focus-ring', x: 2, y: top + 2, width: width - 4, height: rowH - 4, rx: 6 }, g);
        return {
          el: g,
          label: `${row.label}: ${row.span}. 시행 후 관측: ${row.after}`,
          tooltip: { title: row.label, rows: [{ value: row.span }, { value: row.after, label: '시행 후 관측' }] },
          anchor: { x: row.point ? x(time(row.point)) : row.end ? x(time(row.end)) : x(time(`${row.years.at(-1)}-07-01`)), y: cy },
        };
      });
      interact(mount, svg, items);
    });
  }

  A11y.charts = Object.assign(A11y.charts || {}, { coverageChart });
})((window.A11y = window.A11y || {}));

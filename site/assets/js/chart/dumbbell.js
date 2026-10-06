// 항목별 전후 비교(덤벨). 같은 색상환의 두 단계: 옅은 점이 2025년, 짙은 점이 2026년.
(function (A11y) {
  'use strict';
  const { fmt, fmtSigned } = A11y.format;
  const { chartSvg, interact, legend, linear, measure, niceDomain, plotArea, responsive, svgEl, svgText } = A11y.chart;

  function dumbbellChart(mount, opts) {
    const { groups, aLabel, bLabel, unit = '', digits = 0, xMax, diffText, labelledBy, describedBy } = opts;
    legend(
      mount,
      [
        { label: aLabel, cls: 'before', shape: 'dot' },
        { label: bLabel, cls: 'after', shape: 'dot' },
      ],
      { label: '시점' },
    );
    const rows = groups.flatMap((g) => g.rows.map((r) => ({ ...r, group: g.title })));
    const diff = diffText ?? ((r) => `${fmtSigned(r.b - r.a, digits)}${unit}`);

    responsive(mount, (width) => {
      const plot = plotArea(mount);
      const probe = chartSvg(plot, { width, height: 10, labelledBy, describedBy });
      const labelWidth = Math.max(...rows.map((r) => Math.max(measure(probe, r.label, 'row-label'), r.sub ? measure(probe, r.sub, 'row-sub') : 0)));
      const diffWidth = Math.max(...rows.map((r) => measure(probe, diff(r), 'label label--value')));
      // 점 바깥에 쓰는 값 라벨이 행 이름·차이 열과 겹치지 않도록 양쪽에 자리를 둔다.
      const valueWidth = Math.max(...rows.flatMap((r) => [measure(probe, fmt(r.a, digits), 'label label--value'), measure(probe, fmt(r.b, digits), 'label label--value')]));
      probe.remove();

      const wide = width >= 560;
      // 좁은 화면에서는 차이 값을 행 이름 줄 오른쪽에 써서 그림 폭을 넓힌다.
      const margin = { top: 8, right: wide ? Math.ceil(diffWidth) + 18 : 8, bottom: 30, left: wide ? Math.ceil(labelWidth) + 22 : 8 };
      const rowH = (r) => (wide ? (r.sub ? 46 : 38) : r.sub ? 72 : 56);
      const groupH = 30;
      let cursor = margin.top;
      const layout = [];
      let currentGroup;
      for (const r of rows) {
        if (r.group && r.group !== currentGroup) {
          currentGroup = r.group;
          layout.push({ type: 'group', title: r.group, y: cursor });
          cursor += groupH;
        }
        layout.push({ type: 'row', row: r, y: cursor, h: rowH(r) });
        cursor += rowH(r);
      }
      const height = cursor + margin.bottom;
      const svg = chartSvg(plot, { width, height, labelledBy, describedBy });
      const max = xMax ?? niceDomain(0, Math.max(...rows.flatMap((r) => [r.a, r.b])), 4)[1];
      const pad = Math.ceil(valueWidth) + 16;
      const x = linear([0, max], [margin.left + pad, width - margin.right - pad]);
      const deco = svgEl('g', { 'aria-hidden': 'true' }, svg);
      const bottom = height - margin.bottom;

      for (const t of x.ticks(width >= 560 ? 5 : 3)) {
        svgEl('line', { class: t === 0 ? 'baseline' : 'grid', x1: x(t), x2: x(t), y1: margin.top, y2: bottom }, deco);
        svgText(deco, x(t), bottom + 18, fmt(t), { class: 'axis-label', 'text-anchor': 'middle' });
      }

      const layer = svgEl('g', { class: 'datums' }, svg);
      const items = [];
      for (const item of layout) {
        if (item.type === 'group') {
          svgText(deco, wide ? 0 : margin.left, item.y + 20, item.title, { class: 'group-label' });
          continue;
        }
        const { row: r, y: top, h } = item;
        const cy = wide ? top + h / 2 + (r.sub ? 0 : 0) : top + h - 18;
        if (wide) {
          svgText(deco, margin.left - 16, r.sub ? cy - 7 : cy, r.label, { class: 'row-label', 'text-anchor': 'end', 'dominant-baseline': 'middle' });
          if (r.sub) svgText(deco, margin.left - 16, cy + 11, r.sub, { class: 'row-sub', 'text-anchor': 'end', 'dominant-baseline': 'middle' });
        } else {
          svgText(deco, margin.left, top + 16, r.label, { class: 'row-label' });
          if (r.sub) svgText(deco, margin.left, top + 33, r.sub, { class: 'row-sub' });
        }
        const xa = x(r.a);
        const xb = x(r.b);
        svgEl('line', { class: 'dumbbell-bar', x1: xa, x2: xb, y1: cy, y2: cy }, deco);
        svgEl('circle', { class: 'dot dot--lg before', cx: xa, cy, r: 5.5 }, deco);
        svgEl('circle', { class: 'dot dot--lg after', cx: xb, cy, r: 5.5 }, deco);
        const aLeft = xa <= xb;
        svgText(deco, xa + (aLeft ? -10 : 10), cy, fmt(r.a, digits), { class: 'label', 'text-anchor': aLeft ? 'end' : 'start', 'dominant-baseline': 'middle' });
        svgText(deco, xb + (aLeft ? 10 : -10), cy, fmt(r.b, digits), { class: 'label label--value', 'text-anchor': aLeft ? 'start' : 'end', 'dominant-baseline': 'middle' });
        svgText(deco, width - 2, wide ? cy : top + 16, diff(r), { class: 'label label--diff', 'text-anchor': 'end', 'dominant-baseline': wide ? 'middle' : 'auto' });

        const g = svgEl('g', {}, layer);
        svgEl('rect', { class: 'hit', x: 0, y: top, width, height: h }, g);
        svgEl('rect', { class: 'focus-ring', x: 2, y: top + 2, width: width - 4, height: h - 4, rx: 6 }, g);
        items.push({
          el: g,
          label: `${r.group ? `${r.group}, ` : ''}${r.label}${r.sub ? ` (${r.sub})` : ''}: ${aLabel} ${fmt(r.a, digits)}${unit}, ${bLabel} ${fmt(r.b, digits)}${unit}, 차이 ${diff(r)}`,
          tooltip: {
            title: r.label,
            rows: [
              { key: 'dot', cls: 'before', value: `${fmt(r.a, digits)}${unit}`, label: aLabel },
              { key: 'dot', cls: 'after', value: `${fmt(r.b, digits)}${unit}`, label: bLabel },
              { value: diff(r), label: '차이' },
            ],
            note: r.sub,
          },
          anchor: { x: Math.max(xa, xb), y: cy },
        });
      }
      interact(mount, svg, items);
    });
  }

  A11y.charts = Object.assign(A11y.charts || {}, { dumbbellChart });
})((window.A11y = window.A11y || {}));

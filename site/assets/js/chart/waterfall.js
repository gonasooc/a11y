// 폭포 차트: 시작 합계에서 집단별 증감을 거쳐 끝 합계에 이른다.
(function (A11y) {
  'use strict';
  const { fmt, fmtSigned } = A11y.format;
  const { band, chartSvg, columnPath, interact, legend, linear, measure, niceDomain, plotArea, responsive, svgEl, svgText } = A11y.chart;

  function waterfallChart(mount, opts) {
    const { start, steps, end, unit = '대', labelledBy, describedBy } = opts;
    legend(
      mount,
      [
        { label: '합계', cls: 'total', shape: 'box' },
        { label: '감소', cls: 'dec', shape: 'box' },
        { label: '증가', cls: 'inc', shape: 'box' },
      ],
      { label: '막대 색' },
    );

    // 각 열의 라벨은 여러 줄(lines)로 받아 좁은 화면에서도 겹치지 않게 쓴다.
    const columns = [{ kind: 'total', lines: start.lines, name: start.name, from: 0, to: start.value, value: start.value }];
    let running = start.value;
    for (const s of steps) {
      columns.push({ kind: s.value < 0 ? 'dec' : 'inc', lines: s.lines, name: s.name, from: running, to: running + s.value, value: s.value });
      running += s.value;
    }
    if (running !== end.value) throw new Error('폭포 차트의 끝 합계가 맞지 않는다');
    columns.push({ kind: 'total', lines: end.lines, name: end.name, from: 0, to: end.value, value: end.value });
    const maxLines = Math.max(...columns.map((c) => c.lines.length));

    responsive(mount, (width) => {
      const plot = plotArea(mount);
      const height = Math.round(Math.max(280, Math.min(340, width * 0.46)));
      const margin = { top: 26, right: 8, bottom: 22 + maxLines * 16, left: 44 };
      const svg = chartSvg(plot, { width, height, labelledBy, describedBy });
      const max = niceDomain(0, Math.max(...columns.flatMap((c) => [c.from, c.to])), 4)[1];
      const y = linear([0, max], [height - margin.bottom, margin.top]);
      const keys = columns.map((_, i) => String(i));
      const x = band(keys, [margin.left, width - margin.right], { inner: 0.4, outer: 0.15 });
      const barW = Math.min(28, x.bandwidth);
      // 칸이 좁아 라벨이 맞닿으면 라벨만 한 단계 작게 쓴다.
      const widest = Math.max(...columns.flatMap((c) => c.lines.map((line, k) => measure(svg, line, k === 0 ? 'axis-label axis-label--strong' : 'axis-label'))));
      const compact = widest > x.step - 4 ? ' axis-label--compact' : '';
      const deco = svgEl('g', { 'aria-hidden': 'true' }, svg);
      const base = y(0);

      for (const t of y.ticks(4)) {
        svgEl('line', { class: t === 0 ? 'baseline' : 'grid', x1: margin.left, x2: width - margin.right, y1: y(t), y2: y(t) }, deco);
        svgText(deco, margin.left - 8, y(t), fmt(t), { class: 'axis-label', 'text-anchor': 'end', 'dominant-baseline': 'middle' });
      }

      const layer = svgEl('g', { class: 'datums' }, svg);
      const items = columns.map((c, i) => {
        const cx = x.center(String(i));
        const yTop = y(Math.max(c.from, c.to));
        const yBottom = y(Math.min(c.from, c.to));
        if (i < columns.length - 1) {
          const next = x.center(String(i + 1));
          svgEl('line', { class: 'connector', x1: cx + barW / 2, x2: next - barW / 2, y1: y(c.to), y2: y(c.to) }, deco);
        }
        const g = svgEl('g', {}, layer);
        svgEl('rect', { class: 'hit', x: x(String(i)) - (x.step - x.bandwidth) / 2, y: margin.top - 20, width: x.step, height: base - margin.top + 20 }, g);
        const d = c.kind === 'total' ? columnPath(cx - barW / 2, barW, base, yTop) : `M${cx - barW / 2},${yTop}h${barW}v${Math.max(1, yBottom - yTop)}h${-barW}Z`;
        svgEl('path', { class: `bar ${c.kind}`, d }, g);
        svgEl('rect', { class: 'focus-ring', x: cx - barW / 2 - 5, y: yTop - 24, width: barW + 10, height: yBottom - yTop + 28, rx: 5 }, g);
        const text = c.kind === 'total' ? `${fmt(c.value)}${unit}` : fmtSigned(c.value);
        svgText(deco, cx, yTop - 8, text, { class: 'label label--value', 'text-anchor': 'middle' });
        c.lines.forEach((line, k) => {
          svgText(deco, cx, base + 18 + k * 16, line, { class: `axis-label${k === 0 ? ' axis-label--strong' : ''}${compact}`, 'text-anchor': 'middle' });
        });
        // 화면 라벨은 짧게 줄을 나누고, 보조기술과 툴팁에는 온전한 이름(name)을 쓴다.
        const name = c.name ?? c.lines.join(' ');
        return {
          el: g,
          label: `${name}: ${c.kind === 'total' ? `${fmt(c.value)}${unit}` : `${fmtSigned(c.value)}${unit}`}`,
          tooltip: {
            title: name,
            rows: [{ key: 'box', cls: c.kind, value: c.kind === 'total' ? `${fmt(c.value)}${unit}` : `${fmtSigned(c.value)}${unit}`, label: c.kind === 'total' ? '순증 합계' : '순증 수량 차이' }],
          },
          anchor: { x: cx + barW / 2, y: yTop },
        };
      });
      interact(mount, svg, items);
    });
  }

  A11y.charts = Object.assign(A11y.charts || {}, { waterfallChart });
})((window.A11y = window.A11y || {}));

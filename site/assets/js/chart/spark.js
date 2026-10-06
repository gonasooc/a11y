// 첫 화면 수치 카드용 작은 그림. 수치와 문장이 같은 내용을 전하므로 보조기술에서는 숨긴다.
(function (A11y) {
  'use strict';
  const { columnPath, linear, plotArea, point, responsive, svgEl } = A11y.chart;

  function sparkLine(mount, values) {
    responsive(mount, (width) => {
      const plot = plotArea(mount);
      const height = 44;
      const svg = svgEl('svg', { width, height, viewBox: `0 0 ${width} ${height}`, 'aria-hidden': 'true', focusable: 'false', class: 'spark' }, plot);
      const min = Math.min(...values);
      const max = Math.max(...values);
      const x = point(values.map((_, i) => i), [5, width - 5]);
      const y = linear([min, max], [height - 6, 6]);
      const d = values.map((v, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join('');
      svgEl('path', { class: 'area s1', d: `${d}L${x(values.length - 1)},${height}L${x(0)},${height}Z` }, svg);
      svgEl('path', { class: 'line s1', d }, svg);
      svgEl('circle', { class: 'dot s1', cx: x(0), cy: y(values[0]), r: 3.5 }, svg);
      svgEl('circle', { class: 'dot s1', cx: x(values.length - 1), cy: y(values.at(-1)), r: 4 }, svg);
    });
  }

  function sparkBars(mount, values, isHighlighted) {
    responsive(mount, (width) => {
      const plot = plotArea(mount);
      const height = 44;
      const svg = svgEl('svg', { width, height, viewBox: `0 0 ${width} ${height}`, 'aria-hidden': 'true', focusable: 'false', class: 'spark' }, plot);
      const max = Math.max(...values);
      const step = width / values.length;
      const barW = Math.max(2, Math.min(8, step - 2));
      const y = linear([0, max], [height - 1, 2]);
      values.forEach((v, i) => {
        const cx = step * i + step / 2;
        svgEl('path', { class: `bar ${isHighlighted(i) ? 's1' : 'bar--muted'}`, d: columnPath(cx - barW / 2, barW, height - 1, y(v), 2) }, svg);
      });
    });
  }

  function sparkMeter(mount, share) {
    const track = document.createElement('span');
    track.className = 'spark-meter';
    track.setAttribute('aria-hidden', 'true');
    const fill = document.createElement('span');
    fill.className = 'spark-meter__fill';
    fill.style.setProperty('--v', `${share}%`);
    track.append(fill);
    mount.replaceChildren(track);
  }

  A11y.charts = Object.assign(A11y.charts || {}, { sparkLine, sparkBars, sparkMeter });
})((window.A11y = window.A11y || {}));

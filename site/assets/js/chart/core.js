// 차트 공통 도구: SVG 생성, 척도, 반응형 다시 그리기, 툴팁, 키보드 탐색.
// 모든 라벨은 textContent로 넣는다(데이터 문자열을 HTML로 해석하지 않는다).
(function (A11y) {
  'use strict';

  /*
   * ticks·tickIncrement·nice는 d3-array 3.2.4(src/ticks.js, src/nice.js)에서 옮겼다.
   * Copyright 2010-2023 Mike Bostock
   *
   * Permission to use, copy, modify, and/or distribute this software for any purpose
   * with or without fee is hereby granted, provided that the above copyright notice
   * and this permission notice appear in all copies.
   *
   * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
   * REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
   * FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
   * INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
   * OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
   * TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF
   * THIS SOFTWARE.
   */
  const e10 = Math.sqrt(50);
  const e5 = Math.sqrt(10);
  const e2 = Math.sqrt(2);

  function tickSpec(start, stop, count) {
    const step = (stop - start) / Math.max(0, count);
    const power = Math.floor(Math.log10(step));
    const error = step / Math.pow(10, power);
    const factor = error >= e10 ? 10 : error >= e5 ? 5 : error >= e2 ? 2 : 1;
    let i1;
    let i2;
    let inc;
    if (power < 0) {
      inc = Math.pow(10, -power) / factor;
      i1 = Math.round(start * inc);
      i2 = Math.round(stop * inc);
      if (i1 / inc < start) ++i1;
      if (i2 / inc > stop) --i2;
      inc = -inc;
    } else {
      inc = Math.pow(10, power) * factor;
      i1 = Math.round(start / inc);
      i2 = Math.round(stop / inc);
      if (i1 * inc < start) ++i1;
      if (i2 * inc > stop) --i2;
    }
    if (i2 < i1 && 0.5 <= count && count < 2) return tickSpec(start, stop, count * 2);
    return [i1, i2, inc];
  }

  function d3ticks(start, stop, count) {
    stop = +stop;
    start = +start;
    count = +count;
    if (!(count > 0)) return [];
    if (start === stop) return [start];
    const reverse = stop < start;
    const [i1, i2, inc] = reverse ? tickSpec(stop, start, count) : tickSpec(start, stop, count);
    if (!(i2 >= i1)) return [];
    const n = i2 - i1 + 1;
    const out = new Array(n);
    if (reverse) {
      if (inc < 0) for (let i = 0; i < n; ++i) out[i] = (i2 - i) / -inc;
      else for (let i = 0; i < n; ++i) out[i] = (i2 - i) * inc;
    } else {
      if (inc < 0) for (let i = 0; i < n; ++i) out[i] = (i1 + i) / -inc;
      else for (let i = 0; i < n; ++i) out[i] = (i1 + i) * inc;
    }
    return out;
  }

  function tickIncrement(start, stop, count) {
    return tickSpec(+start, +stop, +count)[2];
  }

  function d3nice(start, stop, count) {
    let prestep;
    while (true) {
      const step = tickIncrement(start, stop, count);
      if (step === prestep || step === 0 || !isFinite(step)) {
        return [start, stop];
      } else if (step > 0) {
        start = Math.floor(start / step) * step;
        stop = Math.ceil(stop / step) * step;
      } else if (step < 0) {
        start = Math.ceil(start * step) / step;
        stop = Math.floor(stop * step) / step;
      }
      prestep = step;
    }
  }

  const SVG_NS = 'http://www.w3.org/2000/svg';

  function svgEl(tag, attrs = {}, parent) {
    const el = document.createElementNS(SVG_NS, tag);
    for (const [key, value] of Object.entries(attrs)) {
      if (value === undefined || value === null || value === false) continue;
      el.setAttribute(key, value === true ? '' : String(value));
    }
    if (parent) parent.append(el);
    return el;
  }

  function svgText(parent, x, y, text, attrs = {}) {
    const el = svgEl('text', { x, y, ...attrs }, parent);
    el.textContent = text;
    return el;
  }

  function htmlEl(tag, attrs = {}, ...children) {
    const el = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs)) {
      if (value === undefined || value === null || value === false) continue;
      if (key === 'text') el.textContent = value;
      else if (key === 'className') el.className = value;
      else el.setAttribute(key, value === true ? '' : String(value));
    }
    for (const child of children) if (child !== null && child !== undefined) el.append(child);
    return el;
  }

  /* ---------- 척도 ---------- */

  function linear([d0, d1], [r0, r1]) {
    const k = (r1 - r0) / (d1 - d0 || 1);
    const scale = (value) => r0 + (value - d0) * k;
    scale.ticks = (count = 5) => d3ticks(d0, d1, count);
    scale.domain = [d0, d1];
    scale.range = [r0, r1];
    return scale;
  }

  const niceDomain = (min, max, count = 5) => d3nice(min, max, count);

  /** 막대용 띠 척도. bandwidth는 막대 두께 상한(24px)과 별개로 칸의 너비다. */
  function band(keys, [r0, r1], { inner = 0.3, outer = 0.2 } = {}) {
    const n = keys.length;
    const step = (r1 - r0) / Math.max(1, n - inner + outer * 2);
    const start = r0 + step * outer;
    const index = new Map(keys.map((key, i) => [key, i]));
    const scale = (key) => start + step * index.get(key);
    scale.step = step;
    scale.bandwidth = step * (1 - inner);
    scale.center = (key) => scale(key) + scale.bandwidth / 2;
    return scale;
  }

  /** 선 차트용 점 척도: 첫 값과 끝 값이 범위 양 끝에 놓인다. */
  function point(keys, [r0, r1]) {
    const step = keys.length > 1 ? (r1 - r0) / (keys.length - 1) : 0;
    const index = new Map(keys.map((key, i) => [key, i]));
    const scale = (key) => r0 + step * index.get(key);
    scale.step = step;
    return scale;
  }

  /** 막대 끝만 둥근(4px) 세로 막대 경로. 기준선 쪽은 직각이다. */
  function columnPath(x, width, yBase, yValue, radius = 4) {
    const top = Math.min(yBase, yValue);
    const height = Math.abs(yBase - yValue);
    const r = Math.min(radius, width / 2, height);
    if (yValue <= yBase) {
      return `M${x},${yBase}V${top + r}Q${x},${top} ${x + r},${top}H${x + width - r}Q${x + width},${top} ${x + width},${top + r}V${yBase}Z`;
    }
    const bottom = top + height;
    return `M${x},${yBase}V${bottom - r}Q${x},${bottom} ${x + r},${bottom}H${x + width - r}Q${x + width},${bottom} ${x + width},${bottom - r}V${yBase}Z`;
  }

  /** 가로 막대(오른쪽 끝만 둥근) 경로. */
  function barPath(xBase, xValue, y, height, radius = 4) {
    const left = Math.min(xBase, xValue);
    const width = Math.abs(xValue - xBase);
    const r = Math.min(radius, height / 2, width);
    const right = left + width;
    return `M${left},${y}H${right - r}Q${right},${y} ${right},${y + r}V${y + height - r}Q${right},${y + height} ${right - r},${y + height}H${left}Z`;
  }

  /** 텍스트 너비를 잰다(같은 SVG 안에서 측정해야 정확하다). */
  function measure(svg, text, className = 'label') {
    const probe = svgText(svg, -9999, -9999, text, { class: className });
    const width = probe.getComputedTextLength();
    probe.remove();
    return width;
  }

  /** 세로로 겹치는 라벨을 최소 간격만큼 떼어 놓는다. items: [{ y }] → 각 item.labelY를 채운다. */
  function spreadLabels(items, gap, [minY, maxY]) {
    const sorted = [...items].sort((a, b) => a.y - b.y);
    sorted.forEach((item, i) => {
      item.labelY = Math.max(item.y, i ? sorted[i - 1].labelY + gap : minY);
    });
    const overflow = sorted.length ? sorted.at(-1).labelY - maxY : 0;
    if (overflow > 0) {
      for (let i = sorted.length - 1; i >= 0; i -= 1) {
        sorted[i].labelY = Math.min(sorted[i].labelY - overflow, i < sorted.length - 1 ? sorted[i + 1].labelY - gap : maxY);
      }
    }
    return items;
  }

  /* ---------- 반응형 ---------- */

  /** 마운트 너비가 바뀔 때마다 draw(width)를 다시 호출하고, 키보드 초점 위치를 되살린다. */
  function responsive(mount, draw) {
    let lastWidth = 0;
    let frame = 0;
    const run = () => {
      const width = Math.floor(mount.getBoundingClientRect().width);
      if (!width || width === lastWidth) return;
      lastWidth = width;
      const datums = [...mount.querySelectorAll('.datum')];
      const focused = datums.indexOf(document.activeElement);
      draw(width);
      if (focused >= 0) mount.querySelectorAll('.datum')[focused]?.focus({ preventScroll: true });
    };
    const observer = new ResizeObserver(() => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(run);
    });
    observer.observe(mount);
    // 웹 글꼴이 늦게 도착하면 글자 폭이 바뀌므로 한 번 더 그린다(라벨 위치를 글꼴 기준으로 다시 잰다).
    // requestAnimationFrame은 숨은 탭에서 멈추므로 짧은 타이머로 모아서 한 번만 그린다.
    if (document.fonts) {
      let fontTimer = 0;
      document.fonts.addEventListener('loadingdone', () => {
        clearTimeout(fontTimer);
        fontTimer = setTimeout(() => {
          lastWidth = 0;
          run();
        }, 50);
      });
    }
    run();
  }

  /** 마운트 안의 그림 영역(.viz-plot)을 비우고 돌려준다. */
  function plotArea(mount) {
    let plot = mount.querySelector(':scope > .viz-plot');
    if (!plot) {
      plot = htmlEl('div', { className: 'viz-plot' });
      mount.append(plot);
    }
    plot.replaceChildren();
    return plot;
  }

  /** 접근 가능한 SVG 틀: 제목·요약은 figure의 캡션을 가리킨다. */
  function chartSvg(plot, { width, height, labelledBy, describedBy }) {
    return svgEl(
      'svg',
      {
        width,
        height,
        viewBox: `0 0 ${width} ${height}`,
        role: 'group',
        'aria-labelledby': labelledBy,
        'aria-describedby': describedBy,
        class: 'viz-svg',
      },
      plot,
    );
  }

  /* ---------- 범례 ---------- */

  /** items: [{ label, cls, shape: 'line' | 'box' | 'dot' }] */
  function legend(mount, items, { label = '범례' } = {}) {
    if (mount.querySelector(':scope > .viz-legend')) return;
    const list = htmlEl('ul', { className: 'viz-legend', role: 'list', 'aria-label': label });
    for (const item of items) {
      list.append(
        htmlEl(
          'li',
          { className: `viz-legend__item ${item.cls ?? ''}` },
          htmlEl('span', { className: `key key--${item.shape ?? 'box'}`, 'aria-hidden': 'true' }),
          htmlEl('span', { text: item.label }),
        ),
      );
    }
    mount.prepend(list);
  }

  /* ---------- 툴팁 ---------- */

  function tooltip(mount) {
    let el = mount.querySelector(':scope > .viz-tip');
    if (!el) {
      el = htmlEl('div', { className: 'viz-tip', 'aria-hidden': 'true', hidden: true });
      mount.append(el);
    }
    return {
      show(content, anchor, svg) {
        el.replaceChildren();
        if (content.title) el.append(htmlEl('p', { className: 'viz-tip__title', text: content.title }));
        const list = htmlEl('ul', { className: 'viz-tip__rows', role: 'list' });
        for (const row of content.rows ?? []) {
          list.append(
            htmlEl(
              'li',
              { className: `viz-tip__row ${row.cls ?? ''}` },
              row.key ? htmlEl('span', { className: `key key--${row.key}`, 'aria-hidden': 'true' }) : null,
              htmlEl('strong', { text: row.value }),
              row.label ? htmlEl('span', { className: 'viz-tip__label', text: row.label }) : null,
            ),
          );
        }
        el.append(list);
        if (content.note) el.append(htmlEl('p', { className: 'viz-tip__note', text: content.note }));
        el.hidden = false;

        const mountBox = mount.getBoundingClientRect();
        const svgBox = svg.getBoundingClientRect();
        const x = svgBox.left - mountBox.left + anchor.x;
        const y = svgBox.top - mountBox.top + anchor.y;
        const tipBox = el.getBoundingClientRect();
        let left = x + 14;
        if (left + tipBox.width > mountBox.width) left = x - 14 - tipBox.width;
        left = Math.max(0, Math.min(left, mountBox.width - tipBox.width));
        const top = Math.max(0, y - tipBox.height / 2);
        el.style.left = `${left}px`;
        el.style.top = `${top}px`;
      },
      hide() {
        el.hidden = true;
      },
    };
  }

  /* ---------- 상호작용 ---------- */

  /**
   * items: [{ el, label, tooltip: { title, rows, note }, anchor: { x, y } }]
   * - 차트당 탭 정지점은 하나(로빙 tabindex)이고, 화살표·Home·End로 값 사이를 움직인다.
   * - 마우스·터치는 같은 툴팁을 보여 주며 초점은 옮기지 않는다.
   */
  function interact(mount, svg, items) {
    const tip = tooltip(mount);
    let active = -1;

    const activate = (i) => {
      if (active >= 0 && items[active]) items[active].el.classList.remove('is-active');
      active = i;
      items[i].el.classList.add('is-active');
      tip.show(items[i].tooltip, items[i].anchor, svg);
    };
    const deactivate = () => {
      if (active >= 0 && items[active]) items[active].el.classList.remove('is-active');
      active = -1;
      tip.hide();
    };

    items.forEach((item, i) => {
      const el = item.el;
      el.classList.add('datum');
      el.setAttribute('role', 'img');
      el.setAttribute('aria-label', item.label);
      el.setAttribute('tabindex', i === 0 ? '0' : '-1');
      el.addEventListener('pointerenter', () => activate(i));
      el.addEventListener('pointerdown', () => activate(i));
      el.addEventListener('focus', () => {
        items.forEach((other, j) => other.el.setAttribute('tabindex', j === i ? '0' : '-1'));
        activate(i);
      });
      el.addEventListener('blur', () => {
        requestAnimationFrame(() => {
          if (!svg.contains(document.activeElement)) deactivate();
        });
      });
    });

    svg.addEventListener('pointerleave', () => {
      if (!svg.contains(document.activeElement)) deactivate();
    });

    svg.addEventListener('keydown', (event) => {
      const i = items.findIndex((item) => item.el === document.activeElement);
      if (i < 0) return;
      let next;
      switch (event.key) {
        case 'ArrowRight':
        case 'ArrowDown':
          next = Math.min(items.length - 1, i + 1);
          break;
        case 'ArrowLeft':
        case 'ArrowUp':
          next = Math.max(0, i - 1);
          break;
        case 'Home':
          next = 0;
          break;
        case 'End':
          next = items.length - 1;
          break;
        case 'Escape':
          tip.hide();
          return;
        default:
          return;
      }
      event.preventDefault();
      items[next].el.focus();
    });
  }

  A11y.chart = { svgEl, svgText, htmlEl, linear, band, point, columnPath, barPath, measure, spreadLabels, responsive, plotArea, chartSvg, legend, interact, niceDomain };
})((window.A11y = window.A11y || {}));

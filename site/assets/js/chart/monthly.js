// 월별 납품요구 순증: 비교 구간 띠, 정책 일정 표식, 전환월 표시가 있는 세로 막대.
(function (A11y) {
  'use strict';
  const { fmt, monthLabel } = A11y.format;
  const { band, chartSvg, columnPath, htmlEl, interact, legend, linear, niceDomain, plotArea, responsive, svgEl, svgText } = A11y.chart;

  const CIRCLED = ['', '①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨'];

  function inWindow(month, windows) {
    const [year, m] = month.split('-').map(Number);
    return windows.find((w) => w.year === year && m >= w.from && m <= w.to);
  }

  function monthlyChart(mount, opts) {
    const { months, windows, transition, january, events, labelledBy, describedBy } = opts;
    legend(
      mount,
      [
        { label: '주 비교 구간(2~9월)의 달', cls: 's1', shape: 'box' },
        { label: '비교에서 뺀 달', cls: 'muted', shape: 'box' },
      ],
      { label: '막대 색' },
    );

    responsive(mount, (width) => {
      const plot = plotArea(mount);
      const keys = months.map((m) => m.month);
      const margin = { top: 0, right: 12, bottom: 46, left: 40 };
      const x = band(keys, [margin.left, width - margin.right], { inner: 0.3, outer: 0.15 });

      // 정책 일정 표식이 겹치지 않도록 줄을 나눈다.
      const cellStart = (key) => x(key) - (x.step * 0.3) / 2;
      const xDate = (date) => {
        const [yy, mm, dd] = date.split('-').map(Number);
        const days = new Date(yy, mm, 0).getDate();
        return cellStart(`${yy}-${String(mm).padStart(2, '0')}`) + x.step * ((dd - 0.5) / days);
      };
      const lanes = [];
      const placed = events.map((e) => {
        const ex = xDate(e.date);
        let lane = lanes.findIndex((last) => ex - last >= 21);
        if (lane < 0) {
          lane = lanes.length;
          lanes.push(ex);
        } else {
          lanes[lane] = ex;
        }
        return { ...e, x: ex, lane };
      });
      const laneH = 22;
      margin.top = lanes.length * laneH + 30;
      const height = margin.top + Math.round(Math.max(200, Math.min(280, width * 0.36))) + margin.bottom;
      const svg = chartSvg(plot, { width, height, labelledBy, describedBy });
      const max = niceDomain(0, Math.max(...months.map((m) => m.qty)), 4)[1];
      const y = linear([0, max], [height - margin.bottom, margin.top]);
      const base = y(0);
      const barW = Math.min(24, x.bandwidth);
      const deco = svgEl('g', { 'aria-hidden': 'true' }, svg);

      for (const w of windows) {
        const k0 = `${w.year}-${String(w.from).padStart(2, '0')}`;
        const k1 = `${w.year}-${String(w.to).padStart(2, '0')}`;
        const x0 = cellStart(k0) + 1;
        const x1 = cellStart(k1) + x.step - 1;
        svgEl('rect', { class: 'window-band', x: x0, y: margin.top - 4, width: x1 - x0, height: base - margin.top + 4, rx: 6 }, deco);
        // 띠 오른쪽 끝에 붙여 쓴다(왼쪽 끝은 1월 막대의 라벨과 겹칠 수 있다).
        const text = x1 - x0 > 170 ? `${w.year}년 ${w.from}~${w.to}월 합계 ${fmt(w.total)}대` : `${fmt(w.total)}대`;
        svgText(deco, x1 - 8, margin.top + 12, text, { class: 'window-label', 'text-anchor': 'end' });
      }

      for (const t of y.ticks(4)) {
        svgEl('line', { class: t === 0 ? 'baseline' : 'grid', x1: margin.left, x2: width - margin.right, y1: y(t), y2: y(t) }, deco);
        svgText(deco, margin.left - 8, y(t), fmt(t), { class: 'axis-label', 'text-anchor': 'end', 'dominant-baseline': 'middle' });
      }

      // 정책 일정 표식: 번호는 아래 목록과 1장의 일정 목록 번호와 같다.
      for (const e of placed) {
        const cy = 12 + e.lane * laneH;
        svgEl('line', { class: `event-tick${e.role === 'treatment' ? ' event-tick--main' : ''}`, x1: e.x, x2: e.x, y1: cy + 9, y2: margin.top - 6 }, deco);
        svgEl('circle', { class: `event-dot${e.role === 'treatment' ? ' event-dot--main' : ''}`, cx: e.x, cy, r: 9 }, deco);
        svgText(deco, e.x, cy + 0.5, String(e.n), { class: `event-num${e.role === 'treatment' ? ' event-num--main' : ''}`, 'text-anchor': 'middle', 'dominant-baseline': 'central' });
      }

      const showAll = x.step >= 26;
      months.forEach((m) => {
        const mm = Number(m.month.slice(5));
        if (showAll || [1, 4, 7, 10].includes(mm)) {
          svgText(deco, x.center(m.month), height - margin.bottom + 18, `${mm}`, { class: 'axis-label', 'text-anchor': 'middle' });
        }
        if (mm === 1) {
          svgText(deco, cellStart(m.month) + 2, height - margin.bottom + 37, `${m.month.slice(0, 4)}년`, { class: 'axis-label axis-label--strong' });
        }
      });
      svgText(deco, width - margin.right, height - margin.bottom + 37, '접수월', { class: 'axis-label', 'text-anchor': 'end' });

      const peak = months.reduce((a, b) => (b.qty > a.qty ? b : a));
      const layer = svgEl('g', { class: 'datums' }, svg);
      const items = months.map((m) => {
        const cx = x.center(m.month);
        const win = inWindow(m.month, windows);
        const isTransition = m.month === transition;
        const g = svgEl('g', {}, layer);
        svgEl('rect', { class: 'hit', x: cellStart(m.month), y: margin.top - 4, width: x.step, height: base - margin.top + 4 }, g);
        svgEl('path', { class: `bar ${win ? 's1' : 'bar--muted'}`, d: columnPath(cx - barW / 2, barW, base, y(m.qty)) }, g);
        svgEl('rect', { class: 'focus-ring', x: cx - barW / 2 - 5, y: y(m.qty) - 6, width: barW + 10, height: base - y(m.qty) + 10, rx: 5 }, g);
        // 막대가 좁으면 최댓값만 쓰고 나머지는 툴팁과 표에 맡긴다.
        const roomy = x.step >= 28;
        if (m.month === peak.month || (isTransition && roomy)) {
          svgText(deco, cx, y(m.qty) - 7, fmt(m.qty), { class: 'label label--value', 'text-anchor': 'middle' });
        }
        if (isTransition && roomy) {
          svgText(deco, cx, y(m.qty) - 22, '전환월', { class: 'label label--note', 'text-anchor': 'middle' });
        }
        const jan = january.find((j) => `${j.year}-01` === m.month);
        const status = win ? `주 비교 구간(${win.year}년 ${win.from}~${win.to}월)` : isTransition ? '전환월: 비교에서 뺐다' : '비교에서 뺀 달';
        const rows = [
          { key: 'box', cls: win ? 's1' : 'muted', value: `${fmt(m.qty)}대`, label: '순증 수량' },
          { value: `${fmt(m.eok, 2)}억원`, label: '순증 금액' },
          { value: `${fmt(m.requests)}개`, label: '변경 관측 요구번호' },
          { value: `${fmt(m.institutions)}곳`, label: '수요기관' },
        ];
        if (jan) rows.push({ value: `${fmt(jan.early)}대 + ${fmt(jan.late)}대`, label: '1~21일 + 22~31일' });
        return {
          el: g,
          label: `${monthLabel(m.month)}: 순증 ${fmt(m.qty)}대, ${status}${jan ? `, 1~21일 ${fmt(jan.early)}대와 22~31일 ${fmt(jan.late)}대` : ''}`,
          tooltip: { title: monthLabel(m.month), rows, note: status },
          anchor: { x: cx + barW / 2, y: y(m.qty) },
        };
      });
      interact(mount, svg, items);
    });

    if (!mount.querySelector(':scope > .viz-events')) {
      const list = htmlEl('ol', { className: 'viz-events', role: 'list', 'aria-label': '차트 위 번호가 가리키는 정책 일정' });
      for (const e of events) {
        list.append(
          htmlEl(
            'li',
            { className: e.role === 'treatment' ? 'is-main' : '' },
            htmlEl('span', { className: 'viz-events__n', 'aria-hidden': 'true', text: CIRCLED[e.n] ?? String(e.n) }),
            htmlEl('time', { datetime: e.date, text: e.date }),
            ' ',
            htmlEl('span', { text: e.label }),
          ),
        );
      }
      mount.append(list);
    }
  }

  A11y.charts = Object.assign(A11y.charts || {}, { monthlyChart });
})((window.A11y = window.A11y || {}));

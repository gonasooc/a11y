// 영상 접근성 보고서: 생성 구역의 JSON으로 차트를 그리고 목차를 연결한다.
// 일반 스크립트(defer)다. 공통 스크립트가 window.A11y에 올려 둔 함수를 쓴다.
(function (A11y) {
  'use strict';
  const { columnChart, lineChart, refBars } = A11y.charts;

  const data = JSON.parse(document.getElementById('report-data').textContent);

  /** 차트 하나가 실패해도 나머지는 그리고, 표로 보기를 안내한다. */
  function render(key, draw) {
    const el = document.querySelector(`[data-viz="${key}"]`);
    if (!el) return;
    try {
      draw(el, { labelledBy: el.dataset.labelledby, describedBy: el.dataset.describedby });
    } catch (error) {
      console.error(`[${key}] 차트를 그리지 못했다`, error);
      el.replaceChildren();
      const message = document.createElement('p');
      message.className = 'note';
      message.textContent = '차트를 그리지 못했다. 같은 값은 표로 보기에서 확인할 수 있다.';
      el.append(message);
    }
  }

  render('registryAge', (el, ids) =>
    lineChart(el, { years: data.registryAge.years, series: data.registryAge.series, yDomain: [0, 40], digits: 1, ...ids }),
  );
  render('ccBelow', (el, ids) =>
    columnChart(el, { items: data.ccBelow, digits: 0, unit: '곳', tooltipNote: '폐쇄자막 실적이 목표보다 작은 방송사', ...ids }),
  );
  render('earlyBelow', (el, ids) =>
    columnChart(el, { items: data.earlyBelow, digits: 0, unit: '곳', tooltipNote: '폐쇄자막·화면해설·한국수어 가운데 하나라도 목표보다 작은 방송사', ...ids }),
  );
  render('terrestrial', (el, ids) =>
    refBars(el, { items: data.terrestrial, domain: [0, 100], unit: '%', digits: 2, ticks: 4, tooltipNote: '지상파 방송사별 실적의 단순 평균', ...ids }),
  );
  render('tvService', (el, ids) =>
    refBars(el, { items: data.tvService, domain: [0, 100], unit: '%', digits: 1, ticks: 4, tooltipNote: '하나만 고르는 문항, 세 값의 합 100%', ...ids }),
  );
  render('rerun', (el, ids) =>
    refBars(el, { items: data.rerun, domain: [0, 30], ref: { value: 25, label: '상한 25%' }, unit: '%', digits: 2, ticks: 3, tooltipNote: '화면해설 의무 편성 중 재방송 비율', ...ids }),
  );

  /* 주소의 # 대상이 접힌 노트 안에 있으면 바깥 <details>까지 모두 펼친 뒤 그 위치로 이동한다. */
  const openTarget = () => {
    const id = decodeURIComponent(location.hash.slice(1));
    const target = id && document.getElementById(id);
    if (!target) return;
    let opened = false;
    const own = target.matches('.analysis-note') ? target.querySelector(':scope > details.note-details') : null;
    if (own && !own.open) {
      own.open = true;
      opened = true;
    }
    for (let el = target; el; el = el.parentElement?.closest('details')) {
      const details = el.closest('details');
      if (!details) break;
      if (!details.open) {
        details.open = true;
        opened = true;
      }
      el = details;
    }
    if (opened) target.scrollIntoView();
  };
  openTarget();
  window.addEventListener('hashchange', openTarget);

  /* 목차: 넓은 화면에서는 항상 펼치고, 읽는 위치를 표시한다. */
  const toc = document.querySelector('[data-toc]');
  if (toc) {
    const wide = matchMedia('(min-width: 74rem)');
    const syncOpen = () => {
      if (wide.matches) toc.open = true;
    };
    toc.open = wide.matches;
    wide.addEventListener('change', syncOpen);

    const links = [...toc.querySelectorAll('a[href^="#"]')];
    const byId = new Map(links.map((a) => [decodeURIComponent(a.hash.slice(1)), a]));
    const visible = new Map();
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) visible.set(entry.target.id, entry.isIntersecting);
        const current = [...byId.keys()].find((id) => visible.get(id));
        for (const [id, link] of byId) {
          if (id === current) link.setAttribute('aria-current', 'true');
          else link.removeAttribute('aria-current');
        }
      },
      { rootMargin: '-15% 0px -70% 0px' },
    );
    for (const id of byId.keys()) {
      const section = document.getElementById(id);
      if (section) observer.observe(section);
    }
    toc.addEventListener('click', (event) => {
      if (event.target.closest('a') && !wide.matches) toc.open = false;
    });
  }
})(window.A11y);

// 브라우저(window.A11y.format)와 데이터 생성 스크립트(Node, require)가 함께 쓰는 한국어 숫자 형식.
// 반올림은 Intl 기본값(0.5는 0에서 먼 쪽)으로, 분석 코드의 ROUND_HALF_UP과 양수에서 같다.
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else (root.A11y = root.A11y || {}).format = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const MINUS = '−';

  const cache = new Map();
  function nf(digits) {
    if (!cache.has(digits)) {
      cache.set(digits, new Intl.NumberFormat('ko-KR', { minimumFractionDigits: digits, maximumFractionDigits: digits }));
    }
    return cache.get(digits);
  }

  function round(value, digits = 0) {
    const factor = 10 ** digits;
    return (Math.round((Math.abs(value) + Number.EPSILON) * factor) / factor) * Math.sign(value);
  }

  /** 1,234 / −12.5 처럼 쓴다. */
  function fmt(value, digits = 0) {
    const r = round(value, digits);
    const text = nf(digits).format(Math.abs(r));
    return r < 0 ? MINUS + text : text;
  }

  /** +3.7 / −275 / 0.0 처럼 부호를 붙인다. */
  function fmtSigned(value, digits = 0) {
    const r = round(value, digits);
    if (r > 0) return `+${nf(digits).format(r)}`;
    if (r < 0) return MINUS + nf(digits).format(-r);
    return nf(digits).format(0);
  }

  const fmtPct = (value, digits = 1) => `${fmt(value, digits)}%`;
  const fmtSignedPct = (value, digits = 1) => `${fmtSigned(value, digits)}%`;

  /** 원 단위 금액을 억원 수로 바꾼다. */
  const toEok = (krw) => Number(krw) / 1e8;

  const pctChange = (before, after) => ((after - before) / before) * 100;

  /** '2026-02' → '2026년 2월' */
  function monthLabel(month) {
    const [y, m] = month.split('-');
    return `${y}년 ${Number(m)}월`;
  }

  return { MINUS, round, fmt, fmtSigned, fmtPct, fmtSignedPct, toEok, pctChange, monthLabel };
});

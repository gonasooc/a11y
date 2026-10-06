const ESCAPES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };

export function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (ch) => ESCAPES[ch]);
}

/** JSON을 <script type="application/json">에 안전하게 넣는다. */
export function jsonForScript(value) {
  // "<"와 줄 구분 문자(U+2028, U+2029)를 JSON 이스케이프로 바꿔 스크립트 경계를 지킨다.
  const LS = String.fromCharCode(0x2028);
  const PS = String.fromCharCode(0x2029);
  return JSON.stringify(value)
    .replaceAll('<', '\\u003c')
    .replaceAll(LS, '\\u2028')
    .replaceAll(PS, '\\u2029');
}

function renderCell(value) {
  if (value && typeof value === 'object') {
    const main = value.href
      ? `<a href="${escapeHtml(value.href)}">${escapeHtml(value.text)}</a>`
      : `<span class="cell-main">${escapeHtml(value.text)}</span>`;
    const sub = value.sub ? `<span class="cell-sub">${escapeHtml(value.sub)}</span>` : '';
    return main + sub;
  }
  return escapeHtml(value ?? '');
}

function cellClass(col, value) {
  const classes = [];
  if (col?.numeric) classes.push('num');
  if (value && typeof value === 'object' && value.cls) classes.push(value.cls);
  return classes.length ? ` class="${escapeHtml(classes.join(' '))}"` : '';
}

/**
 * 표 정의를 접근 가능한 <table>로 만든다.
 * table = { caption, columns: [{ label, numeric }], rows: [[cell, ...]], rowHeader, note, className, scroll }
 * cell은 문자열이거나 { text, sub, cls, href } 객체다.
 */
export function renderTable(table) {
  const head = table.columns
    .map((col) => `<th scope="col"${cellClass(col)}>${escapeHtml(col.label)}</th>`)
    .join('');
  const body = table.rows
    .map((row) => {
      const cells = row
        .map((value, i) => {
          const col = table.columns[i];
          const tag = i === 0 && table.rowHeader !== false ? 'th scope="row"' : 'td';
          const close = tag.startsWith('th') ? 'th' : 'td';
          return `<${tag}${cellClass(col, value)}>${renderCell(value)}</${close}>`;
        })
        .join('');
      return `<tr>${cells}</tr>`;
    })
    .join('\n');
  const tableClass = ['data-table', table.className].filter(Boolean).join(' ');
  const html = `<table class="${escapeHtml(tableClass)}">
<caption>${escapeHtml(table.caption)}</caption>
<thead><tr>${head}</tr></thead>
<tbody>
${body}
</tbody>
</table>`;
  const note = table.note ? `<p class="table-note">${escapeHtml(table.note)}</p>` : '';
  if (table.scroll === false) return html + note;
  return `<div class="table-scroll" role="region" aria-label="${escapeHtml(table.caption)}" tabindex="0">
${html}
</div>${note}`;
}

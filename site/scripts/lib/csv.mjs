// RFC 4180 CSV를 머리글 기준 객체 배열로 읽는다.
// 따옴표 안의 쉼표·줄바꿈과 "" 이스케이프를 처리하고, 열 수가 머리글과 다르면 멈춘다.
const QUOTE = 34;
const COMMA = 44;
const LF = 10;
const CR = 13;
const BOM = 0xfeff;

export function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = '';
  let quoted = false;
  let i = text.charCodeAt(0) === BOM ? 1 : 0;
  for (; i < text.length; i += 1) {
    const code = text.charCodeAt(i);
    if (quoted) {
      if (code === QUOTE) {
        if (text.charCodeAt(i + 1) === QUOTE) {
          field += '"';
          i += 1;
        } else {
          quoted = false;
        }
      } else {
        field += text[i];
      }
    } else if (code === QUOTE && field === '') {
      quoted = true;
    } else if (code === COMMA) {
      row.push(field);
      field = '';
    } else if (code === LF || code === CR) {
      if (code === CR && text.charCodeAt(i + 1) === LF) i += 1;
      row.push(field);
      rows.push(row);
      row = [];
      field = '';
    } else {
      field += text[i];
    }
  }
  if (quoted) throw new Error('CSV: 닫히지 않은 따옴표가 있다');
  if (field !== '' || row.length) {
    row.push(field);
    rows.push(row);
  }
  const [header, ...body] = rows.filter((r) => !(r.length === 1 && r[0] === ''));
  return body.map((r, n) => {
    if (r.length !== header.length) throw new Error(`CSV ${n + 2}행: 열 수 ${r.length}개가 머리글 ${header.length}개와 다르다`);
    return Object.fromEntries(header.map((name, j) => [name, r[j]]));
  });
}

// 본문 숫자 검사: <태그 data-check="키" [data-abs]>숫자</태그>를 facts[키]와 표시한 자릿수로 비교한다.
// data-abs가 있으면 부호 없이 크기만 비교한다(예: "217대 감소").
const CHECK_RE = /<[a-z][\w-]*([^>]*\bdata-check="([^"]+)"[^>]*)>([^<]*)</g;

/** 본문 숫자 텍스트를 수와 소수 자릿수로 읽는다. 쉼표, 단위, 유니코드 빼기 기호를 허용한다. */
export function parseDisplayedNumber(text) {
  const normalized = text.replace(/−/g, '-').replace(/,/g, '');
  const match = normalized.match(/[-+]?\d+(?:\.(\d+))?/);
  if (!match) return null;
  return { value: Number(match[0]), decimals: match[1]?.length ?? 0 };
}

export function checkFacts(html, facts) {
  const problems = [];
  let count = 0;
  for (const [, attrs, key, text] of html.matchAll(CHECK_RE)) {
    count += 1;
    const absolute = /\bdata-abs\b/.test(attrs);
    if (!(key in facts)) {
      problems.push(`정의되지 않은 data-check 키: ${key}`);
      continue;
    }
    const shown = parseDisplayedNumber(text);
    if (!shown) {
      problems.push(`${key}: 숫자를 읽을 수 없다 → "${text}"`);
      continue;
    }
    const factor = 10 ** shown.decimals;
    const raw = absolute ? Math.abs(facts[key]) : facts[key];
    const expected = (Math.sign(raw) * Math.round((Math.abs(raw) + Number.EPSILON) * factor)) / factor;
    if (Math.abs(expected - shown.value) > 1e-9) {
      problems.push(`${key}: 본문 "${text.trim()}" ≠ 데이터 ${expected}`);
    }
  }
  return { problems, count };
}

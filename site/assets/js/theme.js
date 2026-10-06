// 화면 테마 선택(자동·밝게·어둡게). 저장소를 쓸 수 없는 환경(파일로 연 페이지 등)에서도 동작한다.
// <head>의 짧은 인라인 스크립트가 저장된 값을 먼저 적용하고, 이 파일은 선택 상자를 연결한다.
(function () {
  'use strict';
  const KEY = 'a11y-theme';
  const root = document.documentElement;
  const current = root.dataset.theme === 'light' || root.dataset.theme === 'dark' ? root.dataset.theme : 'auto';

  for (const group of document.querySelectorAll('[data-theme-switch]')) {
    for (const input of group.querySelectorAll('input[name="theme"]')) {
      input.checked = input.value === current;
      input.addEventListener('change', () => {
        if (!input.checked) return;
        if (input.value === 'auto') delete root.dataset.theme;
        else root.dataset.theme = input.value;
        try {
          if (input.value === 'auto') localStorage.removeItem(KEY);
          else localStorage.setItem(KEY, input.value);
        } catch {
          // 저장할 수 없으면 이번 방문에만 적용한다.
        }
      });
    }
  }
})();

/* Apply the preference before first paint. Storage is optional. */
(() => {
  'use strict';
  const themes = ['light', 'pink', 'dark'];
  const system = matchMedia('(prefers-color-scheme: dark)');
  let saved;
  try { saved = localStorage.getItem('ct-appearance'); } catch { /* Private storage may be unavailable. */ }
  let explicit = themes.includes(saved);
  function apply(theme) {
    document.documentElement.dataset.theme = theme;
    const choice = document.getElementById('theme-choice');
    if (choice) choice.value = theme;
    document.dispatchEvent(new Event('ct-theme-change'));
  }
  apply(explicit ? saved : system.matches ? 'dark' : 'light');
  system.addEventListener('change', event => { if (!explicit) apply(event.matches ? 'dark' : 'light'); });
  document.addEventListener('DOMContentLoaded', () => {
    const choice = document.getElementById('theme-choice');
    choice.value = document.documentElement.dataset.theme;
    choice.addEventListener('change', () => {
      explicit = true;
      apply(choice.value);
      try { localStorage.setItem('ct-appearance', choice.value); } catch { /* The theme still works for this visit. */ }
    });
  });
})();

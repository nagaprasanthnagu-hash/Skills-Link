/* ==========================================================================
   THEME-TOGGLE.JS — switches [data-theme] between "dark" and "light" on
   <html>, persists the choice in localStorage, and keeps every open tab's
   toggle icon in sync. The very first paint is handled separately by an
   inline snippet in <head> (see theme-init in the layout templates) so
   there's no flash of the wrong theme before this file even loads.
   ========================================================================== */
(function () {
  'use strict';
  var STORAGE_KEY = 'servora-theme';

  function applyIcon(theme) {
    document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
      var sun = btn.querySelector('[data-theme-icon-light]');
      var moon = btn.querySelector('[data-theme-icon-dark]');
      if (!sun || !moon) return;
      var isLight = theme === 'light';
      sun.classList.toggle('d-none', isLight);
      moon.classList.toggle('d-none', !isLight);
      btn.setAttribute('aria-label', isLight ? 'Switch to dark theme' : 'Switch to light theme');
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    applyIcon(document.documentElement.getAttribute('data-theme') || 'light');

    document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var current = document.documentElement.getAttribute('data-theme') || 'light';
        var next = current === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', next);
        try { localStorage.setItem(STORAGE_KEY, next); } catch (e) {}
        applyIcon(next);
      });
    });
  });
})();

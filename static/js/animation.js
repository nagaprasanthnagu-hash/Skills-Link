/* ==========================================================================
   ANIMATION.JS — hero glow that follows the pointer (CSS var driven,
   no canvas/Three.js — kept intentionally lightweight per design brief)
   ========================================================================== */
(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var glowHero = document.querySelector('[data-glow-hero]');
    if (!glowHero || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    glowHero.addEventListener('mousemove', function (e) {
      var rect = glowHero.getBoundingClientRect();
      var x = ((e.clientX - rect.left) / rect.width) * 100;
      var y = ((e.clientY - rect.top) / rect.height) * 100;
      glowHero.style.setProperty('--x', x + '%');
      glowHero.style.setProperty('--y', y + '%');
    });
  });
})();

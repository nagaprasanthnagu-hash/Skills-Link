/* ==========================================================================
   DASHBOARD.JS — lightweight 3D tilt for .card-tilt elements
   ========================================================================== */
(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var tiltCards = document.querySelectorAll('.card-tilt');
    if (!tiltCards.length || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    tiltCards.forEach(function (card) {
      card.addEventListener('mousemove', function (e) {
        var rect = card.getBoundingClientRect();
        var x = (e.clientX - rect.left) / rect.width - 0.5;
        var y = (e.clientY - rect.top) / rect.height - 0.5;
        card.style.setProperty('--ry', (x * 8) + 'deg');
        card.style.setProperty('--rx', (y * -8) + 'deg');
      });
      card.addEventListener('mouseleave', function () {
        card.style.setProperty('--rx', '0deg');
        card.style.setProperty('--ry', '0deg');
      });
    });
  });
})();

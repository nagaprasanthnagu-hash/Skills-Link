/* ==========================================================================
   SCROLL-MOTION.JS — Scroll Animation & Premium UI Enhancement PRD.
   Vanilla JS + IntersectionObserver only: animated stat counters and
   scroll-spy active-nav highlighting. Everything here fails safe: if JS
   never runs, the numbers/nav still show their real static values (no
   content depends on this file to be visible).
   ========================================================================== */
(function () {
  'use strict';
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  document.addEventListener('DOMContentLoaded', function () {
    initStatCounters();
    initScrollSpyNav();
  });

  // -- Statistics count-up ---------------------------------------------
  // Parses "500+", "10K+", "4.8", keeps the exact suffix, skips anything
  // that isn't a clean number (e.g. "24/7" stays static — animating that
  // would be meaningless). Runs once per element, plain IntersectionObserver.
  function initStatCounters() {
    var targets = document.querySelectorAll('.stat-item b, .stat b');
    if (!targets.length) return;

    var parsed = [];
    targets.forEach(function (el) {
      var raw = el.textContent.trim();
      var match = raw.match(/^([\d]+(?:\.\d+)?)(K)?(\+)?$/i);
      if (!match) return; // e.g. "24/7" — leave as-is, no count-up
      var value = parseFloat(match[1]);
      var isK = !!match[2];
      var suffix = (match[2] || '') + (match[3] || '');
      var decimals = match[1].includes('.') ? match[1].split('.')[1].length : 0;
      parsed.push({ el: el, target: value, suffix: suffix, decimals: decimals, isK: isK });
      el.textContent = (decimals ? (0).toFixed(decimals) : '0') + suffix;
    });
    if (!parsed.length) return;

    if (reduceMotion) {
      parsed.forEach(function (p) {
        p.el.textContent = (p.decimals ? p.target.toFixed(p.decimals) : p.target) + p.suffix;
      });
      return;
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var item = parsed.filter(function (p) { return p.el === entry.target; })[0];
        if (item && !item.done) {
          item.done = true;
          animateCount(item);
        }
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.4 });

    parsed.forEach(function (p) { observer.observe(p.el); });
  }

  function animateCount(item) {
    var duration = 1100;
    var start = null;
    function step(ts) {
      if (start === null) start = ts;
      var progress = Math.min((ts - start) / duration, 1);
      var eased = 1 - Math.pow(1 - progress, 3); // ease-out-cubic
      var current = item.target * eased;
      item.el.textContent = (item.decimals ? current.toFixed(item.decimals) : Math.round(current)) + item.suffix;
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  // -- Scroll-spy: highlight the matching nav link while its section is
  // in view. Reusable — only affects links that actually have a matching
  // in-page section id, so it's a no-op everywhere else. --------------
  function initScrollSpyNav() {
    var navLinks = document.querySelectorAll('.navbar-app .nav-link[href*="#"]');
    if (!navLinks.length) return;

    var map = [];
    navLinks.forEach(function (link) {
      var id = link.getAttribute('href').split('#')[1];
      var section = id && document.getElementById(id);
      if (section) map.push({ link: link, section: section });
    });
    if (!map.length) return;

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        var item = map.filter(function (m) { return m.section === entry.target; })[0];
        if (!item) return;
        if (entry.isIntersecting) {
          map.forEach(function (m) { m.link.classList.remove('active'); });
          item.link.classList.add('active');
        }
      });
    }, { rootMargin: '-45% 0px -45% 0px' });

    map.forEach(function (m) { observer.observe(m.section); });
  }
})();

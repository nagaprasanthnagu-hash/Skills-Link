/* ==========================================================================
   HERO-VIDEO.JS — checks whether a local hero video asset exists before
   ever touching the <video> element's src. If it's missing (no file has
   been added yet), the video stays hidden and the glass/glow illustration
   already in the hero markup is the fallback — no broken URL is ever set.
   Also drives the lightweight ambient particle field.
   ========================================================================== */
(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    initHeroVideo();
    initHeroParticles();
    initHeroSearchHandoff();
  });

  function initHeroVideo() {
    var video = document.querySelector('[data-hero-video]');
    if (!video) return;

    var candidates = ['/static/media/hero-loop.webm', '/static/media/hero-loop.mp4'];

    function tryNext(i) {
      if (i >= candidates.length) return; // no asset yet — illustration fallback stands
      fetch(candidates[i], { method: 'HEAD' }).then(function (res) {
        if (res.ok) {
          var source = document.createElement('source');
          source.src = candidates[i];
          video.appendChild(source);
          video.load();
          video.play().catch(function () {});
          video.classList.add('is-ready');
        } else {
          tryNext(i + 1);
        }
      }).catch(function () { tryNext(i + 1); });
    }
    tryNext(0);
  }

  function initHeroParticles() {
    var field = document.querySelector('[data-hero-particles]');
    if (!field || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    var count = window.innerWidth < 768 ? 14 : 28;
    for (var i = 0; i < count; i++) {
      var p = document.createElement('span');
      p.className = 'hero-particle';
      p.style.left = Math.random() * 100 + '%';
      p.style.bottom = (Math.random() * 40 - 10) + '%';
      p.style.animationDuration = (8 + Math.random() * 10) + 's';
      p.style.animationDelay = (Math.random() * 10) + 's';
      field.appendChild(p);
    }
  }

  // Hero quick-search hands its query to the Services page's existing
  // client-side filter (categories/list.html) via sessionStorage — no
  // server-side search param needed, so the URL/view stay untouched.
  function initHeroSearchHandoff() {
    var form = document.querySelector('[data-hero-search]');
    if (!form) return;
    form.addEventListener('submit', function () {
      var input = form.querySelector('input[name="q"]');
      if (input && input.value.trim()) {
        sessionStorage.setItem('servora_search_query', input.value.trim());
      }
    });
  }
})();

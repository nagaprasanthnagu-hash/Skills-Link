/* ==========================================================================
   GSAP-INIT.JS — premium motion layer (Sections 12.1-12.3).
   Progressive enhancement: if GSAP fails to load, app.js's vanilla
   IntersectionObserver reveal + the CSS keyframe float still run, so
   nothing is ever broken by this file being absent or failing.
   Fully gated by prefers-reduced-motion (12.3 / 15.4).
   ========================================================================== */
(function () {
  'use strict';
  if (!window.gsap) return;

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (window.gsap.registerPlugin && window.ScrollTrigger) {
    gsap.registerPlugin(ScrollTrigger);
  }

  document.addEventListener('DOMContentLoaded', function () {
    initHeroTimeline();
    initScrollStagger();
    initHeroBadgeFloat();
    initPageEntrance();
    initScrollTriggerSafetyNet();
  });

  // Safety net: ScrollTrigger-gated content must never stay permanently
  // invisible (a stuck opacity:0 is a broken page, not a design choice).
  // Force everything visible after a short grace period regardless of
  // whether it has scrolled into view yet, and again after full page load
  // (images/fonts can shift layout and throw off trigger positions).
  function initScrollTriggerSafetyNet() {
    var reveal = function () {
      document.querySelectorAll('.stagger, .stagger > *, .reveal-on-scroll').forEach(function (el) {
        if (parseFloat(getComputedStyle(el).opacity) < 1) {
          gsap.to(el, { opacity: 1, y: 0, duration: 0.3 });
        }
      });
      if (window.ScrollTrigger) ScrollTrigger.refresh();
    };
    window.addEventListener('load', function () { if (window.ScrollTrigger) ScrollTrigger.refresh(); });
    setTimeout(reveal, 2500);
  }

  // 12.2 Page/Section Transition — soft fade+rise on initial load
  function initPageEntrance() {
    var main = document.querySelector('[data-page-main]');
    if (!main) return;
    if (reduceMotion) { gsap.set(main, { opacity: 1, y: 0 }); return; }
    gsap.fromTo(main, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.4, ease: 'power2.out' });
  }

  // Hero entrance — headline/subtext/CTAs/badges stagger in (12.2 "Hero Load")
  function initHeroTimeline() {
    var hero = document.querySelector('[data-hero]');
    if (!hero) return;
    var targets = hero.querySelectorAll('[data-hero-in]');
    if (!targets.length) return;
    if (reduceMotion) { gsap.set(targets, { opacity: 1, y: 0, scale: 1 }); return; }

    gsap.timeline({ defaults: { ease: 'power3.out' } })
      .fromTo(targets, { opacity: 0, y: 22 }, { opacity: 1, y: 0, duration: 0.6, stagger: 0.09 });
  }

  // Hero floating badges — organic GSAP float, replaces the CSS keyframe
  // for this specific element set (12.2 "Floating idle" on hero icon badges)
  function initHeroBadgeFloat() {
    var badges = document.querySelectorAll('[data-float-badge]');
    if (!badges.length || reduceMotion) return;
    badges.forEach(function (el, i) {
      gsap.to(el, {
        y: '+=14',
        duration: 2.6 + (i % 3) * 0.4,
        ease: 'sine.inOut',
        repeat: -1,
        yoyo: true,
        delay: i * 0.2,
      });
    });
  }

  // Scroll-triggered stagger reveal for card grids (12.2 "Scroll Reveal")
  function initScrollStagger() {
    if (!window.ScrollTrigger) return;
    document.querySelectorAll('.stagger').forEach(function (group) {
      var items = group.children.length ? Array.prototype.slice.call(group.children) : [group];
      if (reduceMotion) { gsap.set(items, { opacity: 1, y: 0 }); return; }
      gsap.fromTo(items, { opacity: 0, y: 24 }, {
        opacity: 1, y: 0, duration: 0.5, stagger: 0.08, ease: 'power2.out',
        scrollTrigger: { trigger: group, start: 'top 88%' },
      });
    });

    document.querySelectorAll('.reveal-on-scroll').forEach(function (el) {
      if (reduceMotion) { gsap.set(el, { opacity: 1, y: 0 }); return; }
      gsap.fromTo(el, { opacity: 0, y: 20 }, {
        opacity: 1, y: 0, duration: 0.5, ease: 'power2.out',
        scrollTrigger: { trigger: el, start: 'top 90%' },
      });
    });
  }
})();

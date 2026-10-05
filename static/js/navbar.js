/* ==========================================================================
   NAVBAR.JS — navbar scroll-shadow state + mobile dashboard-menu toggle
   Hooks preserved: .navbar-app, [data-sidebar-toggle], .app-sidebar, .is-open
   ========================================================================== */
(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var navbar = document.querySelector('.navbar-app');
    if (navbar) {
      var onScroll = function () {
        navbar.classList.toggle('is-scrolled', window.scrollY > 8);
      };
      onScroll();
      window.addEventListener('scroll', onScroll, { passive: true });
    }

    var sidebarToggle = document.querySelector('[data-sidebar-toggle]');
    var sidebar = document.querySelector('.app-sidebar');
    if (sidebarToggle && sidebar) {
      function setOpen(open) {
        sidebar.classList.toggle('is-open', open);
        sidebarToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      }
      sidebarToggle.setAttribute('aria-expanded', 'false');
      sidebarToggle.addEventListener('click', function () {
        setOpen(!sidebar.classList.contains('is-open'));
      });
      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') setOpen(false);
      });
    }
  });
})();

/* ==========================================================================
   APP.JS — shared behaviours loaded on every page (vanilla JS + Bootstrap JS).
   Alerts auto-dismiss, tooltips, form-submit loading state, confirmation
   modal for [data-confirm], client-side validation hints, animated counters,
   scroll reveal (IntersectionObserver), password toggle, star rating, and the
   hero-search hand-off. Nothing here changes a form action, field, URL or
   request; it only adds presentation and confirmation UX.
   ========================================================================== */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  document.addEventListener('DOMContentLoaded', function () {
    initAutoDismissAlerts();
    initTooltips();
    initConfirmPrompts();      // registered before loading forms so it can veto a submit first
    initLoadingForms();
    initClientValidation();
    initAnimatedCounters();
    initScrollReveal();
    initPasswordToggles();
    initStarRatings();
    initHeroSearchHandoff();
  });

  // Back/forward cache restores the page as it was left; make sure no submit
  // button is stuck in its loading state.
  window.addEventListener('pageshow', function (e) {
    if (!e.persisted) return;
    document.querySelectorAll('.btn.is-loading').forEach(function (btn) {
      btn.disabled = false;
      btn.classList.remove('is-loading');
      btn.removeAttribute('aria-busy');
      var spin = btn.querySelector('.loading-spinner');
      if (spin) spin.remove();
    });
  });

  // -- Password visibility toggle --------------------------------------------
  function initPasswordToggles() {
    document.querySelectorAll('[data-password-toggle]').forEach(function (btn) {
      var wrapper = btn.closest('.password-field');
      var input = wrapper ? wrapper.querySelector('input') : null;
      if (!input) return;
      btn.addEventListener('click', function () {
        var showing = input.type === 'text';
        input.type = showing ? 'password' : 'text';
        btn.querySelector('i').className = showing ? 'bi bi-eye' : 'bi bi-eye-slash';
        btn.setAttribute('aria-label', showing ? 'Show password' : 'Hide password');
      });
    });
  }

  // -- Interactive star rating (wraps the existing radio inputs) ------------
  function initStarRatings() {
    document.querySelectorAll('[data-star-rating]').forEach(function (group) {
      var labels = [].slice.call(group.querySelectorAll('.star-rating-label'));
      var inputs = [].slice.call(group.querySelectorAll('input'));

      function paintTo(value) {
        labels.forEach(function (label) {
          var starValue = parseInt(label.getAttribute('data-star-value'), 10);
          label.classList.toggle('is-filled', starValue <= value);
        });
      }
      function checkedValue() {
        var checked = inputs.filter(function (i) { return i.checked; })[0];
        return checked ? parseInt(checked.value, 10) : 0;
      }

      paintTo(checkedValue());

      labels.forEach(function (label) {
        var starValue = parseInt(label.getAttribute('data-star-value'), 10);
        label.addEventListener('mouseenter', function () { paintTo(starValue); });
      });
      group.addEventListener('mouseleave', function () { paintTo(checkedValue()); });
      inputs.forEach(function (input) {
        input.addEventListener('change', function () { paintTo(checkedValue()); });
        input.addEventListener('focus', function () { paintTo(checkedValue()); });
      });
    });
  }

  function initAutoDismissAlerts() {
    document.querySelectorAll('.alert[data-auto-dismiss]').forEach(function (alertEl) {
      setTimeout(function () {
        if (!document.body.contains(alertEl)) return;
        bootstrap.Alert.getOrCreateInstance(alertEl).close();
      }, 6000);
    });
  }

  function initTooltips() {
    [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]')).forEach(function (el) {
      new bootstrap.Tooltip(el);
    });
  }

  // -- Submit-button loading state (opt-in: form[data-loading-form]) ---------
  // The button is disabled on the next tick, AFTER the browser has built the
  // form data, so a submit button's own name/value is never dropped.
  function initLoadingForms() {
    document.querySelectorAll('form[data-loading-form]').forEach(function (form) {
      form.addEventListener('submit', function (e) {
        if (e.defaultPrevented) return;                    // vetoed (e.g. awaiting confirmation)
        var btn = form.querySelector('button[type="submit"]');
        if (!btn || btn.disabled || !form.checkValidity()) return;
        var spinner = document.createElement('span');
        spinner.className = 'loading-spinner me-2';
        spinner.setAttribute('aria-hidden', 'true');
        btn.prepend(spinner);
        btn.classList.add('is-loading');
        btn.setAttribute('aria-busy', 'true');
        setTimeout(function () { btn.disabled = true; }, 0);
      });
    });
  }

  // -- Confirmation modal for [data-confirm] ---------------------------------
  // Replaces window.confirm with a Bootstrap modal. The original form/link is
  // left exactly as it is: on "Confirm" we re-submit the SAME form (same action,
  // method, CSRF token, submitter) or follow the SAME link. If Bootstrap's modal
  // isn't available, we fall back to the native confirm().
  var confirmModalEl = null;
  var confirmModal = null;
  var confirmPending = null;

  function buildConfirmModal() {
    if (confirmModalEl) return;
    confirmModalEl = document.createElement('div');
    confirmModalEl.className = 'modal fade';
    confirmModalEl.id = 'vvConfirmModal';
    confirmModalEl.tabIndex = -1;
    confirmModalEl.setAttribute('aria-labelledby', 'vvConfirmTitle');
    confirmModalEl.setAttribute('aria-hidden', 'true');
    confirmModalEl.innerHTML =
      '<div class="modal-dialog modal-dialog-centered"><div class="modal-content">' +
        '<div class="modal-body p-4">' +
          '<div class="d-flex gap-3">' +
            '<span class="modal-confirm-icon" data-vv-icon aria-hidden="true"><i class="bi bi-question-lg"></i></span>' +
            '<div><h2 class="modal-title mb-1" id="vvConfirmTitle">Please confirm</h2>' +
            '<p class="mb-0 text-muted-bookinghub" data-vv-message></p></div>' +
          '</div>' +
        '</div>' +
        '<div class="modal-footer border-0 pt-0">' +
          '<button type="button" class="btn btn-light" data-bs-dismiss="modal">Go back</button>' +
          '<button type="button" class="btn btn-primary" data-vv-confirm>Confirm</button>' +
        '</div>' +
      '</div></div>';
    document.body.appendChild(confirmModalEl);
    confirmModal = new bootstrap.Modal(confirmModalEl);

    confirmModalEl.querySelector('[data-vv-confirm]').addEventListener('click', function () {
      var action = confirmPending;
      confirmPending = null;
      confirmModal.hide();
      if (action) action();
    });
    confirmModalEl.addEventListener('hidden.bs.modal', function () { confirmPending = null; });
  }

  function askConfirm(message, onConfirm) {
    if (!window.bootstrap || !window.bootstrap.Modal) {
      if (window.confirm(message)) onConfirm();
      return;
    }
    buildConfirmModal();
    var destructive = /cancel|deactivate|delete|remove|reject/i.test(message);
    confirmModalEl.querySelector('[data-vv-message]').textContent = message;
    var btn = confirmModalEl.querySelector('[data-vv-confirm]');
    btn.className = 'btn ' + (destructive ? 'btn-danger' : 'btn-primary');
    btn.textContent = destructive ? 'Yes, continue' : 'Confirm';
    var icon = confirmModalEl.querySelector('[data-vv-icon]');
    icon.classList.toggle('is-danger', destructive);
    icon.innerHTML = '<i class="bi ' + (destructive ? 'bi-exclamation-triangle' : 'bi-question-lg') + '"></i>';
    confirmPending = onConfirm;
    confirmModal.show();
  }

  function initConfirmPrompts() {
    document.querySelectorAll('[data-confirm]').forEach(function (el) {
      var message = el.getAttribute('data-confirm');

      if (el.tagName === 'FORM') {
        var approved = false;
        el.addEventListener('submit', function (e) {
          if (approved) { approved = false; return; }       // second pass: let it through untouched
          e.preventDefault();
          var submitter = e.submitter || null;
          askConfirm(message, function () {
            approved = true;
            if (typeof el.requestSubmit === 'function') {
              submitter ? el.requestSubmit(submitter) : el.requestSubmit();
            } else {
              el.submit();
            }
          });
        });
        return;
      }

      // Links / buttons carrying data-confirm
      var approvedClick = false;
      el.addEventListener('click', function (e) {
        if (approvedClick) { approvedClick = false; return; }
        e.preventDefault();
        askConfirm(message, function () {
          approvedClick = true;
          el.click();
        });
      });
    });
  }

  // -- Bootstrap-style client-side validation hints (server stays authoritative)
  function initClientValidation() {
    var forms = document.getElementsByClassName('needs-validation');
    Array.prototype.filter.call(forms, function (form) {
      form.addEventListener('submit', function (event) {
        if (form.checkValidity() === false) {
          event.preventDefault();
          event.stopPropagation();
        }
        form.classList.add('was-validated');
      }, false);
    });
  }

  // -- Animated counters: <span data-counter="128">0</span> -------------------
  // requestAnimationFrame, one run per element, final value set immediately
  // when reduced motion is preferred or IntersectionObserver is unavailable.
  function formatCounter(el, target, value) {
    el.textContent = target % 1 !== 0 ? value.toFixed(1) : Math.round(value);
  }

  function initAnimatedCounters() {
    var counters = document.querySelectorAll('[data-counter]');
    if (!counters.length) return;

    if (reduceMotion || !('IntersectionObserver' in window)) {
      counters.forEach(function (el) {
        var t = parseFloat(el.getAttribute('data-counter'));
        if (!isNaN(t)) formatCounter(el, t, t);
      });
      return;
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        animateCounter(entry.target);
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.4 });

    counters.forEach(function (el) { observer.observe(el); });
  }

  function animateCounter(el) {
    var target = parseFloat(el.getAttribute('data-counter'));
    if (isNaN(target)) return;
    var duration = 900;
    var start = performance.now();

    function tick(now) {
      var progress = Math.min((now - start) / duration, 1);
      var eased = 1 - Math.pow(1 - progress, 3);
      formatCounter(el, target, target * eased);
      if (progress < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  // -- Scroll reveal ------------------------------------------------------------
  // Targets: every .reveal-on-scroll element and every direct child of .stagger.
  // JS adds .reveal-ready (hidden + shifted), .is-revealed when it scrolls into
  // view, then strips both classes so hover effects work normally afterwards.
  // Without JS / IntersectionObserver / with reduced motion nothing is hidden.
  function initScrollReveal() {
    if (reduceMotion || !('IntersectionObserver' in window)) return;

    var set = [].slice.call(document.querySelectorAll('.reveal-on-scroll, .stagger > *'));
    set = set.filter(function (el, i) { return set.indexOf(el) === i; });
    if (!set.length) return;

    function finish(el) {
      el.classList.add('is-revealed');
      setTimeout(function () {
        el.classList.remove('reveal-ready', 'is-revealed');
      }, 700);
    }

    set.forEach(function (el) { el.classList.add('reveal-ready'); });

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        finish(entry.target);
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.12 });

    set.forEach(function (el) { observer.observe(el); });

    // Safety net: content must never stay invisible.
    setTimeout(function () {
      set.forEach(function (el) {
        if (el.classList.contains('reveal-ready') && !el.classList.contains('is-revealed')) {
          observer.unobserve(el);
          finish(el);
        }
      });
    }, 4000);
  }

  // -- Hero quick-search hand-off ----------------------------------------------
  // Moved here from hero-video.js (unchanged logic and storage key) so the
  // homepage search still pre-fills the Services page quick filter after the
  // video script is retired. Safe if both scripts are present: it only stores
  // the same value twice.
  function initHeroSearchHandoff() {
    var form = document.querySelector('[data-hero-search]');
    if (!form) return;
    form.addEventListener('submit', function () {
      var input = form.querySelector('input[name="q"]');
      if (!input) return;
      try {
        if (input.value.trim()) {
          sessionStorage.setItem('servora_search_query', input.value.trim());
        }
      } catch (err) { /* storage unavailable — search still works server-side */ }
    });
  }
})();

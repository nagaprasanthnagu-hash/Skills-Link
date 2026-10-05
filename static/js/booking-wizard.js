/* ==========================================================================
   BOOKING-WIZARD.JS — turns the single existing BookingForm into a 4-step
   guided flow (Service → Details → Schedule → Confirm), per Section 16.3.
   The form still has one action/method and posts once, on the final step —
   the Django view, URL, and form fields are completely unchanged.
   ========================================================================== */
(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var form = document.querySelector('[data-booking-wizard]');
    if (!form) return;

    var steps = [].slice.call(form.querySelectorAll('[data-wizard-step]'));
    var dots = [].slice.call(document.querySelectorAll('[data-step-dot]'));
    var nextBtn = form.querySelector('[data-wizard-next]');
    var backBtn = form.querySelector('[data-wizard-back]');
    var submitBtn = form.querySelector('[data-wizard-submit]');
    var current = 1;

    function fieldsFor(step) {
      var el = form.querySelector('[data-wizard-step="' + step + '"]');
      return el ? [].slice.call(el.querySelectorAll('input, select, textarea')) : [];
    }

    function validateStep(step) {
      var valid = true;
      fieldsFor(step).forEach(function (field) {
        if (!field.checkValidity()) {
          field.reportValidity();
          valid = false;
        }
      });
      return valid;
    }

    function updateConfirmSummary() {
      var categorySelect = form.querySelector('#id_category');
      var addressField = form.querySelector('#id_address');
      var datetimeField = form.querySelector('#id_preferred_datetime');
      var descriptionField = form.querySelector('#id_description');

      var categoryText = categorySelect && categorySelect.selectedIndex >= 0
        ? categorySelect.options[categorySelect.selectedIndex].text : '—';

      setText('[data-confirm-category]', categoryText);
      setText('[data-confirm-address]', addressField && addressField.value ? addressField.value : '—');
      setText('[data-confirm-datetime]', datetimeField && datetimeField.value ? formatDateTime(datetimeField.value) : '—');
      setText('[data-confirm-description]', descriptionField && descriptionField.value ? descriptionField.value : '—');
    }

    function setText(selector, value) {
      var el = form.querySelector(selector);
      if (el) el.textContent = value;
    }

    function formatDateTime(value) {
      var date = new Date(value);
      if (isNaN(date.getTime())) return value;
      return date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
    }

    function goTo(step) {
      steps.forEach(function (el) {
        el.classList.toggle('is-active', parseInt(el.getAttribute('data-wizard-step'), 10) === step);
      });
      dots.forEach(function (dot) {
        var dotStep = parseInt(dot.getAttribute('data-step-dot'), 10);
        dot.classList.toggle('is-active', dotStep === step);
        dot.classList.toggle('is-complete', dotStep < step);
      });

      backBtn.style.visibility = step === 1 ? 'hidden' : 'visible';
      var isLast = step === steps.length;
      nextBtn.classList.toggle('d-none', isLast);
      submitBtn.classList.toggle('d-none', !isLast);
      if (isLast) updateConfirmSummary();

      current = step;
    }

    nextBtn.addEventListener('click', function () {
      if (!validateStep(current)) return;
      if (current < steps.length) goTo(current + 1);
    });

    backBtn.addEventListener('click', function () {
      if (current > 1) goTo(current - 1);
    });

    goTo(1);
  });
})();

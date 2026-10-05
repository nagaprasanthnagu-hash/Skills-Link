/* ==========================================================================
   BOOKING.JS — lightweight status refresh on the booking detail page
   (unchanged behaviour from the previous booking-status.js, renamed to
   match the new static/js/ file map).
   ========================================================================== */
(function () {
  'use strict';

  function refreshBookingStatus(bookingId, badgeEl) {
    fetch('/bookings/' + bookingId + '/', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (response) {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.text();
      })
      .then(function (html) {
        var parser = new DOMParser();
        var doc = parser.parseFromString(html, 'text/html');
        var freshBadge = doc.querySelector('[data-booking-status-badge]');
        if (freshBadge && badgeEl) {
          badgeEl.innerHTML = freshBadge.innerHTML;
        }
      })
      .catch(function () {
        // Silently ignore — the page reflects the latest status on next load.
      });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var badge = document.querySelector('[data-booking-status-badge]');
    if (!badge) return;
    var bookingId = badge.getAttribute('data-booking-id');
    if (!bookingId) return;
    setInterval(function () {
      refreshBookingStatus(bookingId, badge);
    }, 20000);
  });
})();

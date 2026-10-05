/* ==========================================================================
   TOAST.JS — lightweight toast stack with a small JS API (window.showToast).
   Django messages are rendered as inline alerts by components/alerts.html;
   this is available for any page that wants a transient notice.
   ========================================================================== */
(function () {
  'use strict';

  function ensureStack() {
    var stack = document.querySelector('.toast-stack');
    if (!stack) {
      stack = document.createElement('div');
      stack.className = 'toast-stack';
      stack.setAttribute('aria-live', 'polite');
      document.body.appendChild(stack);
    }
    return stack;
  }

  window.showToast = function (message, level) {
    level = level || 'info';
    var stack = ensureStack();
    var toast = document.createElement('div');
    toast.className = 'toast-app ' + level;
    toast.setAttribute('role', level === 'danger' ? 'alert' : 'status');
    toast.textContent = message;
    stack.appendChild(toast);
    setTimeout(function () {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 200ms ease-out';
      setTimeout(function () { toast.remove(); }, 200);
    }, 5000);
  };
})();

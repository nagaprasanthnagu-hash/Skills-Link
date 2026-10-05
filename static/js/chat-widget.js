/* ==========================================================================
   CHAT-WIDGET.JS — AI Chat Assistant front-end shell (Section 16.10).
   Renders from a static mock JSON fixture (static/data/chat-fixture.json).
   No backend/AI integration — purely a presentational placeholder.
   ========================================================================== */
(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var widget = document.querySelector('[data-chat-widget]');
    if (!widget) return;

    var launcher = widget.querySelector('[data-chat-launcher]');
    var panel = widget.querySelector('[data-chat-panel]');
    var closeBtn = widget.querySelector('[data-chat-close]');
    var thread = widget.querySelector('[data-chat-thread]');
    var quickReplies = widget.querySelector('[data-chat-quick-replies]');
    var form = widget.querySelector('[data-chat-input-form]');
    var input = widget.querySelector('[data-chat-input]');
    var sendBtn = widget.querySelector('[data-chat-send]');
    var unreadBadge = widget.querySelector('[data-chat-unread-badge]');
    var browseUrl = widget.getAttribute('data-browse-url');

    var fixtureUrl = widget.getAttribute('data-fixture-url');
    var fixture = null;
    var opened = false;

    function fetchFixture() {
      if (!fixtureUrl) return Promise.resolve(null);
      return fetch(fixtureUrl).then(function (res) { return res.ok ? res.json() : null; }).catch(function () { return null; });
    }

    function openPanel() {
      panel.hidden = false;
      launcher.setAttribute('aria-expanded', 'true');
      if (unreadBadge) unreadBadge.classList.add('d-none');
      if (!opened) {
        opened = true;
        (fixture ? Promise.resolve(fixture) : fetchFixture()).then(function (data) {
          fixture = data;
          renderGreeting();
        });
      }
      input.focus();
    }

    function closePanel() {
      panel.hidden = true;
      launcher.setAttribute('aria-expanded', 'false');
    }

    launcher.addEventListener('click', function () {
      panel.hidden ? openPanel() : closePanel();
    });
    closeBtn.addEventListener('click', closePanel);

    function scrollToBottom() {
      thread.scrollTop = thread.scrollHeight;
    }

    function addBubble(text, sender) {
      var bubble = document.createElement('div');
      bubble.className = 'chat-bubble chat-bubble-' + sender;
      bubble.textContent = text;
      thread.appendChild(bubble);
      scrollToBottom();
    }

    function addProviderCard(card) {
      var el = document.createElement('div');
      el.className = 'chat-provider-card';
      var initials = card.name.split(' ').map(function (w) { return w[0]; }).slice(0, 2).join('').toUpperCase();
      el.innerHTML =
        '<div class="chat-provider-card-header">' +
          '<span class="chat-provider-card-avatar">' + initials + '</span>' +
          '<div>' +
            '<div class="chat-provider-card-name">' + card.name + '</div>' +
            '<div class="chat-provider-card-meta"><i class="bi bi-star-fill" style="color:var(--color-warning)"></i> ' + card.rating + ' · ' + card.availability + '</div>' +
          '</div>' +
        '</div>' +
        '<a href="' + (browseUrl || '#') + '" class="btn btn-primary btn-sm w-100">Book Now</a>';
      thread.appendChild(el);
      scrollToBottom();
    }

    function addAction(label, url) {
      var el = document.createElement('a');
      el.href = url || browseUrl || '#';
      el.className = 'btn btn-outline-primary btn-sm align-self-start';
      el.textContent = label;
      thread.appendChild(el);
      scrollToBottom();
    }

    function showTyping() {
      var el = document.createElement('div');
      el.className = 'chat-typing';
      el.setAttribute('data-chat-typing', '');
      el.innerHTML = '<span></span><span></span><span></span>';
      thread.appendChild(el);
      scrollToBottom();
      return el;
    }

    function renderQuickReplies(options) {
      quickReplies.innerHTML = '';
      (options || []).forEach(function (label) {
        var chip = document.createElement('button');
        chip.type = 'button';
        chip.className = 'chat-quick-reply-chip';
        chip.textContent = label;
        chip.addEventListener('click', function () { handleUserMessage(label); });
        quickReplies.appendChild(chip);
      });
    }

    function renderGreeting() {
      if (!fixture) {
        addBubble('Hi! I\u2019m the SkillLink Assistant. (Demo mode \u2014 mock data unavailable.)', 'assistant');
        return;
      }
      addBubble(fixture.greeting, 'assistant');
      renderQuickReplies(fixture.quickReplies);
    }

    function respondTo(userText) {
      var typingEl = showTyping();
      var key = userText.trim().toLowerCase();
      setTimeout(function () {
        typingEl.remove();
        if (!fixture) {
          addBubble('Thanks! (Demo mode \u2014 mock data unavailable.)', 'assistant');
          return;
        }
        var match = fixture.responses && fixture.responses[key];
        if (match) {
          addBubble(match.text, 'assistant');
          if (match.providerCard) addProviderCard(match.providerCard);
          if (match.actionLabel) addAction(match.actionLabel, browseUrl);
        } else {
          addBubble(fixture.fallback, 'assistant');
        }
        renderQuickReplies(fixture.quickReplies);
      }, 700);
    }

    function handleUserMessage(text) {
      if (!text) return;
      addBubble(text, 'user');
      quickReplies.innerHTML = '';
      respondTo(text);
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var value = input.value;
      input.value = '';
      handleUserMessage(value);
    });
  });
})();

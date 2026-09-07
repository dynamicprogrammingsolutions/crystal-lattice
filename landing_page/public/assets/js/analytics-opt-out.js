(function (window, document) {
  'use strict';

  function doNotTrackEnabled() {
    return window.navigator.doNotTrack === '1' ||
      window.doNotTrack === '1' ||
      window.navigator.msDoNotTrack === '1';
  }

  function setup() {
    var root = document.querySelector('[data-analytics-opt-out]');
    if (!root || root.dataset.ready === 'true') return;

    var button = root.querySelector('button');
    var status = root.querySelector('[data-analytics-status]');
    if (!button || !status) return;
    root.dataset.ready = 'true';

    function isDisabled() {
      try {
        return window.localStorage.getItem('umami.disabled') === '1';
      } catch (_error) {
        return false;
      }
    }

    function render(message) {
      var dnt = doNotTrackEnabled();
      var disabled = isDisabled();
      status.textContent = message || (dnt
        ? 'Analytics is disabled because your browser sends Do Not Track.'
        : disabled
          ? 'Analytics is disabled in this browser.'
          : 'Analytics is enabled in this browser.');
      button.textContent = disabled ? 'Enable analytics' : 'Disable analytics';
      button.setAttribute('aria-pressed', disabled ? 'true' : 'false');
      button.disabled = dnt;
    }

    button.addEventListener('click', function () {
      try {
        if (isDisabled()) {
          window.localStorage.removeItem('umami.disabled');
          render('Analytics will be enabled from your next page load.');
        } else {
          window.localStorage.setItem('umami.disabled', '1');
          render('Analytics is now disabled in this browser.');
        }
      } catch (_error) {
        render('Your browser prevented this preference from being saved.');
      }
    });

    render();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setup);
  } else {
    setup();
  }
  document.addEventListener('astro:after-swap', setup);
})(window, document);

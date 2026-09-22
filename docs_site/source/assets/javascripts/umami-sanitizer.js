(function (window, document) {
  'use strict';

  var MAX_PATH_LENGTH = 500;
  var MAX_TITLE_LENGTH = 200;
  var UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

  function tracker() {
    return document.querySelector(
      'script[data-before-send="crystalLatticeUmamiBeforeSend"]'
    );
  }

  function trackerConfiguration() {
    var element = tracker();
    var domains = element ? element.getAttribute('data-domains') || '' : '';
    var website = element ? element.getAttribute('data-website-id') || '' : '';

    return {
      domains: domains
        .split(',')
        .map(function (domain) { return domain.trim().toLowerCase(); })
        .filter(Boolean),
      website: UUID_PATTERN.test(website) ? website : ''
    };
  }

  function analyticsDisabled() {
    try {
      return window.localStorage.getItem('umami.disabled') === '1';
    } catch (_error) {
      return false;
    }
  }

  function sanitizePageUrl(rawUrl, allowedDomains) {
    if (typeof rawUrl !== 'string' || rawUrl.length > 2048) return null;

    var parsed;
    try {
      parsed = new URL(rawUrl, window.location.origin);
    } catch (_error) {
      return null;
    }

    if (
      !allowedDomains.includes(parsed.hostname.toLowerCase()) ||
      parsed.pathname.length > MAX_PATH_LENGTH
    ) return null;

    parsed.username = '';
    parsed.password = '';
    parsed.search = '';
    parsed.hash = '';
    return parsed.toString();
  }

  function sanitizeReferrer(rawUrl) {
    if (typeof rawUrl !== 'string' || rawUrl.length > 2048) return null;

    var parsed;
    try {
      parsed = new URL(rawUrl);
    } catch (_error) {
      return null;
    }

    if (
      (parsed.protocol !== 'https:' && parsed.protocol !== 'http:') ||
      !parsed.hostname ||
      parsed.hostname.length > 253 ||
      parsed.pathname.length > MAX_PATH_LENGTH
    ) return null;

    parsed.username = '';
    parsed.password = '';
    parsed.search = '';
    parsed.hash = '';
    return parsed.toString();
  }

  window.crystalLatticeUmamiBeforeSend = function (type, payload) {
    if (
      analyticsDisabled() ||
      (type !== 'event' && type !== 'performance') ||
      !payload ||
      typeof payload !== 'object'
    ) return null;

    if (type === 'event' && (payload.name !== undefined || payload.data !== undefined)) {
      return null;
    }

    if (payload.id !== undefined || payload.tag !== undefined) return null;

    var configuration = trackerConfiguration();
    var hostname = typeof payload.hostname === 'string'
      ? payload.hostname.toLowerCase()
      : '';

    if (
      !configuration.website ||
      payload.website !== configuration.website ||
      configuration.domains.length !== 1 ||
      !configuration.domains.includes(hostname)
    ) return null;

    var url = sanitizePageUrl(payload.url, configuration.domains);
    if (!url) return null;

    var sanitized = {
      website: configuration.website,
      hostname: hostname,
      url: url
    };

    if (typeof payload.screen === 'string' && /^\d{2,5}x\d{2,5}$/.test(payload.screen)) {
      sanitized.screen = payload.screen;
    }
    if (typeof payload.language === 'string' && payload.language.length <= 35) {
      sanitized.language = payload.language;
    }
    if (typeof payload.title === 'string') {
      sanitized.title = payload.title.slice(0, MAX_TITLE_LENGTH);
    }
    if (payload.referrer) {
      var referrer = sanitizeReferrer(payload.referrer);
      if (referrer) sanitized.referrer = referrer;
    }

    if (type === 'performance') {
      ['lcp', 'inp', 'cls', 'fcp', 'ttfb', 'duration'].forEach(function (metric) {
        var value = payload[metric];
        if (typeof value === 'number' && Number.isFinite(value) && value >= 0) {
          sanitized[metric] = value;
        }
      });
    }

    return sanitized;
  };
})(window, document);

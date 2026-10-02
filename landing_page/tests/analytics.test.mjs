import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';
import test from 'node:test';

const landingPath = new URL('../public/assets/js/umami-sanitizer.js', import.meta.url);
const docsPath = new URL('../../docs_site/source/assets/javascripts/umami-sanitizer.js', import.meta.url);
const website = '123e4567-e89b-42d3-a456-426614174000';

async function loadSanitizer({ disabled = false } = {}) {
  const source = await readFile(landingPath, 'utf8');
  const storage = new Map(disabled ? [['umami.disabled', '1']] : []);
  const tracker = {
    getAttribute(name) {
      if (name === 'data-domains') return 'crystallattice.dev';
      if (name === 'data-website-id') return website;
      return null;
    },
  };
  const window = {
    location: { origin: 'https://crystallattice.dev' },
    localStorage: {
      getItem(key) { return storage.get(key) ?? null; },
    },
  };
  const document = {
    querySelector(selector) {
      assert.equal(selector, 'script[data-before-send="crystalLatticeUmamiBeforeSend"]');
      return tracker;
    },
  };
  vm.runInNewContext(source, { window, document, URL, Number });
  return window.crystalLatticeUmamiBeforeSend;
}

test('landing and docs use the identical sanitizer source', async () => {
  assert.equal(await readFile(landingPath, 'utf8'), await readFile(docsPath, 'utf8'));
});

test('page views remove query, fragment, referrer credentials and query', async () => {
  const sanitize = await loadSanitizer();
  const output = sanitize('event', {
    website,
    hostname: 'crystallattice.dev',
    url: 'https://crystallattice.dev/mobile?gclid=secret&utm_source=test#private',
    referrer: 'https://name:password@example.com/path?email=a@example.com#token',
    title: 'Mobile',
    language: 'en-US',
    screen: '1440x900',
  });

  assert.deepEqual(JSON.parse(JSON.stringify(output)), {
    website,
    hostname: 'crystallattice.dev',
    url: 'https://crystallattice.dev/mobile',
    referrer: 'https://example.com/path',
    title: 'Mobile',
    language: 'en-US',
    screen: '1440x900',
  });
});

test('custom events, wrong domains, wrong website IDs and opt-out are rejected', async () => {
  const sanitize = await loadSanitizer();
  const base = { website, hostname: 'crystallattice.dev', url: '/' };
  assert.equal(sanitize('event', { ...base, name: 'signup' }), null);
  assert.equal(sanitize('event', { ...base, hostname: 'preview.example' }), null);
  assert.equal(sanitize('event', { ...base, website: '223e4567-e89b-42d3-a456-426614174000' }), null);
  const disabled = await loadSanitizer({ disabled: true });
  assert.equal(disabled('event', base), null);
});

test('performance keeps only finite non-negative supported metrics', async () => {
  const sanitize = await loadSanitizer();
  const output = sanitize('performance', {
    website,
    hostname: 'crystallattice.dev',
    url: '/',
    lcp: 1234,
    inp: -1,
    cls: 0.05,
    fcp: Number.POSITIVE_INFINITY,
    ttfb: 120,
    duration: 1500,
    data: { private: true },
  });
  assert.deepEqual(JSON.parse(JSON.stringify(output)), {
    website,
    hostname: 'crystallattice.dev',
    url: 'https://crystallattice.dev/',
    lcp: 1234,
    cls: 0.05,
    ttfb: 120,
    duration: 1500,
  });
});

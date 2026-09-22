import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { load } from 'js-yaml';

const homePath = new URL('../src/content/pages/home.yaml', import.meta.url);
const installer =
  'curl -fsSL https://download.crystallattice.dev/crystal-lattice-cli/install.sh | bash';

async function loadHome() {
  return load(await readFile(homePath, 'utf8'));
}

test('homepage identifies the project as open source', async () => {
  const home = await loadHome();
  const hero = home.sections.find((section) => section.type === 'hero');

  assert.ok(hero);
  assert.equal(hero.badge, 'Open Source');
});

test('homepage advertises only the supported bundled installer', async () => {
  const home = await loadHome();
  const hero = home.sections.find((section) => section.type === 'hero');

  assert.ok(hero);
  assert.equal(hero.install.command, installer);
  assert.equal(hero.install.altHtml, undefined);
  assert.doesNotMatch(JSON.stringify(home), /pipx install crystal-lattice-cli/i);
});
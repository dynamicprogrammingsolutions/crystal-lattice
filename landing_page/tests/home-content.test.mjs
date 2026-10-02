import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { load } from 'js-yaml';

const homePath = new URL('../src/content/pages/home.yaml', import.meta.url);
const shellInstaller =
  'curl -fsSL https://download.crystallattice.dev/crystal-lattice-cli/install.sh | bash';
const powershellInstaller =
  'irm https://download.crystallattice.dev/crystal-lattice-cli/install.ps1 | iex';
const installationDocs =
  '$docsUrl/packages/application-python/installation/';

async function loadHome() {
  return load(await readFile(homePath, 'utf8'));
}

test('homepage identifies the project as open source', async () => {
  const home = await loadHome();
  const hero = home.sections.find((section) => section.type === 'hero');

  assert.ok(hero);
  assert.equal(hero.badge, 'Open Source');
});

test('homepage owns the supported installation methods in one chooser', async () => {
  const home = await loadHome();
  const hero = home.sections.find((section) => section.type === 'hero');

  assert.ok(hero);
  assert.equal(hero.install.ariaLabel, 'Install Crystal Lattice');
  assert.equal(hero.install.defaultMethod, 'macos-linux');
  assert.deepEqual(
    hero.install.methods.map(({ id, tabLabel, kind }) => ({
      id,
      tabLabel,
      kind,
    })),
    [
      { id: 'macos-linux', tabLabel: 'macOS/Linux', kind: 'command' },
      { id: 'windows', tabLabel: 'Windows', kind: 'command' },
      { id: 'manual', tabLabel: 'Manual', kind: 'manual' },
    ],
  );

  const macosLinux = hero.install.methods[0];
  assert.equal(macosLinux.panelLabel, 'Terminal');
  assert.equal(macosLinux.prompt, '$');
  assert.equal(macosLinux.command, shellInstaller);
  assert.equal(
    macosLinux.support,
    'macOS Intel or Apple silicon · Linux x64 or ARM64',
  );
  assert.equal(macosLinux.documentation.href, installationDocs);

  const windows = hero.install.methods[1];
  assert.equal(windows.panelLabel, 'Windows PowerShell');
  assert.equal(windows.prompt, 'PS>');
  assert.equal(windows.command, powershellInstaller);
  assert.equal(
    windows.support,
    'Windows x64 or ARM64 · No admin rights, Python, Git Bash, or WSL needed',
  );
  assert.equal(windows.documentation.href, installationDocs);

  const manual = hero.install.methods[2];
  assert.deepEqual(manual.platforms, [
    'macOS Intel',
    'macOS Apple silicon',
    'Linux x64',
    'Linux ARM64',
    'Windows x64',
    'Windows ARM64',
  ]);
  assert.equal(
    manual.download.href,
    'https://github.com/dynamicprogrammingsolutions/crystal-lattice/releases/latest',
  );
  assert.equal(manual.download.target, '_blank');
  assert.equal(manual.documentation.href, installationDocs);

  const contentOutsideHero = JSON.stringify(
    home.sections.filter((section) => section !== hero),
  );
  assert.doesNotMatch(contentOutsideHero, /crystal-lattice-cli\/install\.(?:sh|ps1)/);
  assert.doesNotMatch(JSON.stringify(home), /pipx install crystal-lattice-cli/i);
});

test('first-success guide links to the chooser instead of repeating installation', async () => {
  const home = await loadHome();
  const guide = home.sections.find(
    (section) =>
      section.type === 'actionGuide' && section.id === 'computer-to-phone',
  );

  assert.ok(guide);
  const installStep = guide.action.steps[0];
  assert.equal(installStep.label, 'Install the CLI');
  assert.equal(installStep.link.href, '#install');
  assert.equal(installStep.link.label, 'Choose an installation method');
  assert.equal(installStep.code.trim(), '$ crystal-lattice --help');
  assert.doesNotMatch(JSON.stringify(installStep), /install\.(?:sh|ps1)/);
});
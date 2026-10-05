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
  const highlights = home.sections.find(
    (section) => section.id === 'product-highlights',
  );

  assert.ok(hero);
  assert.ok(highlights);
  assert.equal(hero.badge, 'Open Source');
  assert.match(
    highlights.items.find(({ id }) => id === 'feature-transparency').description,
    /Framework and plugin boundaries make .* visible and user-modifiable/,
  );
  assert.match(
    highlights.items.find(({ id }) => id === 'feature-transparency').description,
    /Open source adds full source-level transparency/,
  );
});

test('homepage starts with hero, draft highlights, and getting started', async () => {
  const home = await loadHome();
  const primarySections = home.sections.slice(0, 3);

  assert.deepEqual(
    primarySections.map(({ type, id }) => ({ type, id })),
    [
      { type: 'hero', id: 'hero' },
      { type: 'featureShowcase', id: 'product-highlights' },
      { type: 'gettingStarted', id: 'getting-started' },
    ],
  );

  const hero = primarySections[0];
  assert.equal(hero.install, undefined);
  assert.equal(hero.actions[0].label, 'Get started');
  assert.equal(hero.actions[0].href, '#getting-started');
  assert.equal(
    home.sections.some((section) => section.id === 'computer-to-phone'),
    false,
  );
});

test('homepage defines four compact user features followed by two configurable deep dives', async () => {
  const home = await loadHome();
  const highlights = home.sections.find(
    (section) => section.id === 'product-highlights',
  );

  assert.ok(highlights);
  assert.equal(highlights.layout, 'two-column');
  assert.equal(highlights.presentation, 'editorial');
  assert.match(highlights.reviewStatus, /Structural prototype/);
  assert.deepEqual(
    highlights.items.map(({ title }) => title),
    [
      'One workspace for every model family.',
      'Work from anywhere.',
      'Vibe code—or vibe anything.',
      'Sessions become workspaces.',
      'Replace the parts you disagree with.',
      'Transparency by design.',
    ],
  );
  assert.equal(highlights.items.length, 6);
  for (const item of highlights.items) {
    assert.match(item.reviewStatus, /Draft/);
    assert.ok(item.media.assets?.length || item.media.desktop);
    assert.equal(item.link, undefined);
  }
  assert.deepEqual(
    highlights.items.map(({ layout }) => layout ?? 'compact'),
    ['compact', 'compact', 'compact', 'compact', 'full-width', 'full-width'],
  );
  assert.match(highlights.items[0].media.assets[0].alt, /Codex selected/);
  assert.match(highlights.items[0].media.assets[1].alt, /Claude selected/);
  assert.match(highlights.items[3].description, /plugin-driven/);
  assert.equal(highlights.items[3].id, 'session-workbench');
});

test('detailed evidence stays inside its owning highlight without duplicate galleries', async () => {
  const home = await loadHome();
  const highlights = home.sections.find(({ id }) => id === 'product-highlights');
  assert.deepEqual(
    highlights.items.map(({ media }) => media.assets?.length ?? 1),
    [2, 1, 1, 2, 3, 3],
  );
  assert.deepEqual(
    highlights.items[4].media.assets.map(({ label }) => label),
    ['Session actions', 'Actions for each message', 'A session list that fits your work'],
  );
  assert.deepEqual(
    highlights.items[5].media.assets.map(({ label }) => label),
    ['Inspect the instructions', 'See where costs go', 'Track ChatGPT usage'],
  );
  assert.equal(
    home.sections.some(({ id }) =>
      ['session-workbench', 'transparency-details', 'plugin-action-examples'].includes(id),
    ),
    false,
  );
  assert.doesNotMatch(
    JSON.stringify(home),
    /See what goes into each session|Your plugins shape the controls|Inspect and restore session snapshots/,
  );
});

test('getting started owns the supported installation methods in one chooser', async () => {
  const home = await loadHome();
  const gettingStarted = home.sections.find(
    (section) => section.type === 'gettingStarted',
  );
  const installStep = gettingStarted.steps[0];

  assert.ok(gettingStarted);
  assert.equal(installStep.kind, 'install');
  assert.equal(installStep.install.ariaLabel, 'Install Crystal Lattice');
  assert.equal(installStep.install.defaultMethod, 'macos-linux');
  assert.deepEqual(
    installStep.install.methods.map(({ id, tabLabel, kind }) => ({
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

  const macosLinux = installStep.install.methods[0];
  assert.equal(macosLinux.panelLabel, 'Terminal');
  assert.equal(macosLinux.prompt, '$');
  assert.equal(macosLinux.command, shellInstaller);
  assert.equal(
    macosLinux.support,
    'macOS Intel or Apple silicon · Linux x64 or ARM64',
  );
  assert.equal(macosLinux.documentation.href, installationDocs);

  const windows = installStep.install.methods[1];
  assert.equal(windows.panelLabel, 'Windows PowerShell');
  assert.equal(windows.prompt, 'PS>');
  assert.equal(windows.command, powershellInstaller);
  assert.equal(
    windows.support,
    'Windows x64 or ARM64 · No admin rights, Python, Git Bash, or WSL needed',
  );
  assert.equal(windows.documentation.href, installationDocs);

  const manual = installStep.install.methods[2];
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

  const contentOutsideInstallStep = JSON.stringify(
    home.sections.flatMap((section) =>
      section === gettingStarted
        ? [{ ...section, steps: section.steps.slice(1) }]
        : [section],
    ),
  );
  assert.doesNotMatch(
    contentOutsideInstallStep,
    /crystal-lattice-cli\/install\.(?:sh|ps1)/,
  );
  assert.doesNotMatch(JSON.stringify(home), /pipx install crystal-lattice-cli/i);
});

test('getting started defines the six approved structural steps', async () => {
  const home = await loadHome();
  const gettingStarted = home.sections.find(
    (section) => section.type === 'gettingStarted',
  );

  assert.ok(gettingStarted);
  assert.deepEqual(
    gettingStarted.steps.map(({ id, kind }) => ({ id, kind })),
    [
      { id: 'install-cli', kind: 'install' },
      { id: 'start-workspace', kind: 'command' },
      { id: 'download-desktop', kind: 'desktop-download' },
      { id: 'connect-desktop', kind: 'desktop-connect' },
      { id: 'get-mobile', kind: 'mobile-download' },
      { id: 'connect-mobile', kind: 'mobile-connect' },
    ],
  );

  const desktop = gettingStarted.steps[2];
  assert.deepEqual(
    desktop.platforms.map(({ id, status }) => ({ id, status })),
    [
      { id: 'macos', status: 'available' },
      { id: 'windows', status: 'coming-soon' },
      { id: 'linux', status: 'coming-soon' },
    ],
  );

  const desktopConnection = gettingStarted.steps[3];
  assert.equal(desktopConnection.methods.length, 1);
  assert.equal(desktopConnection.methods[0].title, 'Enter the port');
  assert.match(desktopConnection.methods[0].description, /127\.0\.0\.1/);
  assert.equal(desktopConnection.methods[0].code, '9000');

  const mobile = gettingStarted.steps[4];
  assert.deepEqual(
    mobile.platforms.map(({ id, status }) => ({ id, status })),
    [
      { id: 'ios', status: 'coming-soon' },
      { id: 'android', status: 'coming-soon' },
    ],
  );
  assert.equal(mobile.waitlist.status, 'disabled-prototype');
  assert.doesNotMatch(JSON.stringify(mobile), /type=["']?email/i);
});
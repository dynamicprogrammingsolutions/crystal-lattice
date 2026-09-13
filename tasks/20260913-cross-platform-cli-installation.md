# Cross-Platform CLI Installation and Website Choices

Deliver first-class bundled CLI installation for every supported desktop
architecture, including native Windows PowerShell, and present the real
installation choices clearly on the product website and in package-owned user
documentation.

## Requirements checklist

- [ ] Released bundled-Python archives support and are natively verified on
      macOS AMD64, macOS ARM64, Linux AMD64, Linux ARM64, Windows AMD64, and
      Windows ARM64.
- [ ] The shell installer supports macOS and Linux on both released
      architectures and preserves the existing Git Bash/MSYS2/Cygwin path on
      Windows AMD64; Windows ARM64 shell support is included when the native
      runner's Bash environment can exercise it honestly.
- [ ] A native PowerShell installer supports Windows AMD64 and Windows ARM64
      without requiring Git Bash, WSL, Python, administrator privileges, or
      exported environment variables.
- [ ] A normal native Windows installation makes `crystal-lattice` resolvable
      by name from PowerShell and `cmd.exe`; invoking the PowerShell installer
      updates its current PowerShell session when it adds a command directory,
      while newly opened native terminals observe the persisted user setting.
- [ ] Users can manually download the correct archive for every released
      target and follow documented extraction, direct-launch, and optional
      command-installation instructions.
- [ ] Bash installation, PowerShell installation, and direct archive use are
      separate user-path acceptance scenarios. They may share low-level
      helpers and immutable archives but not mutable home, config, plugin,
      download, installation, or command-directory state.
- [ ] Every installed or directly extracted acceptance scenario starts the
      credential-free default configuration and independently exercises
      installation of the designated non-preinstalled plugin where that is
      part of the corresponding existing distribution contract.
- [ ] Root npm commands expose the direct developer acceptance paths, and
      native release Actions invoke those commands or their one direct
      scenario owner rather than maintaining alternate CI-only behavior.
- [ ] Release publication includes both installers and all six archives, and
      bounded post-publication checks verify the public installer/version
      endpoints after CDN propagation.
- [ ] The landing page presents distinct macOS/Linux, Windows PowerShell, and
      manual-download choices through a responsive, keyboard-accessible
      selector with accurate platform and architecture language.
- [ ] Installation commands, labels, manual-download links, and documentation
      links have one maintained content source within the landing package so
      repeated visible placements cannot silently diverge.
- [ ] The landing page links directly to package-owned installation
      documentation covering the overview, macOS/Linux, Windows, and manual
      methods.
- [ ] Current user documentation remains concise at package entry points and
      routes detailed installation behavior through focused pages that are
      published and discoverable in the documentation site.
- [ ] The website direction receives explicit approval after headed-Playwright
      comparison of competitor pages and a Crystal Lattice proposal, even if
      this task's execution plan has already been approved.
- [ ] The completed website implementation receives explicit visual approval
      after headed-Playwright review of the production build.
- [ ] The documentation direction receives explicit approval from a proposed
      page map and rendered outline, even if this task's execution plan has
      already been approved.
- [ ] The completed documentation receives explicit approval after the
      prepared documentation site is reviewed in a headed browser.
- [ ] Public pages claim a platform or installation method only after its
      implementation and native acceptance evidence exist; production
      publication is sequenced so the website never intentionally advertises
      an unavailable installer.
- [ ] Bundling, installation, publication, test, website, and documentation
      changes use the smallest clear ownership model and do not introduce
      package-manager channels, duplicated scenario implementations, or
      speculative abstractions.

## Scope and ownership

This is one standalone cross-package task. It does not reopen
`tasks/20260908-cli-distribution-test-levels.md`, whose completed work remains
the baseline for archive, installer, PATH, plugin-installation, and
credential-free startup behavior.

The application package owns installer, archive, target-matrix, release, and
user installation documentation. The landing package owns website
presentation and installation-choice communication. Existing specifications
are sufficient:

- extend
  `application/python/docs/development/specifications/cli-distribution/` for
  released targets, native PowerShell installation, and verification;
- extend
  `landing_page/docs/development/specifications/product-website-content/` for
  truthful installation choices and links.

No new cross-package specification is planned. The task coordinates the two
existing owners without creating a second behavioral contract.

## Requirement questions and material decisions

### Windows command-directory behavior

**Approved decision:** follow the common no-admin Windows CLI installation
pattern. Preserve the existing preference for a suitable writable directory
already on PATH. When none exists, the PowerShell installer creates a
per-user command directory under
`%LOCALAPPDATA%\Programs\Crystal Lattice\bin`, adds it once to the persisted
user PATH, and adds it to the current PowerShell process. It does not edit
PowerShell profiles or the system PATH. A fresh `cmd.exe` or PowerShell process
then resolves the installed `.cmd` launcher. An explicit `BIN_DIR` override
remains available and does not implicitly change PATH.

This is a deliberate Windows-specific refinement of the earlier
existing-PATH-only Bash-installer decision.

### Native `cmd.exe`

**Recommendation:** provide PowerShell as the native Windows installation
method, not a second batch installer. Verify the installed command by name
from both PowerShell and `cmd.exe`. When the install is launched by a child
PowerShell process from an already open `cmd.exe`, document that a new terminal
is needed to observe a newly persisted PATH entry because a child process
cannot mutate its parent environment.

### Manual download

**Recommendation:** make the manual website option link to the installation
overview/manual guide and to the latest GitHub Release rather than introducing
six mutable version aliases at the download CDN. The guide maps platform and
architecture to the immutable release filenames and explains archive
launchers.

### ARM runner availability

GitHub currently documents public hosted `ubuntu-24.04-arm` and
`windows-11-arm` runners. Windows ARM64 remains a public-preview runner.
Official `actions/setup-python` and Python standalone runtime support make the
target feasible, but dependency installation and the complete CLI smoke must
pass on the actual repository runners before the platform becomes a public
claim. Runner unavailability or a native dependency gap is a blocker to
advertising that row, not permission to substitute an emulated-only test.

### Production publication

Task approval authorizes local implementation only to the extent stated by the
user. Pushing implementation, creating a release tag, publishing CLI
downloads, and deploying the website remain explicit remote actions. The
execution must stop for the applicable confirmation before each production
mutation.

## Supporting facts

- The current released/native matrix has four targets: Linux AMD64, macOS
  AMD64, macOS ARM64, and Windows AMD64.
- Architecture normalization already understands AMD64 and ARM64. Explicit
  shell detection, release matrices, expected archive lists, tests, and public
  documentation enumerate only the current four targets.
- The bundled Windows archive already contains a native `.cmd` launcher. The
  current public installer is Bash-only and creates a Git Bash shim plus a
  `.cmd` forwarding command.
- The existing default-installer smoke runs the user-shaped
  `curl .../install.sh | bash` path from an isolated loopback endpoint and
  validates command lookup, boot, and plugin installation.
- The landing page currently stores one shell command in the hero and repeats
  it in the first-success guide. Its focused content test checks only the hero
  value.
- The landing content system supports data-driven section fields and small
  reusable Astro components. A new global section type is unnecessary if a
  focused reusable installation-choice component can serve the existing hero
  and first-success path.
- Application user documentation is already registered under
  `packages/application-python/` in the generated documentation site. New
  top-level package pages are copied and published without a new package
  registry entry.
- Competitor screenshots and browser state are disposable review inputs and
  belong under ignored `landing_page/artifacts/`; they are not production
  website assets.

## Execution plan

Status: Approved

The implementation is ordered so platform support becomes real before the
website presents it. Specifications and requirement rows come first. Native
installer/archive behavior and release verification come next. Website and
documentation each have a direction gate and a post-completion approval gate
that remain blocking even after this overall plan is approved.

### 1. Specification-first target update

Update the existing CLI-distribution specification and requirements with:

- the six-target release matrix;
- Bash and native PowerShell installer contracts;
- Windows command-directory and PATH behavior after the open decision is
  resolved;
- manual archive use;
- independent Bash, PowerShell, and archive acceptance boundaries;
- release publication and public-endpoint verification.

Update the website-content specification and requirements with outcomes for:

- an understandable installation-method chooser;
- explicit platform, architecture, and shell compatibility;
- direct links to current installation documentation;
- accessible/responsive method selection;
- public claims gated by owning release evidence.

Commit the specification/requirements update separately before implementation.
Do not update current user guides or public website copy to claim the target at
this stage.

### 2. Platform compatibility and installer implementation

Extend the maintained target lists and release workflow to build:

- `darwin-amd64`;
- `darwin-arm64`;
- `linux-amd64`;
- `linux-arm64`;
- `windows-amd64`;
- `windows-arm64`.

Extend the Bash installer's target detection for Linux ARM64 and, when
honestly executable on the native runner, Windows ARM64. Preserve its current
staging, replacement, PATH-selection, local-archive, verification, and
progress behavior.

Add `application/python/scripts/install.ps1` as an independent native
installer. Keep its contract parallel to `install.sh` where platform semantics
allow:

- latest or pinned version resolution;
- download-base and local-archive overrides;
- native architecture detection;
- ZIP extraction into staging;
- atomic replacement of the versioned runtime;
- `.cmd` command installation;
- default command-directory behavior selected by the approved Windows
  decision;
- `--help` and runtime-layout verification;
- numbered progress and actionable failures.

Keep one implementation owner per installer. Share only stable release naming
or test helpers where duplication would otherwise cause drift; do not create a
cross-language installer framework.

Update publication scripts, MIME/cache rules, expected archive lists, release
asset validation, and download smoke behavior for `install.ps1` and all six
archives.

### 3. Direct native acceptance and compatibility gate

Add or extend focused unit tests for:

- architecture and archive naming;
- Bash target detection;
- PowerShell target detection, version resolution, PATH behavior, staging,
  cleanup, overrides, and failure diagnostics;
- publication inputs and endpoint validation;
- root npm command and workflow contracts.

Add a direct PowerShell default-installer smoke that serves `install.ps1`,
`latest.txt`, and the native archive from an isolated loopback endpoint. It
must run the user-shaped PowerShell command, resolve `crystal-lattice` by name,
verify it from PowerShell and `cmd.exe`, boot the default-derived config, and
use independent mutable state.

Run the extracted-archive and applicable installer smokes on every native
matrix target. Windows AMD64 must cover both Git Bash and PowerShell
installation. Windows ARM64 must cover PowerShell and direct archive use; Bash
coverage is additionally required if the native runner supplies a meaningful
compatible Git Bash environment.

**Compatibility gate:** stop website implementation until all six native
archives and their required direct user paths pass on GitHub Actions. Report
any public-preview runner or dependency limitation rather than weakening the
matrix or changing a public claim.

### 4. Website direction approval gate

After the compatibility gate passes, use headed Playwright to inspect the
current installation selectors on Pi, OpenCode, Goose, Aider, and the local
Crystal Lattice page at representative desktop and mobile widths. Store
captures only under ignored `landing_page/artifacts/`.

Prepare a concise Crystal Lattice proposal showing:

- method labels and ordering;
- proposed desktop and mobile layout;
- selected/default tab behavior;
- command and copy-button treatment;
- platform/architecture explanation;
- manual-download and documentation links;
- keyboard interaction.

Present the competitor observations and proposal to the user, then stop for
explicit website-direction approval. Overall task-plan approval does not waive
this gate.

### 5. Website implementation and post-completion approval

Implement a small reusable installation-choice component and a data shape
owned by the landing content. Prefer extending the existing hero/first-success
components over adding a generic section system abstraction.

During implementation, inspect structure, selected/hover/focus/copied states,
keyboard tab and arrow-key behavior, light/dark themes, responsive widths, the
first-success guide, and documentation links with headed Playwright.

Add automated content/component/browser checks for method labels, commands,
ARIA state, keyboard selection, copy behavior, responsive overflow, and
documentation/manual links. Competitor pages remain human research inputs and
are not volatile CI dependencies.

After implementation and automated verification, present the complete
production-built homepage at desktop and mobile widths, interaction notes, and
known limitations. Stop for explicit website post-completion visual approval.

### 6. Documentation direction approval gate

Before writing current installation guides, present this proposed package-owned
page map with a rendered outline and sample command blocks:

- `application/python/docs/installation.md` — choose a method and identify the
  supported platform/architecture;
- `application/python/docs/installation-macos-linux.md` — shell installer,
  pinned/review-first forms, PATH behavior, updates, and troubleshooting;
- `application/python/docs/installation-windows.md` — PowerShell and Git Bash,
  Windows AMD64/ARM64, PATH behavior, PowerShell/cmd command use, updates, and
  troubleshooting;
- `application/python/docs/installation-manual.md` — release asset selection,
  extraction, direct launch, optional command setup, verification, and
  removal.

Show how the package README, quickstart, package docs index, MkDocs navigation,
and landing-page links route to those pages without duplicating full
instructions. Stop for explicit documentation-direction approval. Overall
task-plan approval does not waive this gate.

### 7. Documentation implementation and post-completion approval

Implement the method overview, macOS/Linux and Windows guides, manual
installation and troubleshooting, package-index and quickstart routing, and
landing-page links. Prepare and build the docs site throughout the work and
inspect light/dark, desktop/mobile, navigation, search, command blocks, and
cross-site links with headed Playwright.

Current docs are updated only after the corresponding behavior has native
evidence. Target-only wording remains confined to specifications until then.

After implementation and automated verification, present the complete
documentation journey in the prepared site and stop for explicit
documentation post-completion approval.

### 8. Final verification and truthful publication sequencing

Run:

- focused installer, archive, release-script, landing-content, component, and
  browser tests;
- complete application and Core fast suites;
- landing production build and visual tests;
- docs preparation, tests, and MkDocs build;
- landing-to-documentation Playwright smoke;
- the six-target native release matrix;
- bounded post-publication endpoint checks when publication is authorized.

Prepare implementation and website/docs commits so production order remains
truthful:

1. land and verify installer/archive support without publishing new website
   claims;
2. obtain explicit release confirmation, publish a new CLI version, and verify
   both installers and all six archives through the public endpoint;
3. only then land/deploy current website and user-documentation claims;
4. verify the deployed landing and documentation routes.

If all code must remain in one branch, use coherent commits so the installer
support can be released before the approved current-content commit is pushed.

### Implementation decisions and open questions

- **Task form:** one standalone task is recommended because distribution
  implementation is the primary owner and the existing website-program
  subtasks explicitly consume rather than define CLI release behavior.
- **Specification form:** update the two existing package-owned specifications;
  do not create a new cross-package specification.
- **Windows PATH decision:** approved; use the common no-admin per-user PATH
  fallback when no suitable writable command directory is already available.
- **Windows shell scope:** PowerShell is the native installation path;
  `cmd.exe` is an installed-command verification path, not a separate
  installer.
- **ARM acceptance:** native runner evidence is mandatory; emulation alone
  does not satisfy public support.
- **UI direction:** expected to use accessible method tabs or a segmented
  selector, but exact appearance and content wait for the mandatory website
  direction gate.
- **Manual downloads:** latest GitHub Release plus maintained documentation is
  preferred over introducing mutable per-target CDN aliases.
- **Approval count:** four total human checkpoints: website direction,
  website post-completion, documentation direction, and documentation
  post-completion.
- **Release/deployment:** no production release, push, tag, or site deployment
  occurs without explicit authorization at the relevant execution point.

### Documentation

- Extend the existing application CLI-distribution specification, technical
  specification, and requirements before implementation.
- Extend the existing product-website content specification and requirements
  before website implementation.
- Add the four focused application installation user pages after documentation
  direction approval and verified native behavior.
- Keep `application/python/README.md`, `application/python/docs/quickstart.md`,
  and `application/python/docs/index.md` concise and link-oriented.
- Update root quickstart wording only where needed to route users to the
  maintained installation chooser.
- Update `application/python/docs/development/cli-distribution.md` and
  download-deployment documentation for current implementation and release
  operations.
- Update landing package content-system documentation only if the delivered
  reusable component/data contract materially changes website authoring.
- Do not edit generated `landing_page/dist/`, `docs_site/prepared/`, or
  `docs_site/dist/`.

### Task checklist

- [x] Obtain approval for this draft plan and the Windows PATH refinement.
- [x] Update CLI-distribution and website-content specifications and
      requirements.
- [ ] Commit the specification-first change.
- [ ] Add Linux ARM64 and Windows ARM64 release targets.
- [ ] Extend the Bash installer and target detection.
- [ ] Implement and focus-test the native PowerShell installer.
- [ ] Extend publication, release validation, and public smoke scripts.
- [ ] Add independent PowerShell and expanded native archive/install smokes.
- [ ] Run local focused and fast verification.
- [ ] Push only when authorized and obtain six-target native compatibility
      evidence.
- [ ] Stop at the compatibility gate if any required target or direct user path
      is not genuinely verified.
- [ ] Run headed competitor/local Playwright review and obtain website
      direction approval.
- [ ] Implement the approved website direction and obtain website
      post-completion visual approval.
- [ ] Present and obtain documentation-direction approval.
- [ ] Implement the approved documentation direction and obtain documentation
      post-completion approval.
- [ ] Run final local, browser, documentation, and native matrix verification.
- [ ] Obtain explicit confirmation before release publication.
- [ ] Publish and verify a new CLI version when authorized.
- [ ] Land/deploy current website and documentation claims only after the
      public installers and archives are available.
- [ ] Verify public landing, docs, installers, and archive routes when
      deployment is authorized.
- [ ] Update requirement evidence and append completion notes.

### Requirement verification

- Native release jobs on the six declared target runners each build the
  correctly named archive and execute the required independent direct archive
  and installer scenarios.
- Windows AMD64 and ARM64 tests execute the downloaded PowerShell installer,
  resolve the command by name in PowerShell and a fresh `cmd.exe`, boot the
  application without credentials, and prove isolated plugin installation.
- Bash tests retain direct macOS/Linux and Windows Git Bash behavior without
  sharing mutable state with PowerShell tests.
- Publication tests and authorized live smoke prove `install.sh`,
  `install.ps1`, `latest.txt`, and all six immutable archives are reachable and
  consistent.
- Landing automated tests prove all visible methods, commands, support labels,
  links, tab semantics, keyboard behavior, and copy behavior match maintained
  content; the website direction and post-completion approvals provide the
  remaining human visual evidence.
- Documentation preparation/build and the two-site Playwright smoke prove all
  installation pages are published, linked from the landing page and package
  index, navigable on desktop/mobile, and consistent with native tests; the
  documentation direction and post-completion approvals provide the remaining
  human evidence.
- Public endpoint and deployed-site checks occur only after authorization and
  confirm the exact user-facing routes rather than repository-local
  substitutes.

### Additional implementation verification

- PowerShell syntax and static checks appropriate to the available Windows
  environment.
- Installer failure tests for unsupported architecture, malformed/empty
  latest marker, missing archive, failed extraction, stale staging state,
  unsuitable explicit command directory, failed PATH persistence, and
  verification failure.
- Upgrade tests preserve deterministic replacement and reuse a prior suitable
  command location.
- Both installers preserve local-archive inputs for deterministic smoke
  orchestration without changing the public default path.
- ARM manifests report the correct architecture, packaged Python is native,
  and launcher processes do not silently run an AMD64 archive under emulation.
- Windows process-tree cleanup and port-closure checks continue to cover child
  processes launched through `.cmd` wrappers.
- Shell syntax, Python compile/type/lint checks, workflow YAML parsing, package
  script contract tests, and documentation link validation.
- Headed Playwright review covers competitor and local pages, but CI exercises
  only repository-owned pages so competitor redesigns or availability cannot
  break builds.

## Implementation Notes

- 2026-09-13: The user approved execution, reduced human checkpoints to four
  total, and approved standard no-admin Windows CLI behavior. The mandatory
  stops are website direction, website post-completion, documentation
  direction, and documentation post-completion.
- 2026-09-13: Extended the existing application CLI-distribution target with
  requirements `CLIDIST-110` through `CLIDIST-116` and extended the website
  content target with `WEB-INSTALL-001` through `WEB-INSTALL-004`. Current
  public guides and landing copy remain unchanged until implementation and
  native evidence exist.
# Enforce Bundle Content And Runtime Boundaries

Define and enforce the immutable artifact, installed-plugin, mutable cache, and
test-only dependency boundaries for computer runtime bundles and fixed iOS
runtime bundles.

## Requirements checklist

- [ ] A normal computer runtime bundle contains no installed plugin package;
  bundled plugin projects are installed into a mutable user/plugin cache on
  first CLI use.
- [ ] The fixed iOS runtime bundle contains the exact provider, extension,
  tool, and application-plugin closure selected by the iOS product
  configuration and performs no dynamic plugin installation.
- [ ] No product bundle contains plugin test files, pytest, test fixtures,
  development-only helpers, or dependency sets installed through a plugin
  `dev` extra.
- [ ] Production bundle/build/runtime code never hard-codes installation of a
  specific plugin's development dependencies; only test infrastructure may
  request those dependencies.
- [ ] Computer-bundle verification proves installed plugins load from the
  mutable plugin cache after first startup while the immutable runtime bundle
  remains unchanged.
- [ ] iOS-bundle verification proves preinstalled runtime modules load from
  the immutable iOS archive, dynamic installation is disabled, and mutable
  plugin caches or source/editable fallbacks cannot satisfy those imports.
- [ ] Test-only dependency overlays are external and disposable, contain no
  product provider installation, cannot shadow runtime modules claimed by the
  tested artifact, and are never copied into a product bundle.
- [ ] Build and validation commands fail with actionable evidence when an
  artifact contains a forbidden package, omits a required package, loads from
  the wrong origin, changes during verification, or crosses an immutable/
  mutable boundary.
- [ ] Bundle composition and verification rules are documented for package
  authors, runtime/bundle maintainers, and test authors.

## Scope

This task covers repository-wide rules and reusable enforcement for:

- source plugin projects;
- immutable computer runtime bundles;
- computer-bundle plugin project roots and first-start installation;
- mutable plugin caches and state;
- fixed preinstalled iOS runtime archives;
- test-only dependency environments and overlays;
- module/package provenance and artifact-content assertions.

It does not decide which product features or providers should be enabled in a
particular application. Product-owned configuration remains responsible for
selecting its fixed iOS closure and its computer-bundle plugin catalog.

## Requirement questions

No requirement question blocks planning.

## Supporting details

### Agreed boundary rules

- A normal computer bundle ships the runtime without installed plugins. The
  first CLI start installs selected plugin projects into mutable cache/state.
- The iOS runtime cannot install plugins dynamically and therefore embeds its
  fixed reviewed plugin closure.
- Tests and development dependencies are outside every product artifact.
- Plugin projects and their tests may change to express the correct boundary;
  incompatible historical test setup is not itself a compatibility contract.
- Dev dependency declarations remain package-owned. Product code must not
  contain provider-specific `<plugin>[dev]` installation commands.

### Environment facts rather than layout modes

Consumers should receive concrete facts rather than branching on a global
`source`, `computer-bundle`, or `ios-preinstalled` enum:

- available installable plugin project paths;
- preinstalled plugin/module entries and their expected origins;
- mutable plugin cache path;
- dynamic-install policy;
- runtime Python executable;
- artifact path and content/hash manifest;
- runtime distributions supplied by the artifact;
- test-only overlay path;
- provider transport and configured extension/capability facts.

This supports mixed environments where some plugins are preinstalled and
others are installable without inventing another global mode.

### Evidence from the iOS provider correction

The provider validation in
`tasks/20260910-ios-embedded-runtime-poc/015-useful-runtime-tools-providers-and-settings.md`
demonstrated a feasible test-only overlay:

- pytest and dotenv loaded from an ephemeral virtual environment;
- `agent_core`, `requests`, OpenAI Responses, and OpenRouter loaded from the
  unchanged iOS ZIP;
- neither provider project was installed into the overlay;
- artifact-provided `agent-core` had to be excluded from dev requirements
  because it was already in the ZIP and unavailable from the configured
  package index;
- before/after provenance and SHA-256 assertions caught the intended
  boundaries.

It also demonstrated why positive test selection is necessary: pytest imports
all supplied test modules before marker deselection, so passing an entire
package directory can accidentally require SDK-only or application-only
dependencies outside the selected runtime closure.

## Execution plan

Status: Draft

### Artifact and boundary model

Introduce a small reusable representation of observable artifact/runtime
facts, without a global artifact-layout enum. It should be able to answer:

- Is a plugin entry declared preinstalled, installable from a project, or
  unavailable?
- Where must each runtime module originate?
- Which directory is immutable?
- Which cache/state directories may change?
- Is dynamic installation permitted?
- Which distributions/modules are supplied by the artifact?
- Which dependencies are test-only overlay content?

Keep immutable bundle content, shipped installable plugin projects, mutable
plugin installation cache, mutable application state, and test overlays as
separate paths and concepts.

### Machine-readable composition evidence

Use or extend maintained bundle metadata so validators can determine expected
content without reconstructing builder internals. Record, as appropriate:

- artifact type and format version;
- immutable artifact root/hash;
- preinstalled runtime distributions/modules;
- shipped-but-not-installed plugin projects;
- dynamic installation policy;
- expected mutable cache/state locations;
- explicitly forbidden test/dev content;
- selected fixed iOS plugin closure.

Do not add metadata merely to duplicate facts already available from a
maintained manifest. Prefer extending the existing runtime/preinstalled-plugin
manifests where ownership is clear.

### Reusable verification assertions

Implement reusable assertions covering the previous bundle-verification
proposal:

#### Computer runtime bundle before first startup

- Assert provider/tool/application plugin import packages are absent from the
  immutable runtime environment.
- Assert pytest, test trees, fixtures, development helpers, and dev-only
  distributions are absent.
- Assert shipped plugin projects, when part of the distribution, remain
  projects rather than installed site-packages.
- Record the immutable runtime and plugin-project hashes.

#### Computer runtime bundle after first startup

- Launch the public bundled CLI with fresh isolated state.
- Assert the selected plugin was installed into the configured mutable plugin
  cache.
- Assert all loaded plugin modules originate from that cache, not from the
  immutable runtime, repository checkout, editable finder, or host
  site-packages.
- Assert immutable runtime and shipped plugin-project hashes are unchanged.
- Assert a second startup reuses a valid installation instead of modifying the
  immutable artifact or reinstalling unnecessarily.

#### Fixed iOS runtime bundle

- Assert every configured provider/extension/tool/application-plugin module is
  present in the iOS archive.
- Assert unselected plugin packages and all test/dev content are absent.
- Assert dynamic plugin installation is disabled.
- Assert selected provider/runtime modules originate from the archive before
  and after every test/request.
- Assert source trees, editable installations, mutable plugin caches, and
  test overlays cannot satisfy or replace those imports.
- Assert the archive hash is unchanged after verification.

#### Test-only dependency overlays

- Build overlays outside the artifact and mutable product state.
- Install only package-owned test/dev requirement strings selected by test
  infrastructure; do not install the provider project under test.
- Exclude requirements declared as already supplied by the artifact.
- Put the artifact before overlay site-packages and preimport claimed runtime
  modules before pytest/test helpers.
- Assert overlay-provided modules are test/dev helpers only.
- Assert the overlay is removed after execution and was never copied into a
  bundle.

### Build and test integration

Integrate assertions at the narrowest useful boundaries:

- builder/package tests inspect staged content before archive creation;
- archive tests inspect final immutable content and metadata;
- computer distribution smoke tests drive first-start installation through the
  public CLI;
- iOS provider/package tests validate preinstalled module provenance;
- repository-level commands expose the important enforcement gates.

Do not run hosted provider API tests merely to verify static bundle content.
Use hosted tests only where provider behavior/provenance across the artifact
boundary is the required evidence.

### Failure evidence

Failures should identify:

- artifact and hash;
- expected and actual module origin;
- forbidden or missing archive entry;
- immutable path that changed;
- unexpected installed distribution;
- overlay/cache path involved;
- applicable dynamic-install policy.

Never include credentials, request authorization values, or full environment
contents in assertion output. Hosted test commands use secret-safe traceback
settings.

### Implementation decisions and open questions

- **Decision:** use concrete environment/artifact facts, not a global
  source/computer/iOS enum.
- **Decision:** preinstalled and installable status is resolved per plugin
  entry, allowing mixed environments.
- **Decision:** tests may install development requirements only in explicitly
  test-owned external environments.
- **Decision:** provider projects under test are not installed into an iOS
  test overlay; provenance must remain attributable to the iOS artifact.
- **Decision:** computer-bundle plugin installation is verified through the
  public first-start workflow rather than by embedding installed plugins in
  the runtime or using test-only shortcuts.
- **Decision:** content assertions and runtime provenance assertions are both
  required; either alone leaves an important boundary unverified.
- **Recommendation:** extend existing maintained manifests before introducing
  a new repository-wide bundle manifest.
- **Open design decision:** identify the existing manifest owner best suited
  to record computer shipped-plugin projects and fixed iOS preinstalled
  distributions. Resolve locally after inspecting current builders; escalate
  only if ownership would materially change public artifact contracts.

### Documentation

- Add project-wide bundle/content boundary guidance for runtime and plugin
  maintainers.
- Document package-author responsibilities for runtime versus dev
  dependencies and test markers.
- Document computer first-start installation and immutable/mutable paths.
- Document fixed iOS closure construction and prohibited dynamic installation.
- Document test-overlay construction, provenance assertions, and
  secret-safe hosted verification.
- Update package/build documentation affected by concrete enforcement
  commands or manifest changes.

### Task checklist

- [ ] Inventory computer and iOS bundle builders, manifests, artifact layouts,
  plugin project roots, cache/state roots, and existing distribution tests.
- [ ] Select or extend the maintained metadata owner for expected bundle
  composition and runtime policy.
- [ ] Implement reusable artifact-content, hash, and module-provenance
  assertions.
- [ ] Add computer pre-start assertions proving installed plugins and dev/test
  content are absent.
- [ ] Add realistic first-start CLI verification proving plugins install into
  mutable cache and load from there.
- [ ] Add repeat-start verification and immutable artifact hash checks.
- [ ] Add fixed iOS closure assertions for required, unselected, and forbidden
  content.
- [ ] Add iOS runtime provenance and dynamic-install-denial assertions.
- [ ] Generalize the external test-overlay assertions without moving dev
  dependencies into a product builder.
- [ ] Add root/package commands for the important boundary gates.
- [ ] Update affected tests, package metadata, and documentation.
- [ ] Run fast builder/package tests and realistic computer/iOS artifact
  verification.

### Requirement verification

- Computer immutable content: inspect a built artifact and prove no installed
  plugin or test/dev content is present.
- Computer first-start boundary: launch the bundled CLI with fresh state,
  install a selected shipped plugin through the public path, and prove module
  origin is the mutable cache.
- Computer immutability: compare artifact/project hashes before and after first
  and repeated startup.
- iOS fixed closure: compare configured plugin entries with archive contents
  and prove required entries are present while unselected/test/dev entries are
  absent.
- iOS runtime origin: execute selected provider/plugin behavior and prove all
  claimed runtime modules remain archive-backed before and after execution.
- Test overlay: prove test helpers come from an external disposable
  environment, provider/runtime modules do not, and no overlay content enters
  either product artifact.
- Policy enforcement: intentionally malformed fixture artifacts fail with
  actionable missing, forbidden, origin, cache, or immutability evidence.

### Additional implementation verification

- Verify editable import finders and host/global site-packages cannot satisfy
  artifact-owned modules.
- Verify symlinks or path normalization cannot disguise a mutable/source path
  as an immutable artifact origin.
- Verify assertion tooling works for ZIP paths and ordinary filesystem
  layouts.
- Verify failure messages redact secrets and avoid dumping complete
  environments.
- Verify generated documentation or prepared site content is changed only
  through maintained sources.
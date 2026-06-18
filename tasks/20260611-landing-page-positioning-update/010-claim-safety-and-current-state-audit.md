# Claim Safety And Current State Audit

Audit the current landing page copy for misleading claims, jargon-heavy phrasing, placeholder links, and statements that are stronger than the current product surface supports.

## Requirements checklist

- [x] Read the current landing page content and components referenced below.
- [x] Identify copy that overclaims app availability, provider switching, mobile capabilities, licensing, bridge behavior, or "complete API" coverage.
- [x] Replace or plan replacements using plain-language, human-centered wording.
- [x] Confirm all public links either resolve to real destinations or are clearly marked as coming soon.
- [x] Record any remaining claims that need maintainer confirmation before publication.

Parent Task: `tasks/20260611-landing-page-positioning-update/000-main.md`

## Files To Inspect

In the landing page worktree:

- `landing_page/src/content/pages/home.yaml`
- `landing_page/src/content/pages/mobile.yaml`
- `landing_page/src/content/markdown/home-features.md`
- `landing_page/src/components/Nav.astro`
- `landing_page/src/components/Footer.astro`
- `landing_page/src/components/mobile/Download.astro`
- `landing_page/src/content/markdown/privacy.md`
- `landing_page/src/content/markdown/terms.md`

## Known Risky Current Claims

These were observed during planning and should be fixed or validated:

- `home.yaml`: "The Open Source AI Agent Platform" and broad "Apache 2.0" claims. The root project is Apache-2.0, but the broader repo includes separately licensed AGPL components such as bridge/cloud/cloud-agent pieces. Avoid blanket licensing claims unless verified.
- `home.yaml`: "provider-agnostic" is true in a broad sense but hides the stronger message and can imply all providers behave identically.
- `home.yaml`: placeholder `href: "#"` for GitHub and docs actions.
- `home-features.md`: "The terminal, mobile app, and SDK all work identically regardless of which provider is configured" is too strong and conflicts with provider-native/model-family-specific behavior.
- `mobile.yaml`: App Store and Google Play buttons currently use `href: "#"` and should be "Coming soon" for now.
- `mobile.yaml`: "Anything you can do from the terminal, you can do from your phone" is too strong.
- `mobile.yaml`: "Change the model mid-conversation without losing context" is too strong. In-session provider/model switching is nuanced and not always possible.
- `mobile.yaml`: `crystal-lattice ... --enable-bridge` is not the documented bridge flag. Use `--bridge-url wss://...`.
- `mobile.yaml`: do not say bridge is for avoiding exposing a server. Say it lets users connect from outside the local network.

## Plain-Language Guardrails

Prefer:

```text
Start on your computer. Continue from your phone.
```

Avoid leading with:

```text
local-first
HTTP client
Bonjour
bridge
model-native
provider-agnostic
```

Introduce concepts by explaining them:

- Local network discovery: "On the same Wi-Fi, the app can find your computer automatically."
- Bridge: "When your phone is outside that network, deploy the bridge and pair through it."
- Model-family harnesses: "Different model families are optimized around different coding tools and instructions."
- Plugin-driven UI: "A setting appears because a plugin exposes it."

## Suggested Link Handling

Use the repository URL where appropriate:

```text
https://github.com/dynamicprogrammingsolutions/crystal-lattice
```

Docs can point to the GitHub README or be omitted until there is a real docs URL.

Mobile store buttons:

```text
App Store - Coming soon
Google Play - Coming soon
Run from source
```

## Execution plan

Added during completion after maintainer approval.

1. Update homepage content in `landing_page/src/content/pages/home.yaml`.
   - Replace broad "open source AI agent platform", "local-first", and "provider-agnostic" lead copy with the approved hero direction: "Own the harness. Use the agent anywhere."
   - Replace placeholder GitHub/docs links with real repository or README links.
   - Keep the quickstart structure, but change visible "server" language to "start Crystal Lattice" / "running Crystal Lattice" where possible.
   - Remove blanket Apache 2.0 CTA language and use safer source-available/open-development wording.

2. Update feature copy in `landing_page/src/content/markdown/home-features.md`.
   - Soften privacy/local/offline claims.
   - Remove "all clients work identically regardless of provider" and "one-line provider switching" claims.
   - Keep plugin and session strengths, but phrase provider/model capabilities as configuration-dependent.

3. Update mobile page content in `landing_page/src/content/pages/mobile.yaml`.
   - Mark App Store and Google Play links as coming soon.
   - Add a run-from-source fallback link.
   - Replace "complete API", "anything terminal can do", and model-switching claims.
   - Replace `--enable-bridge` with `--bridge-url wss://<your-cloudfront-domain>/ws/websocket`.
   - Explain local-network discovery and bridge pairing in plain language before jargon.

4. Update shared navigation/footer links and copy.
   - Replace all placeholder GitHub/docs links.
   - Remove blanket Apache 2.0 claims from footer copy.
   - Keep product/legal links intact.

5. Update mobile store button components.
   - Support `comingSoon: true` in `landing_page/src/components/mobile/Hero.astro` and `landing_page/src/components/mobile/Download.astro`.
   - Render coming-soon store buttons as disabled-looking non-links while preserving normal links for real destinations.

6. Update legal copy for claim safety.
   - In privacy copy, avoid absolute "no cloud" and broad Apache/open-source assertions.
   - In terms copy, clarify that repository components have their own licenses; root and many packages are Apache-2.0, while bridge/cloud components are AGPL-3.0.
   - Update `landing_page/src/content/pages/terms.yaml` SEO copy because it repeats the broad Apache claim.

7. Verify.
   - Run targeted `rg` scans for placeholder links and risky phrases.
   - Run `yarn build` from `landing_page`.
   - Add completion notes and mark task status.

## Completion Notes

Added during completion.

Implemented the claim-safety pass across the current landing page without
attempting the full future positioning/layout work.

Changed content:

- `landing_page/src/content/pages/home.yaml`
  - Replaced broad "open source AI agent platform", "local-first", and
    "provider-agnostic" lead copy with the approved "Own the harness. Use the
    agent anywhere." direction.
  - Replaced placeholder GitHub/docs links with repository/README links.
  - Changed user-facing "start the server" language to "start Crystal Lattice."
  - Removed blanket Apache 2.0 CTA language.
  - Softened "Any OpenAI-compatible API" to "OpenAI-compatible APIs."

- `landing_page/src/content/markdown/home-features.md`
  - Replaced "local-first & private" with more accurate storage/traffic wording.
  - Removed "all clients work identically regardless of provider" and one-line
    provider switching claims.
  - Softened streaming, session, and tool metadata claims to acknowledge provider
    and plugin variation.

- `landing_page/src/content/pages/mobile.yaml`
  - Removed "complete API", "anything terminal can do", "own server", and
    mid-conversation model switching claims.
  - Marked App Store and Google Play as coming soon.
  - Added a "Run from source" link to the mobile app directory in the repository.
  - Replaced `--enable-bridge` with
    `--bridge-url wss://<your-cloudfront-domain>/ws/websocket`.
  - Explained automatic local network discovery and bridge pairing in plainer
    language.

- `landing_page/src/components/Nav.astro` and
  `landing_page/src/components/Footer.astro`
  - Replaced `href="#"` placeholders.
  - Removed broad single-license/footer Apache claims.

- `landing_page/src/components/mobile/Hero.astro` and
  `landing_page/src/components/mobile/Download.astro`
  - Added `comingSoon` button support so store buttons are no longer dead links.
  - Added a GitHub icon for the "Run from source" fallback.

- `landing_page/src/content/markdown/privacy.md`,
  `landing_page/src/content/markdown/terms.md`, and
  `landing_page/src/content/pages/terms.yaml`
  - Replaced broad Apache-only and "no cloud" style assertions with
    component-scoped license/privacy wording.

Verification:

- Ran the targeted risky-phrase scan for placeholder links and overclaims:
  no matches remained for `href="#"`, `provider-agnostic`, `complete Crystal
  Lattice API`, `Anything you can`, `mid-conversation`, `--enable-bridge`,
  `HTTP client`, broad `Apache 2.0`, `local-first`, `zero-config`,
  `own server`, `the server`, and related patterns.
- Ran `yarn build` from `landing_page`; build passed.
- Build still emits pre-existing Astro content warnings for duplicate markdown
  IDs: `privacy`, `home-features`, and `terms`. This was not introduced by the
  claim-safety edits and is outside this task's scope.

Remaining maintainer confirmation before publication:

- Legal/privacy copy should still receive maintainer/legal review before a
  public launch, especially around bridge retention wording and component
  license summaries.
- Store availability remains intentionally "coming soon"; real store URLs should
  replace those states later.

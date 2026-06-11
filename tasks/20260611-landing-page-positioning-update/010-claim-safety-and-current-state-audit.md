# Claim Safety And Current State Audit

Audit the current landing page copy for misleading claims, jargon-heavy phrasing, placeholder links, and statements that are stronger than the current product surface supports.

## Requirements checklist

- [ ] Read the current landing page content and components referenced below.
- [ ] Identify copy that overclaims app availability, provider switching, mobile capabilities, licensing, bridge behavior, or "complete API" coverage.
- [ ] Replace or plan replacements using plain-language, human-centered wording.
- [ ] Confirm all public links either resolve to real destinations or are clearly marked as coming soon.
- [ ] Record any remaining claims that need maintainer confirmation before publication.

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

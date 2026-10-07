# Host And Release The Bridge Demo For Invited Testers

Deliver a bounded, account-based free bridge demo using the existing public
identity, challenge, ownership and demo-limit implementations over HTTPS/WSS.
This task owns the operated deployment and complete tester experience.

## Requirements checklist

- [ ] Invited testers can authenticate through configured real identity
  sources and receive bounded free/demo access without a purchase.
- [ ] A tester can log in from the CLI on their Mac, claim their runtime,
  sign in from mobile, discover their own server, complete configured pairing
  and reconnect through the hosted deployment.
- [ ] First-use access, challenge renewal and allowance tiers remain
  replaceable and work through the existing contracts. Demo grants are bound
  to authenticated accounts; arithmetic is not treated as authentication.
- [ ] The deployed service enforces account/server isolation, signed grant
  validity, expiry/revocation, approved demo limits and HTTPS/WSS transport,
  while preserving non-production demo guards.
- [ ] The operator has an approved tester cap, access duration, operating
  limits and cost boundary, plus usable provisioning/removal, monitoring,
  support, recovery and shutdown procedures.
- [ ] Required identity/server credentials use the established secure storage
  and role boundaries. Public source, logs and review evidence expose no
  credentials, private account configuration or tester personal information.
- [ ] Actual deployed mobile/CLI flows and human review establish release
  acceptance before invitations; public availability and privacy/support
  guidance accurately describe the limited demo and relay visibility.

Parent Task: tasks/20260821-modular-bridge-access-platform/000-main.md

Depends On:

- tasks/20260821-modular-bridge-access-platform/040-demo-entitlement-limits-and-client-integration.md
- tasks/20260821-modular-bridge-access-platform/080-authentik-client-identity-and-account-linking-contracts.md
- tasks/20260821-modular-bridge-access-platform/140-hosted-access-grant-enforcement.md
- tasks/20260821-modular-bridge-access-platform/150-terminal-server-login-and-ownership.md
- tasks/20260824-os-level-notification-delivery/020-community-authentik-bridge-identity.md

Coordinates With:

- tasks/20260628-cli-simplification-and-bridge-ux/040-frontend-saved-bridge-urls.md
- tasks/20260610-mobile-message-refresh-performance/050-plain-http-bridge-large-payload-path.md
- tasks/20260823-frontend-connection-lifecycle/030-mobile-connection-race-and-cancellation-cleanup.md

## Approved scope and unresolved decisions

Scope approved on October 7, 2026. Implementation and deployment are not yet
approved; the execution plan below is Draft.

The scope and dependency revision approved on October 7, 2026 brings the
complete login/demo prerequisite chain ahead of CLI/PKG/onboarding work.
E2EE, production quota/metering and their advanced transport integration are
later deliveries and do not gate this demo. Keep the existing demo allowance
limits, actual identity, ownership, grant enforcement and HTTPS/WSS.

**HUMAN JUDGMENT — unresolved before deployment:** hosting/data location,
capacity and cost boundary; enabled login sources and callback configuration;
tester eligibility/cap; duration and allowances; pairing policy; support,
privacy/retention and shutdown policy; and the approved mobile tester channel.
Keep these outside fixed requirement values until decided.

**DESIGN DECISION — unresolved:** how the authenticated community configuration
uses account-bound demo allowances while retaining the demo provider's
production-use guards. Define and review the configuration; an unsafe
production override is not an approved solution.

## Ownership and supporting facts

- 030/040 own the challenge/provider contract and client enforcement. Their
  fake providers prove replaceability; a configured example subject is not
  real user authentication.
- 080 owns base mobile account UI and OIDC clients. 150 owns CLI login,
  claiming and server credentials. These concerns remain separate from
  model-provider authorization.
- The community identity task owns the reusable Authentik/account/ownership/
  grant service and its deployment/recovery capability. Reuse that service;
  this task owns operating and accepting the selected hosted instance.
- 040 owns demo allowance enforcement; 140 owns basic grant/ownership
  enforcement, credential separation, transport authorization and redaction.
  These are the early-demo foundations.
- 060/070 own E2EE and its security review; 130/170 own production quota/
  metering and encrypted/metered integration. None gates this demo.
- HTTPS/WSS protects transport to the relay. The demo relay can read
  application content while processing it; public guidance must describe
  this and must not claim that the demo is end-to-end encrypted.
- Mobile connects to the runtime on the tester's Mac. Desktop bridge-login
  UI, subscription purchases, push notifications and commercial launch are
  outside this delivery.
- Existing AWS bridge deployment is a reusable baseline, documented in
  `tasks/20260421-distribution-release-workstreams/055-aws-fargate-external-bridge.md`.
  Fixed bounded capacity may be sufficient; autoscaling is owned separately.
- Source and operator documentation must be public-safe: repository-relative
  references, non-sensitive configuration and credential-based discovery;
  no personal addresses, workstation paths or private repository references.

## Execution plan

Status: Draft

Use real community identity to establish the stable account. An independently
replaceable access/challenge policy determines that account's demo allowance.
The service issues normalized app/server grants; the bridge validates them,
ownership, demo allowances and HTTPS/WSS transport. The CLI retains
server-scoped credentials, while the mobile client retains its own secure
account session.
The relay remains independent of identity-provider and payment internals.

The community task supplies reusable deployment and account-service behavior.
Select a bounded configuration here rather than creating a second account
store or alternate client path. All tester operations use the production CLI,
mobile UI and frontend adapter. Existing fake-provider tests supplement the
deployed acceptance and do not replace it.

### Delivery steps and human boundaries

1. **AGENT:** Verify dependency delivery, base authentication/transport
   security evidence and actual compatible client/runtime revisions. Resolve
   stale task/spec references. Record genuine gaps instead of claiming Draft
   work exists.
2. **AGENT + HUMAN JUDGMENT:** Prepare the smallest deployment proposal and
   settle the unresolved policy choices above. Show resources, data handling,
   limits, operations and rollback. Keep secrets and tester lists private.
3. **HUMAN — MANDATORY where owner access is needed:** Configure approved
   social-provider credentials/redirects and any interactive account-owner
   step. Enter credentials through secure interfaces; an agent can configure
   ordinary issuer/client settings after credentials and authorization exist.
4. **AGENT:** Prepare reproducible deployment/configuration, role-scoped secret
   references, TLS endpoints, bounded monitoring and operator procedures from
   the public community/bridge baseline. Review the account-bound allowance
   integration and production guards before any hosted mutation.
5. **AGENT:** Verify locally using the real services and production clients:
   login, account mapping/linking, claiming, isolation, challenge/limits,
   credential refresh/revocation and request flow over HTTPS/WSS.
6. **HUMAN JUDGMENT + EXPLICIT DEPLOYMENT APPROVAL:** Review the concrete
   commands/change set, enabled providers, privacy/support text and spend
   exposure. Approve the selected deployment and controlled test identities.
   Server operations still follow the repository's sensitive-server rules.
7. **AGENT:** Execute the authorized deployment. Validate TLS, issuer/key
   discovery, effective policy, health, secret redaction and bounded resource
   use. Record only public-safe outputs in this task.
8. **AGENT + HUMAN:** Through the real mobile UI and CLI, sign in, claim a
   controlled runtime, discover/pair/connect, send a request and reconnect.
   Use the approved tester build/channel; coordinate its normal release task
   if an updated signed client is required.
9. **AGENT:** Verify a second account cannot discover/control the first
   account's runtime; uninvited access is denied; grants expire/revoke within
   their documented bounds; and challenge renewal/tier limits remain
   account-scoped. Use approved short policies through normal configuration.
10. **AGENT:** Confirm logs and public review evidence exclude credentials,
    application payloads and tester personal information. Check credential
    separation/forwarding and privacy claims against the actual relay
    behavior. Exercise restart/recovery and operator removal through normal
    interfaces, with authorized controlled test data.
11. **HUMAN JUDGMENT:** Accept the actual tester UX, demonstrated login sources,
    challenge/limit messages, support/recovery and public claims. Record
    observations; automated checks do not substitute for this acceptance.
12. **AGENT + HUMAN AUTHORIZATION:** Open only the approved cohort, publish
    approved guidance, retain bounded evidence and schedule agreed access
    retirement/cleanup. Changes to cohort, limits or public availability need
    their applicable authorization.

### Implementation decisions and open questions

- Approved: one hosted-demo task in this directory reuses the existing
  provider, client, ownership, demo-limit and community-service tasks.
- Approved: this limited demo uses HTTPS/WSS and real identity without E2EE
  or production quota/metering. Those later production requirements remain
  owned by 060/070/130/170.
- Approved: real login and free/demo entitlement are separate replaceable
  concerns. No purchase or notification delivery is a prerequisite.
- Approved: production mobile/CLI paths are decisive. Desktop bridge support
  is outside the selected client scope.
- Open: select hosting, providers, permitted cohort, allowances, pairing and
  operator/data policy before execution. Keep community task deployment
  decisions consistent rather than independently resolving them here.
- Open: define the secure authenticated demo configuration without weakening
  the non-production provider guard or identity/account binding.
- Open: select a compatible tester-client distribution channel and arrange
  any required signed build/review through its existing release work.

### Documentation

- Community identity and deployment/recovery guidance stays with its existing
  task. Add only hosted-demo operating configuration and supported tester
  onboarding to owning bridge/application/mobile documentation.
- Public guidance describes real sign-in, CLI registration, connection,
  challenge/allowance, withdrawal of access, relay visibility and support
  behavior. Distinguish HTTPS/WSS transport protection from later E2EE.
- Update current availability/privacy/support wording only with approved,
  verified deployment facts. Keep operational secrets and tester records out
  of public task/source/documentation.

### Task checklist

- [ ] **AGENT:** Confirm prerequisites, source/client revisions and real gaps.
- [ ] **AGENT + HUMAN JUDGMENT:** Settle deployment, access and operating policy.
- [ ] **HUMAN as required:** Complete provider credential/owner setup.
- [ ] **AGENT:** Prepare and locally verify the reusable configuration.
- [ ] **HUMAN:** Approve concrete deployment and controlled hosted tests.
- [ ] **AGENT:** Deploy and verify the actual services.
- [ ] **AGENT + HUMAN:** Complete hosted login/claim/connect/challenge flows.
- [ ] **AGENT:** Verify isolation, expiry/revocation, demo limits, HTTPS/WSS,
  credential handling, log redaction and recovery.
- [ ] **HUMAN JUDGMENT:** Accept tester UX, policy and public guidance.
- [ ] **AGENT + HUMAN:** Open the approved cohort and record operations/evidence.

### Requirement verification

- Requirements 1–3: production mobile UI plus CLI against the real configured
  issuer/community service and hosted bridge. Confirm account mapping,
  claiming, pairing, challenge/renewal and reconnect using the normal APIs.
- Requirement 4: two-account hosted negative cases, normal configured
  expiry/demo-limit policies and actual HTTPS/WSS request traffic. Include
  tamper/revocation evidence from the actual grant path; mocks do not supply
  authorization.
- Requirements 5–6: execute authorized provisioning/removal and recovery,
  inspect effective configuration/monitoring, and check logs/public artifacts
  for leaked credentials or personal data.
- Requirement 7: human acceptance of the real client experience and current
  public instructions, including accurate relay-visibility claims, followed
  by approved cohort opening and verification.

### Additional implementation verification

- Reuse provider-replacement and transport/auth evidence from 030/040/140 and
  `tasks/20260610-mobile-message-refresh-performance/050-plain-http-bridge-large-payload-path.md`;
  preserve HTTP product behavior and explicit legacy diagnostics.
- Verify local/static-token profiles remain usable with hosted auth disabled.
- Verify retirement/recovery follows the selected data and credential policy
  and does not silently reactivate expired/revoked access.
# Add The AWS Email Waitlist And Integrate The Form

Parent Task:
`tasks/20260930-homepage-getting-started-and-waitlist/000-main.md`

Depends On:
`tasks/20260930-homepage-getting-started-and-waitlist/019-publishable-homepage-ui-walkthrough.md`

Task Paused By:
`tasks/20261024-production-staging-website-channels.md`

Deploy a small AWS service that accepts mobile-release waitlist email
submissions, stores minimal consent evidence safely, sends a confirmation
through Amazon SES, handles withdrawal and delivery suppression, and adds the
actual working form to the homepage mobile-download step.

## Requirements checklist

- [ ] The approved homepage integration slot becomes an accessible email form
      only after a real deployed endpoint and tested contract exist.
- [ ] The form collects only a normalized email address, required consent
      evidence, and a non-personal consent-text version; it does not collect
      names, company, free-form profile data, IP addresses, or user-agent data.
- [ ] A dedicated AWS HTTPS endpoint validates requests, rejects malformed,
      oversized, automated-honeypot, or throttled submissions, and handles
      duplicate addresses idempotently.
- [ ] Records are stored in a non-public encrypted DynamoDB table with
      least-privilege access and without raw email values in logs.
- [ ] Amazon SES sends a plain confirmation message identifying the purpose,
      privacy route, and withdrawal method without tracking pixels.
- [ ] A recipient can withdraw through an opaque token flow, and withdrawn,
      bounced, or complained addresses are excluded from active-list export.
- [ ] SES bounce and complaint notifications update suppression state or
      produce an equivalent bounded operator-visible outcome.
- [ ] Authenticated operator commands support exporting the active list and
      deleting one address without exposing a public read/admin API.
- [ ] The public privacy policy explains the waitlist purpose, fields,
      processor/storage location, retention, withdrawal/deletion route, and
      contact path in approved language.
- [ ] No browser bundle, repository file, workflow log, Lambda log, API
      response, or public object contains an email-list export, AWS secret, raw
      confirmation/withdrawal token, or private AWS account configuration.
- [ ] AWS and website production deployment require explicit human approval
      and are followed by a real public-path signup, confirmation, storage,
      withdrawal, and production-page verification.
- [ ] The initial service does not implement bulk campaigns, segmentation,
      custom tracking, a public admin UI, or unrelated customer-profile data.

## Coordination and execution boundary

- **User instruction, October 5, 2026:** Nothing remaining in `015` or `018`
  blocks planning or execution of this task. Their completion is not a
  dependency of the service or form implementation.
- `tasks/20260930-homepage-getting-started-and-waitlist/015-homepage-content-assets-layout.md`
  owns homepage content and layout.
- `tasks/20260930-homepage-getting-started-and-waitlist/018-homepage-visuals-product-improvements.md`
  owns product changes and proof assets. Do not change its pending work,
  merge product changes, promote captures, or resolve visual decisions here.
- Work in the existing `main` worktree. Preserve concurrent changes.
  Coordinate edits to the mobile step in `home.yaml` with the other agent;
  keep the form in its own component.
- This pass is planning only. Plan approval permits local implementation and
  credential-free verification; AWS mutations, actual test email sending,
  commits/pushes, and production publication require their explicit gates.
- **Public handoff boundary, October 6, 2026:** Keep this task self-contained
  and suitable for a public repository. Include public sender/domain/region
  values and authenticated AWS discovery commands only. Exclude personal
  addresses, machine-specific paths, local profile names, account IDs,
  private resource identifiers, credentials, and references or copied content
  from other repositories.
- Final website publication reviews the actual integrated homepage, including
  concurrent changes. This release gate does not prevent building the service
  or testing the form now.
- The waitlist backend/form plan remains valid, but implementation, website
  integration, and publication are paused while
  `tasks/20261024-production-staging-website-channels.md` establishes separate
  production and staging variants. Resume only after the target production
  content source and dual deployment workflow are approved.

Coordinates With:
`tasks/20260825-crystal-lattice-product-positioning-and-website/030-release-safe-early-user-website.md`

## Approved shared publication checkpoint — October 7, 2026

Website 030 owns the three-table compatibility catalogue, integrated content
acceptance and live website checks. Homepage task 019 owns the accepted
first-user homepage and selected visual proof. This task retains the
service/form and single integrated website publishing push.

Before the publishing step, obtain 030's accepted content candidate as well as
this task's verified backend/form and approved privacy policy. 030 need not be
marked done at that point: its live checks follow this same push. Afterward,
run this task's production signup/receipt/withdrawal checks and 030's public
website checks against the identical artifact, then record both outcomes.

There is no mutual whole-task completion dependency. Final content readiness
does not gate service/form implementation or isolated deployed-API tests.
The approved checkpoint does not resolve pending data-policy decisions or
authorize AWS mutations, email sending, commits/pushes or publication.

## Human decisions and actions required

The sender and SES region are already selected by the user. Remaining
recommendations are proposals, not approved requirements or policies; resolve
those material decisions before dependent implementation.

| Decision | Recommendation | Why it needs a human decision |
|---|---|---|
| SES sending — selected by the user | Reuse `support@dynamicprogrammingsolutions.com` through SES in `us-west-2` (Oregon); use the same address for replies | No new sender, mailbox, domain identity, or production-access request is planned. Recheck effective identity/authentication before attaching the waitlist's configuration set. |
| Waitlist service and storage region | `us-west-2` for API, Lambda, DynamoDB, and SNS as well | Keeps one regional stack. Approval must explicitly accept Oregon storage and email processing rather than the earlier Ireland proposal. |
| Consent and confirmation | The exact proposed wording below; consent version `mobile-release-v1` | Defines the purpose for which addresses may be used. |
| Retention | Active records expire at the earlier of 12 months after signup or 30 days after the mobile launch announcement. Withdrawal removes the readable email immediately; retain only a suppression hash/state until the same expiry. | Defines storage/deletion commitments, treatment of uncertain launch dates, and suppression duration. |
| Duplicate/suppressed addresses and mail failure | No repeat receipt after a successful send; no public reactivation of suppressed addresses; recovery rules below | Determines public behavior, email-abuse exposure, and possible ambiguous delivery. |
| Integration | Use the current mobile-download slot, proposed form states, and a separate withdrawal route | Approves the form/API and withdrawal contracts without reopening homepage layout. |

Separate actions during execution:

- **AGENT:** Recheck SES production access and sender verification in
  `us-west-2` using authorized AWS credentials. Production access is already
  enabled in the inspected account; do not request it again by default.
- **HUMAN — CONDITIONAL:** If explicit support-address verification is
  required for configuration-set sending, approve resending that verification
  and complete its mailbox link. Domain verification for ordinary sending
  does not by itself prove configuration-set sending is ready.
- **HUMAN — MANDATORY:** Choose a controlled recipient mailbox for test
  signup/confirmation/withdrawal and authorize sending to it. Provide the
  address through local test configuration, not a tracked file.
- **AGENT + HUMAN:** Verify the existing identity/DKIM status. Propose a
  change only if it is actually needed, and obtain explicit approval before
  changing shared SES identity or DNS settings. Do not recreate the domain
  or overwrite existing mail records.
- **HUMAN JUDGMENT:** Approve a concrete AWS change summary before deployment,
  then review the real confirmation and integrated form preview.
- **HUMAN — MANDATORY:** Approve final website production publication. A
  landing-page push automatically starts the existing deployment workflow.
- **HUMAN — MANDATORY:** Authorize any permanent record deletion, teardown, or
  retention purge after reviewing the affected data scope. No list data is
  printed in a permission request.

### Proposed public wording

Form label: **Email address**

Required unchecked consent checkbox:

> Email me when the Crystal Lattice mobile apps become publicly available.
> I can withdraw at any time.

Place a visible **Privacy policy** link beside the consent text.

Submit label: **Join the mobile release waitlist**

Accepted state:

> Thanks. If this address is eligible, we’ll email a receipt with a withdrawal
> link.

Confirmation subject:

> You joined the Crystal Lattice mobile release waitlist

Plain-text message:

> You asked to be notified when the Crystal Lattice mobile apps become
> publicly available. Your address has been added to the mobile release
> waitlist.
>
> This is a receipt, not an email-verification step. No further action is
> needed.
>
> Withdraw from the waitlist: [recipient-only withdrawal link]
>
> Privacy policy: https://crystallattice.dev/privacy/
>
> If you did not request this, withdraw using the link above or contact
> support@dynamicprogrammingsolutions.com.
>
> Dynamic Programming Solutions Kft.

The message must not imply double opt-in or add general product marketing.
Final privacy wording must name the approved region, retention period,
controller/contact, and AWS/SES processing accurately. Draft it during
implementation; do not publish a policy for an undeployed service.

## Supporting facts and research

### Repository inspection — October 5, 2026

- The homepage already has `get-mobile`, a `mobile-download` step, a typed
  `waitlist` field, and a disabled `[data-waitlist-slot]` in
  `GettingStarted.astro`. The current contract renders no form or email input.
- Current content/browser tests explicitly assert the disabled slot. This
  task owns updating those assertions when the real form is integrated.
- No waitlist deployment package, SES application, signup endpoint, or
  list-storage implementation was found under the relevant deployment and
  landing sources.
- The static-site workflow builds Astro and docs, uses the existing
  `production-sites` environment and AWS OIDC role, and deploys on pushes
  touching `landing_page/**`. It has no waitlist endpoint variable yet.
- The public privacy source is
  `landing_page/src/content/markdown/privacy.md`; the existing contact is
  `support@dynamicprogrammingsolutions.com`. It describes website analytics
  separately from app data and needs an explicit waitlist section.
- There are pending `015`/`018` website changes in the `main` worktree.
  Planning did not modify or commit them.

### Existing SES sending and read-only AWS inspection — October 6, 2026

- The selected receipt sender is `support@dynamicprogrammingsolutions.com`;
  the selected SES region is `us-west-2`. Existing ordinary sending uses the
  SES `SendEmail` API with no explicit configuration set or Reply-To.
- Read-only inspection using authenticated operator credentials found:
  - `ProductionAccessEnabled = true` and `SendingEnabled = true`;
  - `dynamicprogrammingsolutions.com` is verified for sending;
  - the separate `support@dynamicprogrammingsolutions.com` email identity
    reports failed verification;
  - DKIM is enabled but reports failed verification;
  - all three current SES DKIM CNAMEs resolve to their expected targets;
  - no default identity configuration set, SES configuration sets, or
    bounce/complaint SNS destinations are configured in the inspected region;
  - feedback forwarding is enabled, and no account suppression settings are
    returned.
- Ordinary sending may inherit the verified domain identity. SES documents
  explicit email-address verification for advanced sending, including use
  with configuration sets. The waitlist needs this preflight; do not treat
  either the failed address status as proof all existing sending is broken
  or the verified domain as proof that event publishing is ready.
- The reason for the failed DKIM state is not established. Recheck provider
  status and effective signing before deployment; the matching DNS records
  do not justify blindly replacing DNS or generating new DKIM tokens.
- Do not assume a credential file or a locally named profile identifies the
  correct account. Resolve the selected identity under current authorized
  credentials, compare the intended sending account privately, and discover
  its ARN for IAM at deploy time. Never write account IDs, ARNs, credentials,
  or local configuration history into this task.
- These checks did not create resources, change DNS, request production
  access, send mail, or change existing delivery behavior.

Reproduce the non-sensitive account/identity checks after setting
`AWS_PROFILE` locally to an authorized operator profile. The task does not
prescribe or record the profile's local name:

```bash
aws --profile "$AWS_PROFILE" --region us-west-2 sesv2 get-account \
  --query '{ProductionAccessEnabled:ProductionAccessEnabled,SendingEnabled:SendingEnabled,SendQuota:SendQuota,SuppressionAttributes:SuppressionAttributes}'

aws --profile "$AWS_PROFILE" --region us-west-2 sesv2 get-email-identity \
  --email-identity dynamicprogrammingsolutions.com \
  --query '{VerificationStatus:VerificationStatus,VerifiedForSendingStatus:VerifiedForSendingStatus,DkimStatus:DkimAttributes.Status,ConfigurationSetName:ConfigurationSetName}'

aws --profile "$AWS_PROFILE" --region us-west-2 sesv2 get-email-identity \
  --email-identity support@dynamicprogrammingsolutions.com \
  --query '{VerificationStatus:VerificationStatus,VerifiedForSendingStatus:VerifiedForSendingStatus,DkimStatus:DkimAttributes.Status,ConfigurationSetName:ConfigurationSetName}'

aws --profile "$AWS_PROFILE" --region us-west-2 sesv2 list-configuration-sets
```

Inspect resource identifiers privately when needed for deployment. Do not
paste complete AWS responses or private diagnostic exports into this task.

### Service facts and limits to verify during implementation

- SES identities, sandbox status, and production access are region-specific.
  Sandbox testing uses verified controlled recipients or the SES mailbox
  simulator; arbitrary public recipients require production access.
- DynamoDB encryption at rest is the initial storage protection. A custom
  KMS key or application-level encryption is not required by the existing
  task; neither removes the need for restricted operator access.
- API Gateway throttling is best effort, so CORS, throttling, and a honeypot
  alone cannot prove absence of email bombing or bounded cost.
- DynamoDB TTL is asynchronous cleanup. Expiry must immediately exclude a
  record from sending/export; an explicit purge verifies permanent deletion
  when the approved retention deadline requires it.
- Provider transport necessarily processes request routing information and
  recipient addresses. The collection constraint concerns application
  records, exports, and logs; do not promise that AWS never transiently
  processes an IP or a recipient.
- The recipient-only token necessarily travels in the email and the
  withdrawal request. It must never appear in public static content, build
  assets, logs, analytics, exports, or API responses. Browser handling is
  transient and only on the recipient's withdrawal page.
- Withdrawal and suppression must remain terminal for ordinary signup
  retries. A late mail-send result or delayed SES event must not recreate a
  deleted record or reactivate a withdrawn recipient.
- Official AWS documentation confirms regional identity/access behavior,
  domain-verification inheritance and advanced-sending limitations,
  best-effort HTTP API throttling, delayed DynamoDB TTL cleanup, and SES
  configuration-set publishing to SNS. Account findings above come from
  the actual AWS API, not assumed defaults. References:
  - https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html
  - https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dkim.html
  - https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html
  - https://docs.aws.amazon.com/ses/latest/dg/monitor-using-event-publishing.html
  - https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-throttling.html
  - https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html

## Execution plan

Status: Draft

### Design and ownership

Implement one small deployment package, `deploy/aws-waitlist/`, with a
CloudFormation template, Python Lambda handlers, tests, deploy/inspect scripts,
operator commands, and README. Send through SES in `us-west-2` from
`support@dynamicprogrammingsolutions.com`. Recommend the same region for the
whole waitlist stack, subject to explicit data-location approval. Use an
authorized operator profile without embedding account-specific values.
The serverless package owns validation, storage, sending, withdrawal,
suppression, retention, and operator access. The landing package owns authored
copy, form rendering, its small browser client, and the withdrawal page.

```text
homepage step 5 -> HTTPS HTTP API -> signup/withdrawal Lambda
                                       |-> private DynamoDB table
                                       |-> SES receipt + configuration set
SES bounce/complaint -> SNS -> suppression Lambda -> same table
local authenticated operator -> export / delete / expiry purge
```

Use API Gateway's generated HTTPS hostname initially. A custom API domain,
certificate, dedicated CloudFront distribution, VPC, queue, CAPTCHA, WAF,
custom KMS key, and bulk-mail service are not initial deliverables. Use
standard SDK role credentials; no browser or Lambda static AWS keys.

CloudFormation owns only the new waitlist resources: its configuration set,
SNS topic, table/index, Lambda roles/functions/permissions, API routes,
throttling, and bounded operational metrics. Reference the existing sending
identity; do not import, recreate, or take ownership of shared SES identities
or DNS records.

The new configuration set is selected explicitly on waitlist `SendEmail`
requests. Its bounce/complaint destination affects those messages only.
Do not set it as the shared identity default, redirect existing feedback
forwarding, change account-wide suppression, or alter existing sending quotas.
Application suppression remains authoritative for waitlist exports/sending;
any SES suppression override is scoped to the waitlist configuration set.

The Lambda uses its own narrowly scoped execution role and the ordinary SDK
credential chain, not copied static access keys. Discover the existing
identity ARN under the deployment credentials and restrict sending to
`support@dynamicprogrammingsolutions.com`. Keep account/resource identifiers
in deployment inputs and private outputs.

Confirm exact resource support against official documentation before coding.
Any actual sender-verification or DKIM repair is a separately reviewed change
to the existing setup. Preserve MX/SPF/DMARC and existing DKIM records unless
the approved fix specifically needs them changed.

Initially deploy infrastructure from a reviewed local command using the
existing AWS deployment opt-in pattern. Do not add a new infrastructure CI
workflow or broaden the static-site deploy role. Add only the public API
base URL to the existing static-site build configuration.

### Proposed API and persisted contract

The public surface is exactly:

| Route | Request | Result |
|---|---|---|
| `POST /waitlist` | `email`, `consent: true`, current `consentVersion`, empty `website` honeypot | Generic accepted result, bounded validation error, or retryable service/throttle error |
| `POST /waitlist/unsubscribe` | Recipient's opaque `token` | Generic withdrawal result without returning an address or record |

Proposed validation: JSON only, at most 2 KiB after decoding, no unknown keys,
trim surrounding whitespace, normalize the supported ordinary email syntax
consistently, limit to 254 characters, and require current explicit consent.
Do not implement provider-specific alias removal or infer that two different
addresses belong to one person. Document any unsupported internationalized or
quoted-mailbox syntax before approval of the final contract.

Select exact status/error codes and normalization rules in the reviewed
contract before tests or frontend behavior depend on them. Responses never
distinguish a new address from active, withdrawn, bounced, or complained.
Honeypot handling cannot send mail or write a recipient record.

One private on-demand DynamoDB table holds:

- normalized email hash key and readable email while active;
- status: `active`, `withdrawn`, `bounced`, or `complained`;
- consent version and signup/updated timestamps;
- approved expiry timestamp;
- hashed withdrawal token and an index for lookup by that hash;
- bounded confirmation state, attempt/lease time, and sent time needed for
  duplicate/concurrent sending control;
- bounded suppression type/time where applicable.

Use SHA-256 for normalized-email deduplication, but treat hashes as restricted
data, not anonymized information. Generate at least 256 random token bits;
persist only the token hash. Operational rate counters, if used, contain no
recipient, IP, user-agent, or other identifying fields and are excluded from
operator recipient exports.

### Sending, duplicates, and failures

Submission activates the record immediately; the receipt is not an
activation link. Keep this existing task boundary.

Conditional writes create a single record. An atomic send claim prevents
concurrent requests from sending two receipts. Successful sending marks the
confirmation complete; duplicates do not resend, rotate a valid token,
update consent evidence, or extend retention.

Storage and SES are not one transaction. Distinguish:

1. Storage fails: no SES send, return a retryable error.
2. SES definitely rejects before accepting the message: preserve bounded
   failure state, return a retryable result; a later eligible attempt after
   cooldown may claim sending and create a replacement token.
3. SES accepts: persist the send result; later ordinary duplicates do not
   send again.
4. Delivery is ambiguous, or SES accepted but recording the result fails:
   record/emit only a bounded diagnostic where possible; do not automatically
   resend after an expired lease. Operator recovery must inspect the state
   and explicitly authorize any resend.

The fourth case prevents an automatic email-bomb loop at the cost of possible
manual recovery. Approval must accept this tradeoff. Never claim exactly-once
email delivery. Do not add an encrypted token outbox or queue solely to hide
this limitation.

Proposed initial resend cooldown is 24 hours for definitely failed eligible
attempts. Global send-attempt limits and Lambda concurrency must bound cost
independently of best-effort gateway throttling, without persisting IPs.
Before deployment, propose concrete daily/rate limits from expected traffic
and inspected SES quota, and obtain human approval of the capacity tradeoff.

Only the existing selected SES identity and the waitlist configuration set
can be used by the signup Lambda. Send as
`Crystal Lattice <support@dynamicprogrammingsolutions.com>` and set replies
to the same address. Disable open/click tracking. Do not log SES request
bodies, addresses, tokens, or raw exception/event objects.

### Withdrawal, suppression, retention, and operations

The email links to `/waitlist/withdraw/#<opaque-token>`. Fragments avoid
putting the token in the server request URL. The dedicated page has no
analytics or third-party content, uses a no-referrer policy, removes the
fragment from browser history immediately, keeps the token only in memory,
and submits it only after the user chooses **Withdraw**.

Opening a link performs no state change; mail-scanner GET requests must not
unsubscribe. The API hashes the submitted token, finds its private record,
and conditionally suppresses it. Repeating withdrawal cannot reactivate or
send. Define expired/invalid-token wording in the contract without exposing
an email. A support contact covers missing-link/manual deletion requests.

The separate SNS handler accepts SES notifications only through a
topic-scoped Lambda permission; the public API cannot submit suppression
events. Handle SES bounce/complaint fixtures and repeated/out-of-order events
idempotently. Do not recreate unknown/deleted records. A complaint cannot
be undone by a later bounce or confirmation completion.

On withdrawal or suppression, remove the readable address and retain only
the deduplication/suppression state, timestamps, and any hashed token needed
for idempotence until approved expiry. State transitions and sends always
exclude expired or suppressed records.

Operator commands require an explicit authenticated profile/region:

- status: aggregate counts, no address output;
- export: only unexpired active readable addresses, to a selected private
  file outside the repository with mode 0600;
- delete: read the selected address from a protected local prompt/input,
  show bounded target/count information, obtain deletion confirmation;
- purge expired: preview affected counts, obtain authorization, delete, and
  verify completion;
- retire list: after the approved launch period, preview and authorize the
  final purge, including suppression hashes.

Do not create a permanent operator resend feature in the first release.
Document an intentional, reviewed recovery procedure for ambiguous send
states. Prevent shell-history/process-list exposure of recipient arguments.

Table retention on stack deletion and bounded CloudWatch log retention must
be explicit. Recommend retaining the table on teardown with no routine
personal-data backup initially; backups complicate promised deletion. If
backup/PITR is selected, disclose its actual retention and restore handling
before production. No automatic destructive down script.

### Form and website integration

`GettingStarted.astro` renders a small independent `WaitlistForm.astro` in the
existing mobile slot. Authored consent/labels belong in maintained content,
not duplicated browser strings. Preserve store-coming-soon controls and
verified CLI/Desktop links.

Add `PUBLIC_CRYSTAL_LATTICE_WAITLIST_API_URL` to the website build. It is a
public generated HTTPS endpoint, not a credential. During development with
no configured endpoint, preserve the disabled slot. Once the slot is marked
active, missing/invalid endpoint configuration must fail the production build
rather than ship a collecting form with no backend.

The form uses a labeled email input, unchecked required consent checkbox,
privacy link, noninteractive honeypot, keyboard submit, bounded error
messages, and a live status region. Sending disables duplicate submission
and announces progress; errors permit a retry. Clear the email input after
accepted submission. Do not persist it in browser storage, URLs, analytics,
DOM attributes, or console output.

Use a small production browser client shared with the integration tests,
not a mocked replacement. Catch transient failures without reflecting raw
server details. Do not show a fake success if networking or consent fails.
The withdrawal page uses the same API base configuration but no tracking.

Only enable real form rendering after the deployed contract is verified.
Local request mocks may prove visual/error states; they never prove
deployed storage or email delivery.

### Ordered execution and approval stops

1. **HUMAN JUDGMENT:** Approve the draft plan, Oregon data-location
   recommendation, wording, retention, and failure/reactivation policy.
   Sender and SES region are already selected. Implementation waits.
2. **AGENT:** Recheck concurrent integration changes and approved public
   contract; implement package, frontend client contract, unit tests, and
   template/build validation locally. No deployment or email sending.
3. **AGENT:** Recheck the selected account's SES identity, DKIM, quota and
   IAM. Prepare the exact new-resource CloudFormation diff, capacity proposal,
   deletion/backup behavior, costs/resources, and commands. Propose any
   shared-identity/DNS correction separately only if the checks require it.
4. **HUMAN JUDGMENT:** Approve those AWS changes and controlled test-email
   use. **HUMAN — CONDITIONAL:** Complete explicit support-address
   verification if configuration-set sending requires it. SES production
   access is already enabled; request it only if a later authorized account
   check contradicts that result.
5. **AGENT:** Deploy the approved waitlist resources and only separately
   authorized identity/DNS corrections. Verify sender authentication, routes,
   policy scopes, table encryption, notification permissions, and generated
   endpoint. Verify existing identity defaults/feedback settings are
   unchanged; stop if unexpected account or DNS conflicts appear.
6. **AGENT + HUMAN:** Exercise signup and withdrawal through public HTTPS,
   inspect the same record privately, receive/review the receipt, and test
   suppression using the SES mailbox simulator. Suppression cannot remain a
   skipped “where practical” test.
7. **AGENT:** Integrate the real form and withdrawal page; update privacy,
   build variable wiring, docs, and changed slot assertions. Reconcile only
   the owned mobile-step hunks with `015`/`018`.
8. **AGENT:** Run the public-backend browser integration and isolated local
   preview at phone/desktop widths. Keep artifacts/screenshots free of
   recipient data and tokens.
9. **HUMAN JUDGMENT:** Review confirmation, consent/privacy text, capacity
   behavior, withdrawal, and actual integrated page. Confirm SES production
   access and sender verification are complete. Require website 030's accepted
   content candidate with task 019's selected visual proof, three compatibility
   tables and reviewed launch positioning; do not require its post-publication
   checks to be complete before this push.
10. **HUMAN — MANDATORY:** Authorize the specific commit/push and production
    website publication, including concurrent homepage changes in that
    release. Do not push during the earlier local review.
11. **AGENT:** Set the approved non-secret endpoint variable, publish through
    the existing site workflow once, and run the decisive production browser
    flow. Coordinate 030's live page/asset/table checks on the same artifact.
12. **AGENT + HUMAN:** Authorize and delete controlled test records; verify
    active export exclusion and no remaining test PII in application logs,
    artifacts, or exports. Record evidence and unresolved items in this task
    and keep the parent status current.

### Implementation decisions and open questions

Preserved scope: immediate activation; confirmation receipt only; minimal
email/consent data; encrypted DynamoDB; SES; opaque hashed withdrawal token;
no public administration, bulk campaigns, tracking, or extra profile data.

Approved publication ownership: this task owns the single integrated push;
website 030 supplies content acceptance before it and public checks after it.
Backend work remains independent of that publishing-stage gate.

Selected by the user on October 6, 2026: reuse
`support@dynamicprogrammingsolutions.com` through SES in `us-west-2`.
No new sender/domain identity or routine SES production-access request.

Recommendations awaiting approval:

- The entire waitlist stack in `us-west-2` (Oregon), with the corresponding
  US data-location disclosure, `mobile-release-v1` copy, and retention proposal.
- Separate topic-only suppression handler, generated API hostname, no new
  infrastructure CI role, ordinary one-table conditional state transitions.
- No silent public reactivation and no automatic retry after ambiguous
  SES acceptance; failed known sends alone use a 24-hour cooldown.
- Fragment-token withdrawal page with explicit user action and no analytics.
- Table retained on teardown; no routine data backup for this small list.

Resolve before dependent implementation: exact email normalization,
status/error codes, and permitted-origin list. Recommend production origin
`https://crystallattice.dev` only; add a temporary isolated preview origin
solely for the approved deployed browser test and remove it afterward.
Never allow wildcard, `null`, or arbitrary reflected origins.

Resolve before deployment: concrete rate/daily caps, Lambda concurrency,
recipient choice, effective sender verification for configuration-set
sending, and the DKIM status mismatch. Verify the intended account using
current authorized credentials. Production access is a read-only preflight,
not an unconditionally required account-owner action. These checks do not
block credential-free implementation after plan approval.

If the user chooses double opt-in, bulk launch sending, public rejoin, or a
different collection/retention policy, ask about the requirement change and
revise this Draft before implementing that behavior.

### Documentation

- `deploy/aws-waitlist/README.md`: service contract, minimal fields, region,
  existing-identity discovery/verification, DKIM preflight, limits, exact
  commands, deployment gates,
  suppression, controlled public tests, private export/delete, retention,
  ambiguous-mail recovery, and safe rollback/teardown.
- `landing_page/README.md` and current content-system docs: endpoint build
  variable, disabled-to-active slot, production client, isolated preview,
  withdrawal privacy, and integration verification.
- Public privacy source: approved purpose/consent, controller/contact,
  fields, AWS/SES/region, retention and backups if selected, withdrawal and
  deletion. Update the policy effective date when this behavior goes live.
- Use the existing page/index structure; no new cross-project specification
  or placeholder documentation tree. Keep operational account configuration
  out of public docs and generated assets.

### Task checklist

- [ ] **HUMAN JUDGMENT:** Approve the plan and material selections above.
- [ ] **AGENT:** Finalize the approved API/state contract and local package.
- [ ] **AGENT:** Implement/test validation, state transitions, SES failure
      boundaries, withdrawal, suppression, retention, and private operations.
- [ ] **AGENT:** Validate templates and prepare reviewed AWS/capacity diff;
      propose identity/DNS fixes separately only when actually needed.
- [ ] **HUMAN — MANDATORY:** Approve AWS mutations and test recipients/sending.
- [ ] **AGENT:** Recheck existing SES production access in `us-west-2`.
- [ ] **AGENT + HUMAN if needed:** Resolve explicit sender verification and
      DKIM preflight; complete a mailbox verification link only if required.
- [ ] **AGENT:** Deploy and verify sender, API, table, IAM, and SES/SNS path.
- [ ] **AGENT + HUMAN:** Receive and review real receipt; pass public API and
      simulator suppression checks.
- [ ] **AGENT:** Integrate the real form/withdrawal client and approved copy.
- [ ] **AGENT:** Update privacy, landing, deployment, and operation docs.
- [ ] **AGENT:** Pass isolated browser tests against the deployed API.
- [ ] **HUMAN JUDGMENT:** Approve final integrated website and privacy copy.
- [ ] **AGENT + HUMAN:** Confirm website 030's accepted complete content
      candidate at the publishing checkpoint.
- [ ] **HUMAN — MANDATORY:** Approve commit/push and production publication.
- [ ] **AGENT:** Publish and verify the production browser/email/data flow.
- [ ] **AGENT:** Record the same publishing artifact and coordinate website
      030's live checks.
- [ ] **AGENT + HUMAN:** Authorize cleanup; verify private test-record removal.
- [ ] **AGENT:** Record completion evidence and update parent status.

### Requirement verification

| Requirements | Decisive evidence |
|---|---|
| Real accessible form, HTTPS API, validation and idempotence | `WAITLIST_PUBLIC_TEST=1 PLAYWRIGHT_PORT=4186 PLAYWRIGHT_REUSE_EXISTING_SERVER=false yarn --cwd landing_page playwright test tests/visual/waitlist-public.spec.mjs --config=playwright.waitlist.config.mjs` with stack outputs and protected controlled-recipient config. Isolated preview renders the production component/client and posts to the deployed API. The same transaction is inspected privately in DynamoDB. Repeat/concurrent submission yields one record and bounded sending. |
| Minimal collection, encrypted private storage, restricted access | Inspect actual table/index schema, encryption, Lambda/operator IAM and API route surface; inspect the controlled signup record privately. No public read/admin routes. Tests prove exact stored field set and absence of IP/user-agent/profiles. |
| Receipt purpose, consent, privacy, withdrawal, no tracking | Actual recipient inbox inspection, approved human wording review, SES response/event evidence, and raw-message inspection kept outside repo/artifacts. A mock mail client or accepted SES send alone does not prove receipt. |
| Withdrawal, suppression, export exclusion | Use the received fragment link and real withdrawal page/client against public API; inspect suppressed state and privately verify export exclusion. Signup retries/late events cannot reactivate it. SES mailbox-simulator bounce and complaint traverse SES configuration set -> SNS -> deployed handler -> stored state. |
| Private operator export/delete and retention | Authenticated commands prove 0600 external output, only active/unexpired records, and confirmed deletion/purge. Clock-controlled tests prove expiry exclusion before delayed TTL cleanup. Test address values do not appear in command logs or output. |
| Accurate privacy and no exposure | Human policy approval plus built HTML/client inspection; actual log/config review with bounded metrics; browser request and analytics inspection. Token appears only in recipient email/in-memory withdrawal request, never static assets, responses, access logs or analytics. |
| Explicit deployment approvals and full production path | Record the concrete approvals and workflow result. Repeat the same browser integration with `WAITLIST_SITE_URL=https://crystallattice.dev`, no local server reuse, and controlled mailbox config; verify receipt, storage, public withdrawal and private export exclusion, then approved cleanup. |
| Scope exclusions | Inspect public routes, data schema, SES configuration, UI and operator surface for absence of profile fields, campaigns, segmentation, tracking or a public admin UI. |

The public test file and `playwright.waitlist.config.mjs` above are planned
interfaces to implement. Its dedicated config selects the isolated local
production build or `WAITLIST_SITE_URL` for the actual production page and
disables PII-bearing screenshots/traces/error artifacts. Share the existing
visual-config port conventions without changing unrelated visual tests.
Store exact working invocation and gate names during implementation. No
unavailable harness or skipped gate counts as decisive evidence.

The public suite owns the entire form -> API -> table -> receipt -> withdrawal
connection. Deterministic local HTTP/SNS fixtures support failure testing, but
do not replace deployed evidence. Production access in `us-west-2` is already
enabled and must be rechecked, along with sender authentication, before
sending. Use disposable controlled test records; never scan or export real
recipients to prove a test.

### Additional implementation verification

- Cover malformed JSON, unknown keys, body bounds including decoded payloads,
  required consent/version, supported address normalization, honeypot and
  throttled requests without invoking SES.
- Cover parallel send claims, known reject/retry, ambiguous send, failure
  after SES acceptance, suppression during send, stale events and delete races.
- Verify scanner GETs cannot mutate state, repeated/unknown withdrawal is
  bounded, token fragments are removed before analytics could run, and no
  recipient input persists in browser storage or error reporting.
- Exercise SNS source permissions and real event schema; use synthetic
  recipient data only in deterministic fixtures.
- Verify waitlist messages select their configuration set and that the
  existing identity default, feedback forwarding, account-wide suppression,
  and shared sending behavior are unchanged. Inspect real receipt headers for
  effective sender authentication without publishing private message data.
- Verify aggregate limit behavior without persisting source IPs. Never load
  test public SES with uncontrolled recipients.
- Run content/analytics tests, warning-free Astro build, owned backend tests,
  relevant workflow security validation, shell/template checks, and isolated
  320/390/768/1440-pixel keyboard/browser checks. Preserve existing previews.
- Inspect the final change set before any commit: concurrent `015`/`018`
  changes require their own review; do not stage them automatically.
- Inspect the task and maintained sources for personal addresses,
  machine-specific paths, local profile names, private AWS identifiers,
  credentials, and references/content from other repositories. Public
  sender/domain/region and authenticated discovery commands are permitted.
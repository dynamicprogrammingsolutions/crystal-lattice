# Add The AWS Email Waitlist And Integrate The Form

Parent Task:
`tasks/20260930-homepage-getting-started-and-waitlist/000-main.md`

Depends On:
`tasks/20260930-homepage-getting-started-and-waitlist/019-publishable-homepage-ui-walkthrough.md`

Deploy a small AWS service that accepts mobile-release waitlist email
submissions, stores minimal consent evidence safely, sends a confirmation
through Amazon SES, handles withdrawal and delivery suppression, and adds the
actual working form to the approved homepage mobile-download step.

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

## Human decisions and actions required

- **HUMAN JUDGMENT:** Approve the sender address. Recommendation:
  `updates@crystallattice.dev`.
- **HUMAN JUDGMENT:** Approve the exact consent and confirmation copy.
- **HUMAN JUDGMENT:** Approve the retention/deletion rule. Recommendation:
  retain active records until public mobile launch or withdrawal, then delete
  the list after the announced launch-notification period.
- **HUMAN — MANDATORY:** If the selected SES region is sandboxed, request
  production access through the AWS account.
- **AGENT + HUMAN:** Verify or create the SES domain identity and DNS records.
  The agent may prepare and inspect infrastructure; account-owner action is
  required wherever AWS policy or account access prevents safe automation.
- **HUMAN — MANDATORY:** Approve the production AWS deployment and final
  website publication.

## Supporting facts and boundaries

- The static Astro website cannot safely store email itself; it needs a
  bounded server-side endpoint.
- A dedicated serverless stack avoids coupling marketing PII to the bridge,
  cloud-agent orchestrator, desktop download bucket, or static-site buckets.
- DynamoDB provides encrypted-at-rest storage and conditional writes suitable
  for a small idempotent list. Application-level encryption and a
  customer-managed KMS key are optional future hardening, not initial
  requirements unless the user expands the security target.
- SES sender verification and sandbox state are region-specific and must be
  inspected in the target account rather than assumed.
- API Gateway throttling is best-effort abuse reduction, not an absolute
  capacity or security boundary. The initial service also uses strict body
  limits, normalization, conditional writes, a honeypot, and resend cooldown.
- CORS is restricted to approved website origins, but request validation and
  throttling remain mandatory because CORS is not an authentication boundary.
- Confirmation means an immediate receipt after an accepted signup. The
  record becomes active on submission. A later double-opt-in requirement would
  be a material scope change.
- Withdrawal uses an opaque random token delivered by email; only its hash is
  stored.

## Execution plan

Status: Draft

Create `deploy/aws-waitlist/` as a package-local deployment boundary with
CloudFormation, Lambda source, build/deploy scripts, outputs, smoke tests, and
operator documentation. Use `us-east-1` unless inspection finds an approved
existing SES identity in another region and the user approves changing the
region.

The initial architecture is:

```text
crystallattice.dev form
  -> API Gateway HTTP API
  -> Lambda
       -> DynamoDB waitlist table
       -> SES confirmation message

SES bounce/complaint event
  -> SNS
  -> Lambda suppression update
```

The public API contract is:

```text
POST /waitlist
POST /waitlist/unsubscribe
```

`POST /waitlist` accepts a small JSON document containing the email, consent
version, and honeypot. Lambda trims and normalizes the address, validates a
bounded email shape, rejects disallowed payload keys and body sizes, hashes
the normalized address for the partition key, and uses a conditional write.
Repeated valid submissions return the same generic accepted response and send
at most one confirmation inside the approved cooldown.

The DynamoDB record contains only:

```text
emailHash
email
status
consentVersion
createdAt
updatedAt
confirmationSentAt
withdrawalTokenHash
```

Delivery events may add bounded bounce/complaint timestamps or reasons without
storing message bodies. The active export includes only `status = active`.

The confirmation is plain text or simple static HTML with no remote tracking
resources. It explains why the message was sent, links to the privacy policy,
and provides a withdrawal action. The raw withdrawal token is generated with
a cryptographically secure random source, sent only to the recipient, and
stored only as a hash.

The browser form posts directly to the public API URL supplied as a build-time
public configuration value. It contains a labeled email input, required
consent, honeypot, submit button, loading state, generic accepted state,
bounded validation error, retryable service error, and an accessible live
status region. It never receives AWS credentials or reads list data.

Operator commands use an explicit local AWS profile to:

- export active addresses to a user-selected private path;
- inspect aggregate counts by status without listing addresses by default;
- delete one normalized address;
- resend a confirmation only through an intentional command if later needed.

No export file is written under the repository by default. Documentation must
tell operators to protect and delete exported files.

The deployment sequence is:

1. read-only inspect SES identity/sandbox and the production hosted zone;
2. approve sender, consent copy, and retention;
3. build and unit-test Lambda code;
4. validate CloudFormation without deployment;
5. receive explicit AWS deployment approval;
6. deploy the waitlist stack and verify outputs;
7. run public API tests with controlled test addresses;
8. integrate the real endpoint into the reviewed homepage;
9. update privacy and operational documentation;
10. build and preview the integrated website;
11. receive final human content/visual/publication approval;
12. push through the protected site deployment path;
13. verify production signup, SES confirmation, stored state, withdrawal, and
    public page behavior;
14. remove controlled test records.

### Implementation decisions and open questions

- Decision: use API Gateway HTTP API, Lambda, DynamoDB, SES, and SNS in a
  dedicated stack.
- Decision: submission immediately activates the waitlist record and SES
  sends a confirmation receipt; double opt-in is outside the initial scope.
- Decision: store the normalized email because future launch notification
  requires it; use the SHA-256 hash as the deduplication key.
- Decision: rely initially on DynamoDB encryption at rest, HTTPS in transit,
  least-privilege IAM, minimal fields, and no body logging rather than adding
  application-level envelope encryption.
- Decision: use route throttling, strict payload limits, honeypot,
  idempotency, and resend cooldown; do not add CAPTCHA or WAF unless observed
  abuse justifies them.
- Decision: handle bounce/complaint suppression before production acceptance.
- Decision: expose no public read, count, export, delete, or administration
  endpoint.
- Decision: the waitlist service sends confirmation only; bulk launch
  campaigns are a separate future task.
- Open human decision: sender address.
- Open human decision: exact consent and email copy.
- Open human decision: retention and post-launch deletion period.

### Documentation

- Add `deploy/aws-waitlist/README.md` covering architecture, prerequisites,
  sender identity, SES sandbox, deployment, outputs, smoke tests, operator
  export/delete, suppression, rollback, and teardown.
- Update landing-package public URL/build configuration docs for the endpoint.
- Update content-system docs for the form integration contract and accessible
  states.
- Update the public privacy policy with approved waitlist language.
- Do not document real emails, tokens, account IDs, secret values, or raw
  event payloads.

### Task checklist

- [ ] **HUMAN JUDGMENT:** Approve sender, consent/confirmation copy, and
      retention.
- [ ] **AGENT:** Add the dedicated CloudFormation/Lambda deployment package.
- [ ] **AGENT:** Implement signup validation, normalization, idempotency,
      storage, confirmation, withdrawal, and suppression handling.
- [ ] **AGENT:** Add backend unit tests, template validation, and local
      deterministic contract tests.
- [ ] **AGENT + HUMAN:** Verify SES identity and production-access state.
- [ ] **HUMAN — MANDATORY:** Approve AWS deployment.
- [ ] **AGENT:** Deploy and verify the public waitlist service.
- [ ] **AGENT:** Add the working accessible form to the reviewed homepage.
- [ ] **AGENT:** Update privacy, landing, deployment, and operations docs.
- [ ] **AGENT:** Run integrated production-like website/API verification.
- [ ] **HUMAN JUDGMENT:** Review final form behavior, copy, confirmation, and
      integrated website preview.
- [ ] **HUMAN — MANDATORY:** Approve production website publication.
- [ ] **AGENT:** Publish, verify the real production flow, and remove test
      records.

### Requirement verification

- Form/API boundary: a browser integration test using the production frontend
  adapter submits through the public HTTPS API; direct Lambda invocation is
  not decisive evidence.
- Storage boundary: authenticated inspection verifies exactly one normalized
  encrypted table record with the approved fields and no duplicate after a
  repeated submission.
- Confirmation boundary: SES delivery evidence and the received controlled
  test message confirm sender, purpose, privacy link, and withdrawal action.
- Withdrawal boundary: the controlled recipient uses the public withdrawal
  flow; DynamoDB state changes and active export excludes the address.
- Suppression boundary: deterministic SES bounce/complaint fixtures plus one
  deployed-path test where practical prove suppression updates without
  exposing email data.
- Security boundary: IAM inspection, API configuration, logs, built browser
  assets, repository scan, and public responses prove no credentials, list
  reads, raw tokens, request bodies, or email exports are exposed.
- Accessibility boundary: browser tests cover labels, required consent,
  keyboard submission, disabled/loading state, focus, generic accepted/error
  messages, and live announcements at desktop and phone widths.
- Production boundary: anonymous checks load the final homepage and submit a
  controlled address; authenticated AWS inspection and received email confirm
  the same transaction; cleanup removes the test record.

### Additional implementation verification

- Test malformed JSON, unknown keys, missing/invalid email, oversized body,
  honeypot, duplicate submission, resend cooldown, and throttling behavior.
- Verify API CORS allows only approved site origins and does not rely on CORS
  for request trust.
- Verify CloudWatch logs contain request IDs and bounded outcome categories,
  not emails, bodies, or tokens.
- Verify SES configuration publishes bounce and complaint events and that
  suppressed records cannot be exported as active.
- Verify DynamoDB deletion protection, backup/point-in-time-recovery choice,
  teardown behavior, and data-retention implications before production.
- Verify the static-site workflow receives only the public endpoint URL and no
  AWS secret.
- Verify no waitlist email address is sent to website analytics.
# Prepare Google Play Console Registration And Internal-Test Metadata

Assemble all fields, listing copy, media, test notes, and manual instructions
needed to create the Play Console app and initialize its internal-testing
release without guesswork.

## Requirements checklist

- [ ] App identity, language, type, price, category, contact, package, and
      developer fields are complete.
- [ ] Short/full descriptions and release notes accurately explain the
      self-hosted product.
- [ ] Privacy, support, and marketing URLs are ready.
- [ ] Store icon, feature graphic, and screenshot requirements are mapped to
      prepared files.
- [ ] Play App Signing and first-release choices are explicit.
- [ ] Internal-testing tester and feedback instructions are actionable.
- [ ] Reviewer/app-access instructions have an explicit readiness status and do
      not promise unavailable public infrastructure.

Parent Task: tasks/20260820-android-google-play-github-fastlane/000-main.md
Depends On: tasks/20260820-android-google-play-github-fastlane/010-play-console-preflight.md
Depends On: tasks/20260820-android-google-play-github-fastlane/030-android-branding-and-store-assets.md
Depends On: tasks/20260820-android-google-play-github-fastlane/050-google-play-privacy-and-app-content.md

## Required reading

Read the parent task's `Shared required reading`, then:

- `tasks/20260614-ios-testflight-github-fastlane/060-app-store-connect-registration-package.md`
- Outputs from Android tasks `030` and `050`
- Create/set up app:
  https://support.google.com/googleplay/android-developer/answer/9859152
- Main store listing:
  https://support.google.com/googleplay/android-developer/answer/9859152#store_listing
- Graphic assets:
  https://support.google.com/googleplay/android-developer/answer/9866151
- Testing:
  https://support.google.com/googleplay/android-developer/answer/9845334

## Proposed registration fields

| Field | Proposed value |
| --- | --- |
| App name | `Crystal Lattice Control` |
| Default language | English (United States) |
| App or game | App |
| Free or paid | Free |
| Category | Productivity |
| Package name | `com.dynamicprogrammingsolutions.crystallatticecontrolrn` |
| Developer/legal entity | Dynamic Programming Solutions Kft. |
| Contact email | `support@dynamicprogrammingsolutions.com` |
| Privacy policy | `https://crystallattice.dev/privacy` |
| Support | `https://crystallattice.dev/support` |
| Marketing | `https://crystallattice.dev/mobile` |
| First track | Internal testing |
| First version | `0.9.0` recommended |

Package name and free/paid selection become consequential Play identity choices.
Confirm them before final creation.

## Proposed listing copy

Short description:

> Connect to self-hosted Crystal Lattice agents, sessions, tools, and files.

Full description:

> Crystal Lattice Control is a mobile client for Crystal Lattice environments
> operated by you or your organization. Connect by local address, local-network
> discovery, a self-hosted bridge, or a supported self-hosted cloud connection.
> Browse sessions, continue conversations, stream responses, use
> plugin-provided actions, attach images and documents, and save or share
> generated files.
>
> Dynamic Programming Solutions Kft. does not operate a public agent service,
> production bridge, advertising network, or analytics service for the app. A
> compatible Crystal Lattice runtime is required for connected operation.

Internal release notes:

> Initial internal Android test. Verify connection setup and reconnection,
> session listing, conversations and streamed responses, plugin actions,
> attachments, generated-file save/share behavior, deep links, and recovery
> after backgrounding. Include app version, Android version, device model,
> connection method, runtime version, and redacted reproduction details in
> reports sent to support@dynamicprogrammingsolutions.com.

## First-release manual sequence

1. Create the app record in the verified organization account.
2. Accept current declarations and Play App Signing terms.
3. Save listing/contact/App content fields required for internal testing.
4. Create the internal release and upload the first signed AAB.
5. Resolve every Play blocking error; classify non-blocking warnings.
6. Add internal testers or a Google Group.
7. Publish only to the internal track.
8. Record the opt-in link.

Google Play may require initial package/App Signing setup in the Console before
API automation can manage later releases. Plan for the first release to include
manual Console steps even when subsequent AAB uploads are automated.

## Execution plan

Status: Draft

Revalidate field limits and live Console wording at execution time. Prepare a
copy/paste registration packet and exact file paths for media. The authorized
owner creates/saves permanent account state. Keep reviewer access marked
unready until task `085` supplies a usable path.

### Implementation decisions and open questions

- Recommendation: Productivity category, free app, English (United States).
- Decision: internal testing first.
- Recommendation: Google-generated Play app-signing key with company-controlled
  upload key.
- Open question: final screenshot/caption approval.
- Open question: initial tester list.
- Open question: app-access instructions pending task `085`.

### Documentation

- Store current listing copy and release instructions in package development
  documentation or fastlane metadata as appropriate.
- Keep public marketing copy consistent with current delivered behavior.

### Task checklist

- [ ] Confirm all proposed identity fields.
- [ ] Finalize short/full descriptions and internal release notes.
- [ ] Map media file paths.
- [ ] Prepare Play App Signing choices.
- [ ] Prepare tester instructions and feedback contact.
- [ ] Prepare owner step-by-step Console checklist.
- [ ] Record app-access readiness/blocker.
- [ ] Have the authorized owner create/confirm the app record.

### Requirement verification

- Registration: Play Console app dashboard matches package and identity.
- Listing: saved text, URLs, contact, and category.
- Media: accepted icon/feature graphic/screenshots where required.
- Signing: Play App Signing status and upload certificate recorded.
- Internal test: track exists with tester configuration and no production
  rollout.
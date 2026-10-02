---
label: Legal
title: Privacy Policy
meta: "Effective date: September 7, 2026"
---

## The short version

Crystal Lattice is local-first, self-hosted software. The mobile app connects to
a Crystal Lattice runtime, bridge, or cloud environment that you or your
organization operates. Dynamic Programming Solutions Kft. does not operate a
public production bridge or cloud-agent service, and the app does not send
conversations, sessions, attachments, or connection credentials to us.

You do not need a Crystal Lattice account. The app contains no advertising,
analytics, telemetry, or cross-app tracking SDKs.

The public website and documentation use a separate, privacy-minimized,
self-hosted analytics service as described below. This does not give us access
to your Crystal Lattice sessions, prompts, attachments, provider requests, or
locally stored application data.

## Controller

The controller for the public website, documentation, and support
correspondence is Dynamic Programming Solutions Kft., Nyári Pál utca 15,
2724 Újlengyel, Hungary. Privacy questions and requests can be sent to
[support@dynamicprogrammingsolutions.com](mailto:support@dynamicprogrammingsolutions.com).

## Data stored on your devices

The Crystal Lattice runtime stores session data, message history, agent
configuration, and generated files on the computer or server where you run it.
The mobile app stores information needed for app functionality on your phone,
which may include:

- Saved runtime addresses and connection names.
- Self-hosted bridge pairing tokens and self-hosted cloud connection tokens.
- Cached session summaries and message display state.
- Pinned actions, preferences, and other interface settings.

This information remains under your control on your devices and self-hosted
systems. Removing an app connection or uninstalling the app removes or makes
unavailable the corresponding local app data according to the operating
system's storage behavior.

## AI provider requests

When you run an agent session, your self-hosted Crystal Lattice runtime may send
messages, attachments, and related request data to the AI provider you
configured, such as OpenAI, Anthropic, Google Gemini, OpenRouter, or a local
model. These requests go from your runtime to that provider. They do not pass
through infrastructure operated by Dynamic Programming Solutions Kft.

Each provider has its own privacy policy, retention rules, and data-handling
practices. You are responsible for selecting and configuring the provider. If
you use a local model, model requests can remain on systems you control.

## Self-hosted bridge and cloud connections

Crystal Lattice includes optional bridge and cloud-orchestrator components that
users can self-host. A bridge relays requests between the mobile app and a
Crystal Lattice runtime. A cloud connection link can connect the app to a
self-hosted cloud-agent environment. The mobile app stores the connection
address and token required to reconnect.

Dynamic Programming Solutions Kft. does not operate a public production bridge
or cloud-agent service. The operator of a self-hosted environment controls its
security, logging, storage, retention, and access policies. Review those
policies before connecting the app.

## Photos, camera, documents, and generated files

The app requests camera, photo-library, or document access only when you choose
an action that needs it. Selected photos and documents may be copied into the
app temporarily and sent to the self-hosted runtime and AI provider you selected
as message attachments.

When you choose to save or share a generated file, the app uses the operating
system's photo-library, document-saving, or share interface. Crystal Lattice
does not receive a copy of the selected or generated file.

## Public website and documentation analytics

The public website at [crystallattice.dev](https://crystallattice.dev) and the
documentation at
[docs.crystallattice.dev](https://docs.crystallattice.dev) use a self-hosted
Umami installation to understand aggregate website use, navigation between the
two sites, documentation usage, and technical page performance. We do not send
this analytics information to Google Analytics or Umami's managed cloud
service, and we do not use it for advertising, remarketing, or cross-site
profiles.

Before transmission, a mandatory filter permits only ordinary page views and
Core Web Vitals. It removes URL query strings and fragments, advertising click
identifiers, referrer query strings, credentials and fragments, custom events,
custom session properties, and user identifiers. Session replay and heatmaps
are disabled.

The permitted information is the sanitized page address and title, sanitized
referrer domain and path, timestamp, browser language, screen dimensions, and
LCP, INP, CLS, FCP, TTFB, or page-duration measurements. Browser, operating
system, device category, and approximate location may be derived on the server
from ordinary request information. IP address and user-agent information are
processed transiently to derive approximate location and anonymous session and
visit values. Raw IP addresses are not intended to be stored in the analytics
database, and the anonymous values are not used to identify named people or
track visitors across unrelated websites.

Dynamic Programming Solutions Kft. operates Umami and its PostgreSQL database
on Amazon Web Services infrastructure in Ireland. Live analytics records are
deleted on a rolling basis after 24 months, and encrypted analytics backups are
retained for up to 35 days. Access is limited to authorized administrators.

Our legal basis is our legitimate interest in operating, evaluating, securing,
and improving the two public sites with strictly minimized first-party
analytics. The tracker respects the browser's Do Not Track setting. You can
also use the analytics preference control below to disable analytics in this
browser, or object by contacting us.

The hosting infrastructure may separately process ordinary request information
needed to deliver and secure the sites. Infrastructure processing is not used
by us for advertising profiles.

## Browser storage

The Umami baseline does not set analytics cookies or write an analytics
identifier to browser storage. It reads the `umami.disabled` preference only
when a visitor has deliberately disabled analytics. The sites may also store
functional preferences, such as the selected light or dark theme, so the
interface can remember a choice requested by the visitor.

We do not request prior consent through a popup for this strictly minimized
baseline because it does not set analytics cookies and our stated legal basis
is legitimate interest. This does not override mandatory requirements that may
apply in a particular jurisdiction. Replay, heatmaps, advertising,
remarketing, identification, or similar technologies will require a separate
assessment and policy update before activation.

## Support correspondence

If you email support, we receive the address, message, and attachments you
choose to send. We retain support correspondence as business records for
handling the request, maintaining service quality, and meeting legal
obligations. Do not include API keys, connection tokens, private conversation
content, or other secrets in a support request.

Apple, Google, GitHub, hosting providers, and other services you independently
use apply their own privacy policies to their services.

## Your rights

Subject to applicable law, you may request access, correction, deletion,
restriction, or portability of your personal data. You may object to processing
based on legitimate interests, including baseline website analytics, on grounds
relating to your situation. We will stop the relevant processing unless
applicable law permits continued processing on compelling legitimate grounds
or for legal claims.

You may also complain to the competent data-protection authority. In Hungary,
this is the Hungarian National Authority for Data Protection and Freedom of
Information (NAIH).

## Open source

The Crystal Lattice repository contains components under their respective open
source licenses. You can review what the software does by reading the source
code and license files on GitHub.

## Changes to this policy

We may update this policy if the software or services change in ways that affect
privacy. Changes will be posted to this page with an updated effective date.

## Contact

Privacy and support questions can be sent to
[support@dynamicprogrammingsolutions.com](mailto:support@dynamicprogrammingsolutions.com).
For general product help, see the [support page](/support).

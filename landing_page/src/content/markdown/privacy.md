---
label: Legal
title: Privacy Policy
meta: "Effective date: May 2025"
---

## The short version

Crystal Lattice is local-first software. It runs on your machine. Your
conversations, sessions, and agent history are stored on your own filesystem and
are never sent to us. We don't have servers that store your data. We don't have
accounts. We don't have a cloud.

## What Crystal Lattice collects

The Crystal Lattice CLI and server software collect nothing on our behalf.
Specifically:

- All session data, message history, and agent configuration is stored locally
  on your machine in the working directory you specify.
- No telemetry, analytics, or usage data is transmitted to Crystal Lattice from
  the CLI or server software.
- No account creation is required. We have no user database.

## AI provider requests

When you run an agent session, Crystal Lattice sends your messages to whichever
AI provider you have configured (OpenAI, Anthropic, Google Gemini, OpenRouter, or
a local model via Ollama). These requests go directly from your machine to the
provider's API — they do not pass through Crystal Lattice infrastructure.

Each provider has their own privacy policy and data handling practices. If you
use a local model via Ollama, no data leaves your machine at all.

## The bridge service

Crystal Lattice includes an optional bridge service that proxies HTTP requests
between your phone and your local server when they are on different networks.
The bridge relays traffic in real time — it does not store your messages,
sessions, or any conversation content. Connections are identified by a pairing
code that you generate and your server registers. The bridge retains pairing
metadata (a session ID and server registration) only as long as the server
session is active.

## This website

This website (crystallattice.dev) may collect standard web server access logs
(IP address, browser type, pages visited, referrer) for operational purposes. We
do not use third-party advertising trackers. If we add any analytics in the
future, we will update this policy.

## The mobile app

Crystal Lattice Control (the iOS and Android companion app) connects only to the
server address you provide — either a local IP, an mDNS address, or the bridge
service. The app does not transmit any data to us. It stores your server
connection preferences locally on your device.

App Store and Google Play distribution means that Apple and Google's platform
privacy policies also apply to the download and installation of the app.

## Open source

Crystal Lattice is open source under the Apache 2.0 license. You can review
exactly what the software does by reading the source code on GitHub. There are
no hidden network calls, no obfuscated telemetry, and no proprietary binary
components in the core platform.

## Changes to this policy

We may update this policy if the software or services change in ways that affect
privacy. Changes will be posted to this page with an updated effective date.

## Contact

Questions about this policy can be directed to the project via GitHub Issues or
the contact information in the repository.

---
label: Legal
title: Privacy Policy
meta: "Effective date: May 2025"
---

## The short version

Crystal Lattice runs from your computer. Your conversations, sessions, and agent
history are stored on your own filesystem by default and are not sent to Crystal
Lattice maintainers by the local app. You do not need an account or a hosted
Crystal Lattice workspace to use the local app.

## What Crystal Lattice collects

The Crystal Lattice CLI and local app process collect nothing on our behalf.
Specifically:

- All session data, message history, and agent configuration is stored locally
  on your machine in the working directory you specify.
- No telemetry, analytics, or usage data is transmitted to Crystal Lattice from
  the CLI or local app process.
- No account creation is required. We have no user database.

## AI provider requests

When you run an agent session, Crystal Lattice sends your messages to whichever
AI provider you have configured (OpenAI, Anthropic, Google Gemini, OpenRouter, or
a local model via Ollama). These requests go directly from your machine to the
provider's API — they do not pass through Crystal Lattice infrastructure.

Each provider has their own privacy policy and data handling practices. If you
use a local model via Ollama, model requests can stay on your machine.

## The bridge service

Crystal Lattice includes an optional bridge service that relays requests between
your phone and Crystal Lattice running on your computer when they are on
different networks. The bridge relays traffic in real time; it is not designed to
store your messages, sessions, or conversation content. Connections are
identified by a pairing code that you generate and the local Crystal Lattice
process registers. The bridge retains pairing metadata, such as a session ID and
registration, while the bridge session is active.

## This website

This website, initially available at
crystallattice.dev.dynamicprogrammingsolutions.com for testing and later at
crystallattice.dev, may collect standard web server access logs (IP address,
browser type, pages visited, referrer) for operational purposes. We do not use
third-party advertising trackers. If we add any analytics in the future, we will
update this policy.

## The mobile app

Crystal Lattice Control connects to the address you choose: a local IP, a local
network discovery address, or a bridge URL. The app stores connection
preferences locally on your device. If you use a bridge operated by the project
or by someone else, traffic is relayed through that bridge.

App Store and Google Play distribution means that Apple and Google's platform
privacy policies also apply to the download and installation of the app.

## Open source

The Crystal Lattice repository contains components under their respective open
source licenses. You can review what the software does by reading the source
code and license files on GitHub.

## Changes to this policy

We may update this policy if the software or services change in ways that affect
privacy. Changes will be posted to this page with an updated effective date.

## Contact

Questions about this policy can be directed to the project via GitHub Issues or
the contact information in the repository.

# Mobile Connectivity And Store Links

Update the mobile page and connectivity copy so it accurately explains local network discovery, bridge pairing, and current mobile distribution status.

## Requirements checklist

- [ ] Mark App Store and Google Play as coming soon.
- [ ] Keep "run from source" as a fallback path.
- [ ] Explain same-network discovery in plain language before naming Bonjour/mDNS.
- [ ] Explain bridge as a way to connect from outside the local network.
- [ ] Use real bridge flags and remote URL shape, not `--enable-bridge` or localhost.
- [ ] Avoid saying the mobile app exposes the complete API or can do everything the terminal can do.
- [ ] Avoid describing desktop as a different device.

Parent Task: `tasks/20260611-landing-page-positioning-update/000-main.md`
Depends On: `tasks/20260611-landing-page-positioning-update/010-claim-safety-and-current-state-audit.md`

## Files To Change

- `landing_page/src/content/pages/mobile.yaml`
- `landing_page/src/components/mobile/Download.astro`
- Possibly `landing_page/src/components/mobile/Hero.astro` if store buttons need disabled/coming-soon state.
- Possibly `landing_page/src/components/mobile/Connect.astro` if method blocks need richer explanatory text.

## Desired Content Target

Use `tasks/20260611-landing-page-positioning-update/desired-final-content/mobile.yaml`
as the target mobile page content. It includes coming-soon store buttons, a
source fallback, and corrected connectivity copy.

## Draft Mobile Hero

```text
Continue agent work from your phone.

Crystal Lattice Control connects to the Crystal Lattice instance running on your computer. Browse sessions, send messages, watch responses stream, and use plugin-driven actions without staying at the keyboard.
```

Store button state:

```text
App Store - Coming soon
Google Play - Coming soon
Run from source
```

## Draft Mobile Feature Copy

Replace "complete API" copy with:

```text
The mobile app focuses on core session workflows: browse sessions, send messages, stream responses, manage supported settings and plugins, and run actions that plugins expose to the UI.
```

Replace provider/model switching claim with:

```text
Choose configured agents and adjust supported session settings. When a plugin exposes a setting, the app can render the control without hardcoding that feature into the app.
```

## Draft Connectivity Section

Title:

```text
Connect near or far
```

Body:

```text
Use automatic discovery when your phone is on the same local network. Use the bridge when you want to connect from outside that network.
```

Methods:

1. Manual address

```text
Enter your computer's local network address and port when you already know where Crystal Lattice is running.
```

Code:

```text
http://192.168.1.42:9000
```

2. Automatic local discovery

```text
On the same Wi-Fi, the app can find your computer automatically. Under the hood this uses Bonjour/mDNS local network discovery.
```

Code:

```bash
crystal-lattice ... --enable-bonjour
```

3. Bridge pairing

```text
When your phone is outside the local network, deploy the bridge and connect through a pairing code.
```

Code:

```bash
crystal-lattice ... --bridge-url wss://<your-cloudfront-domain>/ws/websocket
```

## AWS Bridge Snippet

The bridge AWS deployment is a working path. Use this in either the homepage or mobile connectivity page:

```bash
ALLOW_AWS_DEPLOY=1 deploy/aws-ec2/build.sh \
  --profile secure \
  --stack-name crystal-lattice-bridge \
  --region us-east-1

ALLOW_AWS_DEPLOY=1 deploy/aws-ec2/up.sh \
  --profile secure \
  --stack-name crystal-lattice-bridge \
  --region us-east-1
```

Then connect Crystal Lattice:

```bash
crystal-lattice \
  --server \
  --console \
  --config-local \
  --host 0.0.0.0 \
  --port 9000 \
  --bridge-url wss://<your-cloudfront-domain>/ws/websocket
```

## Component Note

If `mobile/Download.astro` assumes every store button is an anchor, add a minimal `disabled` or `status` property. Avoid `href: "#"` for coming-soon buttons.

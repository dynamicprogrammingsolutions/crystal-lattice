Start Crystal Lattice in the project folder where you want the agent to work. The terminal UI can stay open, but the work is not trapped there: the phone app can open the same sessions and watch responses stream.

On the same Wi-Fi, the mobile app can find your computer automatically. Open Crystal Lattice Control, choose **Automatic Discovery**, select your computer, and keep going from your phone.

```bash
curl -fsSL https://crystal-lattice-downloads-874087778966.s3.us-east-1.amazonaws.com/crystal-lattice-cli/install.sh | bash

mkdir -p ~/crystal-lattice-demo
cd ~/crystal-lattice-demo

crystal-lattice \
  --server \
  --console \
  --config-local \
  --host 0.0.0.0 \
  --port 9000 \
  --enable-bonjour
```

Automatic discovery uses the local network. If your phone is away from that network, use the bridge section below.
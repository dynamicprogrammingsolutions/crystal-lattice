When your phone is not on the same network as your computer, deploy the bridge and pair through it. The bridge gives Crystal Lattice clients a way to reconnect from outside the local network.

Deploy the bridge on AWS:

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

Start Crystal Lattice with the bridge URL printed by the deployment:

```bash
crystal-lattice \
  --server \
  --console \
  --config-local \
  --host 0.0.0.0 \
  --port 9000 \
  --bridge-url wss://<your-cloudfront-domain>/ws/websocket
```

Then open Crystal Lattice Control, choose **Bridge Service**, enter the bridge URL, select your computer, and enter the pairing code.

# Remote Docker deployment

`deploy.sh` copies a clean Bridge service source bundle to an explicit remote
Docker host, selects the installed Compose command, builds and recreates one
bridge node, and verifies the origin and public HTTP v1 capability endpoints.

The deploy script is parameterized and safe to commit. Put concrete hostnames,
SSH identities, and the stable signing secret in a gitignored local wrapper.

See [Remote Docker deployment](../../docs/remote-docker-deployment.md) for
configuration, first deployment, edge requirements, and verification.
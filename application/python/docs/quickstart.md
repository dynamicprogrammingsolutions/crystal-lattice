# Terminal and HTTP application quickstart

This quickstart installs the `crystal-lattice` command, starts its HTTP server,
and verifies a concrete response without requiring provider credentials.

## Install

Install the supported bundled-Python command:

```bash
curl -fsSL https://download.crystallattice.dev/crystal-lattice-cli/install.sh | bash
```

Review the installer before running it when required by your environment:

```bash
curl -fsSLO https://download.crystallattice.dev/crystal-lattice-cli/install.sh
less install.sh
bash install.sh
```

For source development, run from the repository root:

```bash
python -m pip install -e "core/python[dev]"
python -m pip install -e application/python
```

## Start a local server

Create a workspace and start the server with project-local configuration:

```bash
mkdir -p ~/crystal-lattice-demo
cd ~/crystal-lattice-demo
crystal-lattice --config-local --host 127.0.0.1 --port 9000
```

The command creates `.crystal/config.json` when it is missing and listens on
`http://127.0.0.1:9000`.

## Verify the result

From another terminal:

```bash
curl http://127.0.0.1:9000/api/hello
```

The response contains:

```json
{
  "message": "Hello from Bonjour Server!",
  "timestamp": "<UTC timestamp ending in Z>",
  "method": "GET"
}
```

Stop the server with `Ctrl-C`.

## Continue

- Add provider credentials and choose agents using the
  [package README](../README.md#provider-credentials).
- Configure plugin packages, placeholders, and policy in
  [Application configuration](configuration.md).
- Start terminal and server together with:

  ```bash
  crystal-lattice --server --console --config-local
  ```

- For phone connectivity, continue with the
  [mobile connectivity guide](../README.md#mobile-connectivity).
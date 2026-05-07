import Config

config :logger, level: :warning

config :bridge, Bridge.Endpoint,
  http: [port: 4002],
  server: true

config :libcluster,
  topologies: []

config :bridge,
  pairing_token_secret: "bridge-test-pairing-token-secret",
  pairing_token_salt: "pairing-token-test-v1",
  pairing_token_ttl_seconds: 2_592_000

import Config

config :logger, level: :warning

config :bridge, Bridge.Endpoint,
  http: [port: 4002, compress: true],
  server: true

config :libcluster,
  topologies: []

config :bridge,
  pairing_token_secret: "bridge-test-pairing-token-secret",
  pairing_token_salt: "pairing-token-test-v1",
  http_transfer_token_salt: "http-transfer-token-test-v1",
  http_transfer_token_ttl_seconds: 180,
  pairing_token_ttl_seconds: 2_592_000

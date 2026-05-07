import Config

config :cloud_orchestrator, CloudOrchestrator.Endpoint,
  http: [ip: {127, 0, 0, 1}, port: 0],
  server: false

config :cloud_orchestrator,
  runner: CloudOrchestrator.Runner.InMemory,
  public_url: "http://127.0.0.1:4100",
  token_secret: "test-token-secret",
  transfer_public_host: nil

config :logger, level: :warning

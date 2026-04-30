import Config

config :cloud_orchestrator, CloudOrchestrator.Endpoint,
  http: [ip: {0, 0, 0, 0}, port: String.to_integer(System.get_env("PORT") || "4100")],
  server: true,
  secret_key_base: System.get_env("SECRET_KEY_BASE") || String.duplicate("a", 64)

runner =
  case System.get_env("CLOUD_ORCHESTRATOR_RUNNER") || "memory" do
    "docker" -> CloudOrchestrator.Runner.Docker
    "memory" -> CloudOrchestrator.Runner.InMemory
    _ -> CloudOrchestrator.Runner.InMemory
  end

config :cloud_orchestrator,
  runner: runner,
  public_url: System.get_env("CLOUD_ORCHESTRATOR_PUBLIC_URL") || "http://127.0.0.1:4100",
  token_secret: System.get_env("CLOUD_ORCHESTRATOR_TOKEN_SECRET") || "dev-token-secret",
  control_token: System.get_env("CLOUD_ORCHESTRATOR_CONTROL_TOKEN"),
  data_dir: System.get_env("CLOUD_ORCHESTRATOR_DATA_DIR") || "/tmp/cloud-orchestrator",
  host_data_dir:
    System.get_env("CLOUD_ORCHESTRATOR_HOST_DATA_DIR") ||
      System.get_env("CLOUD_ORCHESTRATOR_DATA_DIR") ||
      "/tmp/cloud-orchestrator",
  transfer_port_start: String.to_integer(System.get_env("TRANSFER_PORT_START") || "22000"),
  transfer_port_end: String.to_integer(System.get_env("TRANSFER_PORT_END") || "22099")

config :logger, :console,
  format: "$time $metadata[$level] $message\n",
  metadata: [:request_id]

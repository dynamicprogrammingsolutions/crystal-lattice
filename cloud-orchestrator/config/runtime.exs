import Config

if config_env() == :prod do
  config :cloud_orchestrator, CloudOrchestrator.Endpoint,
    http: [ip: {0, 0, 0, 0}, port: String.to_integer(System.get_env("PORT") || "4100")],
    server: true,
    secret_key_base:
      System.get_env("SECRET_KEY_BASE") ||
        raise("SECRET_KEY_BASE is required in production")

  runner =
    case System.get_env("CLOUD_ORCHESTRATOR_RUNNER") || "docker" do
      "docker" -> CloudOrchestrator.Runner.Docker
      "memory" -> CloudOrchestrator.Runner.InMemory
      other -> raise("Unsupported CLOUD_ORCHESTRATOR_RUNNER=#{other}")
    end

  config :cloud_orchestrator,
    runner: runner,
    public_url:
      System.get_env("CLOUD_ORCHESTRATOR_PUBLIC_URL") ||
        raise("CLOUD_ORCHESTRATOR_PUBLIC_URL is required in production"),
    token_secret:
      System.get_env("CLOUD_ORCHESTRATOR_TOKEN_SECRET") ||
        raise("CLOUD_ORCHESTRATOR_TOKEN_SECRET is required in production"),
    control_token: System.get_env("CLOUD_ORCHESTRATOR_CONTROL_TOKEN"),
    data_dir: System.get_env("CLOUD_ORCHESTRATOR_DATA_DIR") || "/var/lib/cloud-orchestrator",
    host_data_dir:
      System.get_env("CLOUD_ORCHESTRATOR_HOST_DATA_DIR") ||
        System.get_env("CLOUD_ORCHESTRATOR_DATA_DIR") ||
        "/var/lib/cloud-orchestrator",
    transfer_public_host: System.get_env("CLOUD_ORCHESTRATOR_TRANSFER_PUBLIC_HOST"),
    transfer_port_start: String.to_integer(System.get_env("TRANSFER_PORT_START") || "22000"),
    transfer_port_end: String.to_integer(System.get_env("TRANSFER_PORT_END") || "22099")
end

defmodule CloudOrchestrator.Endpoint do
  use Phoenix.Endpoint, otp_app: :cloud_orchestrator

  plug(Plug.Logger)

  plug(Plug.Parsers,
    parsers: [:json, :urlencoded, :multipart],
    pass: ["*/*"],
    json_decoder: Jason,
    length: 100_000_000
  )

  plug(CloudOrchestrator.Router)
end

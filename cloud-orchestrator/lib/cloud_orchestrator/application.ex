defmodule CloudOrchestrator.Application do
  use Application

  @impl true
  def start(_type, _args) do
    children = [
      {Finch, name: CloudOrchestrator.Finch},
      CloudOrchestrator.TransferRegistry,
      CloudOrchestrator.InstanceRegistry,
      CloudOrchestrator.Endpoint
    ]

    Supervisor.start_link(children, strategy: :one_for_one, name: CloudOrchestrator.Supervisor)
  end
end

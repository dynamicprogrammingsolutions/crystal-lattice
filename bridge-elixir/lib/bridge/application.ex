defmodule Bridge.Application do
  use Application

  @impl true
  def start(_type, _args) do
    children = [
      {Phoenix.PubSub, name: Bridge.PubSub},
      {Cluster.Supervisor, [Application.get_env(:libcluster, :topologies), [name: Bridge.ClusterSupervisor]]},
      Bridge.ServerRegistry,
      Bridge.PairingManager,
      Bridge.SessionManager,
      Bridge.Endpoint
    ]

    opts = [strategy: :one_for_one, name: Bridge.Supervisor]
    Supervisor.start_link(children, opts)
  end
end

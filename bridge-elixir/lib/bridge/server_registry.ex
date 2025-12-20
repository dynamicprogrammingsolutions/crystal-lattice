defmodule Bridge.ServerRegistry do
  use GenServer
  require Logger

  @table_name :bridge_servers

  def start_link(_opts) do
    GenServer.start_link(__MODULE__, [], name: __MODULE__)
  end

  def register_server(server_id, info) do
    GenServer.call(__MODULE__, {:register, server_id, info})
  end

  def unregister_server(server_id) do
    GenServer.call(__MODULE__, {:unregister, server_id})
  end

  def get_server(server_id) do
    case :ets.lookup(@table_name, server_id) do
      [{^server_id, info}] -> {:ok, info}
      [] -> {:error, :not_found}
    end
  end

  def list_servers do
    :ets.tab2list(@table_name)
    |> Enum.map(fn {_id, info} -> info end)
  end

  def count_servers do
    :ets.info(@table_name, :size)
  end

  @impl true
  def init(_) do
    :ets.new(@table_name, [:named_table, :set, :public, read_concurrency: true])
    Phoenix.PubSub.subscribe(Bridge.PubSub, "servers:registry")
    {:ok, %{}}
  end

  @impl true
  def handle_call({:register, server_id, info}, _from, state) do
    server_info =
      Map.merge(info, %{
        server_id: server_id,
        node: node(),
        connected_at: DateTime.utc_now()
      })

    :ets.insert(@table_name, {server_id, server_info})

    Phoenix.PubSub.broadcast(
      Bridge.PubSub,
      "servers:registry",
      {:server_registered, server_id, server_info}
    )

    Logger.info("✅ Server registered: #{server_id} (#{server_info.display_name})")
    {:reply, :ok, state}
  end

  @impl true
  def handle_call({:unregister, server_id}, _from, state) do
    :ets.delete(@table_name, server_id)

    Phoenix.PubSub.broadcast(
      Bridge.PubSub,
      "servers:registry",
      {:server_unregistered, server_id}
    )

    Logger.info("❌ Server unregistered: #{server_id}")
    {:reply, :ok, state}
  end

  @impl true
  def handle_info({:server_registered, server_id, info}, state) do
    if info.node != node() do
      :ets.insert(@table_name, {server_id, info})
      Logger.debug("🔄 Remote server registered: #{server_id} on #{info.node}")
    end

    {:noreply, state}
  end

  @impl true
  def handle_info({:server_unregistered, server_id}, state) do
    :ets.delete(@table_name, server_id)
    {:noreply, state}
  end

  @impl true
  def handle_info(_msg, state) do
    {:noreply, state}
  end
end

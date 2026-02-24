defmodule Bridge.ServerRegistry do
  use GenServer
  require Logger

  @table_name :bridge_servers

  defmodule Registration do
    @enforce_keys [:server_id, :info, :monitor_ref]
    defstruct [:server_id, :info, :monitor_ref]
  end

  def start_link(_opts) do
    GenServer.start_link(__MODULE__, [], name: __MODULE__)
  end

  defp safe_send(pid, message) do
    try do
      send(pid, message)
      :ok
    rescue
      ArgumentError ->
        :error
    end
  end

  def register_server(server_id, info, opts \\ []) do
    GenServer.call(__MODULE__, {:register, server_id, info, opts})
  end

  def unregister_server(server_id, channel_pid) do
    GenServer.call(__MODULE__, {:unregister, server_id, channel_pid})
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
    {:ok, %{registrations: %{}, server_id_by_ref: %{}}}
  end

  @impl true
  def handle_call({:register, server_id, info, opts}, _from, state) do
    channel_pid = Map.get(info, :channel_pid)

    if not is_pid(channel_pid) do
      {:reply, {:error, :invalid_channel_pid}, state}
    else
      conflict_policy = Keyword.get(opts, :conflict_policy, server_id_conflict_policy())

      server_info =
        Map.merge(info, %{
          server_id: server_id,
          node: node(),
          connected_at: DateTime.utc_now()
        })

      case :ets.lookup(@table_name, server_id) do
        [] ->
          {state, _ref} = monitor_registration(server_id, channel_pid, state)
          :ets.insert(@table_name, {server_id, server_info})
          broadcast_registered(server_id, server_info)
          Logger.info("✅ Server registered: #{server_id} (#{server_info.display_name})")
          {:reply, {:ok, :registered}, state}

        [{^server_id, existing_info}] ->
          existing_pid = Map.get(existing_info, :channel_pid)

          cond do
            existing_pid == channel_pid ->
              # Idempotent re-register for same pid; refresh metadata.
              :ets.insert(@table_name, {server_id, server_info})
              broadcast_registered(server_id, server_info)
              {:reply, {:ok, :registered}, state}

            conflict_policy == :reject ->
              {:reply, {:error, :already_registered}, state}

            true ->
              # Takeover: replace active pid and notify the old one.
              _ = safe_send(existing_pid, {:superseded, server_id, channel_pid})

              state = demonitor_registration(server_id, state)
              {state, _ref} = monitor_registration(server_id, channel_pid, state)

              :ets.insert(@table_name, {server_id, server_info})
              broadcast_registered(server_id, server_info)

              Logger.warning(
                "🔁 Server takeover for #{server_id}: #{inspect(existing_pid)} -> #{inspect(channel_pid)}"
              )

              {:reply, {:ok, {:took_over, existing_pid}}, state}
          end
      end
    end
  end

  @impl true
  def handle_call({:unregister, server_id, channel_pid}, _from, state) do
    case :ets.lookup(@table_name, server_id) do
      [{^server_id, %{channel_pid: ^channel_pid}}] ->
        :ets.delete(@table_name, server_id)
        state = demonitor_registration(server_id, state)
        broadcast_unregistered(server_id, channel_pid)
        Logger.info("❌ Server unregistered: #{server_id}")
        {:reply, :ok, state}

      _ ->
        {:reply, :ok, state}
    end
  end

  @impl true
  def handle_info({:server_registered, server_id, info}, state) do
    state =
      if info.node != node() do
        state = demonitor_registration(server_id, state)
        :ets.insert(@table_name, {server_id, info})
        Logger.debug("🔄 Remote server registered: #{server_id} on #{info.node}")
        state
      else
        state
      end

    {:noreply, state}
  end

  @impl true
  def handle_info({:server_unregistered, server_id, channel_pid}, state) do
    state =
      case :ets.lookup(@table_name, server_id) do
        [{^server_id, %{channel_pid: ^channel_pid}}] ->
          :ets.delete(@table_name, server_id)
          state = demonitor_registration(server_id, state)
          Logger.debug("🔄 Remote server unregistered: #{server_id}")
          state

        _ ->
          state
      end

    {:noreply, state}
  end

  @impl true
  def handle_info({:DOWN, monitor_ref, :process, channel_pid, _reason}, state) do
    {server_id, state} = pop_server_id_for_ref(monitor_ref, state)

    state =
      case server_id do
        nil ->
          state

        server_id ->
          %{state | registrations: Map.delete(state.registrations, server_id)}
      end

    case server_id do
      nil ->
        {:noreply, state}

      server_id ->
        case :ets.lookup(@table_name, server_id) do
          [{^server_id, %{channel_pid: ^channel_pid}}] ->
            :ets.delete(@table_name, server_id)
            broadcast_unregistered(server_id, channel_pid)
            Logger.info("💥 Server channel down; unregistered: #{server_id}")
            {:noreply, state}

          _ ->
            {:noreply, state}
        end
    end
  end

  @impl true
  def handle_info(_msg, state) do
    {:noreply, state}
  end

  defp monitor_registration(server_id, channel_pid, state) do
    monitor_ref = Process.monitor(channel_pid)

    registrations =
      Map.put(state.registrations, server_id, %Registration{
        server_id: server_id,
        info: %{channel_pid: channel_pid},
        monitor_ref: monitor_ref
      })

    server_id_by_ref = Map.put(state.server_id_by_ref, monitor_ref, server_id)
    {%{state | registrations: registrations, server_id_by_ref: server_id_by_ref}, monitor_ref}
  end

  defp demonitor_registration(server_id, state) do
    case Map.get(state.registrations, server_id) do
      nil ->
        state

      %Registration{monitor_ref: monitor_ref} ->
        Process.demonitor(monitor_ref, [:flush])
        registrations = Map.delete(state.registrations, server_id)
        server_id_by_ref = Map.delete(state.server_id_by_ref, monitor_ref)
        %{state | registrations: registrations, server_id_by_ref: server_id_by_ref}
    end
  end

  defp pop_server_id_for_ref(monitor_ref, state) do
    case Map.pop(state.server_id_by_ref, monitor_ref) do
      {nil, server_id_by_ref} ->
        {nil, %{state | server_id_by_ref: server_id_by_ref}}

      {server_id, server_id_by_ref} ->
        {server_id, %{state | server_id_by_ref: server_id_by_ref}}
    end
  end

  defp broadcast_registered(server_id, server_info) do
    Phoenix.PubSub.broadcast(
      Bridge.PubSub,
      "servers:registry",
      {:server_registered, server_id, server_info}
    )
  end

  defp broadcast_unregistered(server_id, channel_pid) do
    Phoenix.PubSub.broadcast(
      Bridge.PubSub,
      "servers:registry",
      {:server_unregistered, server_id, channel_pid}
    )
  end

  defp server_id_conflict_policy do
    case System.get_env("BRIDGE_SERVER_ID_CONFLICT_POLICY") do
      nil ->
        :takeover

      "" ->
        :takeover

      "reject" ->
        :reject

      "takeover" ->
        :takeover

      other ->
        Logger.warning(
          "Unknown BRIDGE_SERVER_ID_CONFLICT_POLICY=#{inspect(other)}; defaulting to takeover"
        )

        :takeover
    end
  end
end

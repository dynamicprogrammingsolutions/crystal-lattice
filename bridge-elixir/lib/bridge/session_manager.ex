defmodule Bridge.SessionManager do
  use GenServer
  require Logger

  @table_name :bridge_sessions

  defmodule Session do
    defstruct [
      :session_id,
      :server_id,
      :client_id,
      :server_node,
      :client_node,
      :created_at,
      :last_activity
    ]
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

  def create_session(server_id, client_id, server_node, client_node) do
    GenServer.call(__MODULE__, {:create_session, server_id, client_id, server_node, client_node})
  end

  def get_session(session_id) do
    case :ets.lookup(@table_name, session_id) do
      [{^session_id, session}] -> {:ok, session}
      [] -> {:error, :not_found}
    end
  end

  def update_activity(session_id) do
    GenServer.cast(__MODULE__, {:update_activity, session_id})
  end

  def delete_session(session_id) do
    GenServer.call(__MODULE__, {:delete_session, session_id})
  end

  def count_sessions do
    :ets.info(@table_name, :size)
  end

  @impl true
  def init(_) do
    :ets.new(@table_name, [:named_table, :set, :public, read_concurrency: true])
    schedule_cleanup()
    {:ok, %{}}
  end

  @impl true
  def handle_call({:create_session, server_id, client_id, server_node, client_node}, _from, state) do
    case Bridge.ServerRegistry.get_server(server_id) do
      {:ok, server_info} ->
        session_id = generate_session_id()
        now = DateTime.utc_now()

        session = %Session{
          session_id: session_id,
          server_id: server_id,
          client_id: client_id,
          server_node: server_node,
          client_node: client_node,
          created_at: now,
          last_activity: now
        }

        :ets.insert(@table_name, {session_id, session})

        case safe_send(server_info.channel_pid, {:paired, client_id, session_id}) do
          :ok ->
            Logger.info(
              "🔗 Session created: #{session_id} (server: #{server_id}, client: #{client_id})"
            )

            {:reply, {:ok, session_id}, state}

          :error ->
            :ets.delete(@table_name, session_id)
            {:reply, {:error, :server_not_found}, state}
        end

      {:error, :not_found} ->
        {:reply, {:error, :server_not_found}, state}
    end
  end

  @impl true
  def handle_call({:delete_session, session_id}, _from, state) do
    :ets.delete(@table_name, session_id)
    Logger.info("🔌 Session deleted: #{session_id}")
    {:reply, :ok, state}
  end

  @impl true
  def handle_cast({:update_activity, session_id}, state) do
    case :ets.lookup(@table_name, session_id) do
      [{^session_id, session}] ->
        updated_session = %{session | last_activity: DateTime.utc_now()}
        :ets.insert(@table_name, {session_id, updated_session})

      [] ->
        :ok
    end

    {:noreply, state}
  end

  @impl true
  def handle_info(:cleanup_expired, state) do
    timeout = Application.get_env(:bridge, :session_timeout, 3600)
    now = DateTime.utc_now()

    @table_name
    |> :ets.tab2list()
    |> Enum.each(fn {session_id, session} ->
      age = DateTime.diff(now, session.last_activity, :second)

      if age > timeout do
        :ets.delete(@table_name, session_id)
        Logger.debug("🧹 Expired session removed: #{session_id}")
      end
    end)

    schedule_cleanup()
    {:noreply, state}
  end

  defp generate_session_id do
    UUID.uuid4()
  end

  defp schedule_cleanup do
    Process.send_after(self(), :cleanup_expired, 300_000)
  end
end

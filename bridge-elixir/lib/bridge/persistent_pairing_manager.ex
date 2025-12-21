defmodule Bridge.PersistentPairingManager do
  use GenServer
  require Logger

  @table_by_token :bridge_pairings_by_token
  @table_by_key :bridge_pairings_by_key

  defmodule Pairing do
    defstruct [:token, :server_id, :client_id, :last_session_id, :created_at, :last_used_at]
  end

  def start_link(_opts) do
    GenServer.start_link(__MODULE__, [], name: __MODULE__)
  end

  @doc """
  Create or return an existing persistent pairing token.

  The token is scoped to a `(server_id, client_id)` pair and kept in ETS
  for as long as the bridge node is running. It is used by app clients
  to resume a logical pairing across WebSocket reconnects.
  """
  @spec create_or_get_token(String.t(), String.t()) :: {:ok, String.t()}
  def create_or_get_token(server_id, client_id) do
    GenServer.call(__MODULE__, {:create_or_get, server_id, client_id})
  end

  @doc """
  Look up a pairing by its token.
  """
  @spec get_by_token(String.t()) :: {:ok, map()} | {:error, :not_found}
  def get_by_token(token) do
    case :ets.lookup(@table_by_token, token) do
      [{^token, pairing}] -> {:ok, pairing}
      [] -> {:error, :not_found}
    end
  end

  @doc """
  Update `last_used_at` for a token if it exists.
  """
  @spec touch(String.t()) :: :ok
  def touch(token) do
    GenServer.cast(__MODULE__, {:touch, token})
  end

  @doc """
  Remember the most recent bridge `session_id` for this token.

  If the token is unknown, this is a no-op.
  """
  @spec set_last_session(String.t(), String.t()) :: :ok
  def set_last_session(token, session_id) do
    GenServer.call(__MODULE__, {:set_last_session, token, session_id})
  end

  @impl true
  def init(_) do
    :ets.new(@table_by_token, [:named_table, :set, :public, read_concurrency: true])
    :ets.new(@table_by_key, [:named_table, :set, :public, read_concurrency: true])
    {:ok, %{}}
  end

  @impl true
  def handle_cast({:touch, token}, state) do
    case :ets.lookup(@table_by_token, token) do
      [{^token, pairing}] ->
        updated = %{pairing | last_used_at: DateTime.utc_now()}
        :ets.insert(@table_by_token, {token, updated})

      [] ->
        :ok
    end

    {:noreply, state}
  end

  @impl true
  def handle_call({:set_last_session, token, session_id}, _from, state) do
    case :ets.lookup(@table_by_token, token) do
      [{^token, pairing}] ->
        now = DateTime.utc_now()
        updated = %{pairing | last_session_id: session_id, last_used_at: now}
        :ets.insert(@table_by_token, {token, updated})

      [] ->
        :ok
    end

    {:reply, :ok, state}
  end

  @impl true
  def handle_call({:create_or_get, server_id, client_id}, _from, state) do
    key = {server_id, client_id}

    case :ets.lookup(@table_by_key, key) do
      [{^key, token}] ->
        case :ets.lookup(@table_by_token, token) do
          [{^token, _pairing}] ->
            {:reply, {:ok, token}, state}

          [] ->
            # Inconsistent tables; create a fresh pairing.
            create_new_pairing(key, server_id, client_id, state)
        end

      [] ->
        create_new_pairing(key, server_id, client_id, state)
    end
  end

  defp create_new_pairing(key, server_id, client_id, state) do
    token = UUID.uuid4()
    now = DateTime.utc_now()

    pairing = %Pairing{
      token: token,
      server_id: server_id,
      client_id: client_id,
      last_session_id: nil,
      created_at: now,
      last_used_at: now
    }

    :ets.insert(@table_by_token, {token, pairing})
    :ets.insert(@table_by_key, {key, token})

    Logger.info("🔐 Persistent pairing token created for server #{server_id}, client #{client_id}")

    {:reply, {:ok, token}, state}
  end
end

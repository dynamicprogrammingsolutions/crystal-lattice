defmodule Bridge.PairingManager do
  use GenServer
  require Logger

  @table_name :bridge_pairing_codes

  defmodule PairingRequest do
    defstruct [:code, :server_id, :client_id, :expires_at, :attempts]
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

  def create_pairing_request(server_id, client_id) do
    GenServer.call(__MODULE__, {:create_pairing, server_id, client_id})
  end

  def validate_code(server_id, client_id, code) do
    GenServer.call(__MODULE__, {:validate_code, server_id, client_id, code})
  end

  def cancel_pairing(server_id, client_id) do
    GenServer.call(__MODULE__, {:cancel_pairing, server_id, client_id})
  end

  @impl true
  def init(_) do
    :ets.new(@table_name, [:named_table, :set, :public, read_concurrency: true])
    schedule_cleanup()
    {:ok, %{}}
  end

  @impl true
  def handle_call({:create_pairing, server_id, client_id}, _from, state) do
    case Bridge.ServerRegistry.get_server(server_id) do
      {:ok, server_info} ->
        code = generate_code()
        ttl = Application.get_env(:bridge, :pairing_code_ttl, 300)
        expires_at = DateTime.utc_now() |> DateTime.add(ttl, :second)

        request = %PairingRequest{
          code: code,
          server_id: server_id,
          client_id: client_id,
          expires_at: expires_at,
          attempts: 0
        }

        key = {server_id, client_id}
        :ets.insert(@table_name, {key, request})

        case safe_send(server_info.channel_pid, {:pairing_requested, client_id, code, expires_at}) do
          :ok ->
            Logger.info(
              "🔑 Pairing code generated: #{code} for server #{server_id}, client #{client_id}"
            )

            {:reply, {:ok, code, expires_at}, state}

          :error ->
            :ets.delete(@table_name, key)
            {:reply, {:error, :server_not_found}, state}
        end

      {:error, :not_found} ->
        {:reply, {:error, :server_not_found}, state}
    end
  end

  @impl true
  def handle_call({:validate_code, server_id, client_id, code}, _from, state) do
    key = {server_id, client_id}

    case :ets.lookup(@table_name, key) do
      [{^key, request}] ->
        validate_request(request, code, key, state)

      [] ->
        {:reply, {:error, :not_found}, state}
    end
  end

  @impl true
  def handle_call({:cancel_pairing, server_id, client_id}, _from, state) do
    key = {server_id, client_id}
    :ets.delete(@table_name, key)
    {:reply, :ok, state}
  end

  @impl true
  def handle_info(:cleanup_expired, state) do
    now = DateTime.utc_now()

    @table_name
    |> :ets.tab2list()
    |> Enum.each(fn {key, request} ->
      if DateTime.compare(request.expires_at, now) == :lt do
        :ets.delete(@table_name, key)
        Logger.debug("🧹 Expired pairing code removed: #{request.code}")
      end
    end)

    schedule_cleanup()
    {:noreply, state}
  end

  defp validate_request(request, code, key, state) do
    max_attempts = Application.get_env(:bridge, :max_pairing_attempts, 3)
    now = DateTime.utc_now()

    cond do
      DateTime.compare(request.expires_at, now) == :lt ->
        :ets.delete(@table_name, key)
        {:reply, {:error, :expired}, state}

      request.attempts >= max_attempts ->
        :ets.delete(@table_name, key)
        {:reply, {:error, :too_many_attempts}, state}

      request.code != code ->
        updated_request = %{request | attempts: request.attempts + 1}
        :ets.insert(@table_name, {key, updated_request})
        {:reply, {:error, :invalid_code}, state}

      true ->
        :ets.delete(@table_name, key)
        Logger.info("✅ Pairing successful: #{request.server_id} <-> #{request.client_id}")
        {:reply, :ok, state}
    end
  end

  defp generate_code do
    :rand.uniform(999_999)
    |> Integer.to_string()
    |> String.pad_leading(6, "0")
  end

  defp schedule_cleanup do
    Process.send_after(self(), :cleanup_expired, 60_000)
  end
end

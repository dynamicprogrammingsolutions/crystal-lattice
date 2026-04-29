defmodule CloudOrchestrator.TransferRegistry do
  use GenServer

  alias CloudOrchestrator.Id

  def start_link(_opts) do
    GenServer.start_link(__MODULE__, %{}, name: __MODULE__)
  end

  def create(params), do: GenServer.call(__MODULE__, {:create, params})
  def mark_ready(id), do: GenServer.call(__MODULE__, {:mark_ready, id})
  def get(id), do: GenServer.call(__MODULE__, {:get, id})
  def delete(id), do: GenServer.call(__MODULE__, {:delete, id})
  def count, do: GenServer.call(__MODULE__, :count)
  def reset, do: GenServer.call(__MODULE__, :reset)
  def upload_bundle(id, body), do: GenServer.call(__MODULE__, {:upload_bundle, id, body}, 60_000)
  def read_bundle(id), do: GenServer.call(__MODULE__, {:read_bundle, id}, 60_000)

  @impl true
  def init(_opts), do: {:ok, %{}}

  @impl true
  def handle_call({:create, params}, _from, state) do
    direction = Map.get(params, "direction", "upload")
    method = Map.get(params, "method", "managed_ssh")
    transfer_id = Id.new("tr")

    transfer = %{
      "transfer_id" => transfer_id,
      "direction" => direction,
      "method" => method,
      "state" => "created",
      "slot_path" => slot_path(transfer_id),
      "slot_host_path" => slot_host_path(transfer_id),
      "endpoint" => endpoint_for(method, params),
      "created_at" => now(),
      "expires_at" => now(System.system_time(:second) + Map.get(params, "ttl_seconds", 1800))
    }

    File.mkdir_p!(transfer["slot_path"])

    {:reply, {:ok, public_transfer(transfer)}, Map.put(state, transfer["transfer_id"], transfer)}
  end

  def handle_call({:mark_ready, id}, _from, state) do
    case Map.fetch(state, id) do
      {:ok, transfer} ->
        next = Map.put(transfer, "state", "ready")
        {:reply, {:ok, public_transfer(next)}, Map.put(state, id, next)}

      :error ->
        {:reply, {:error, :not_found}, state}
    end
  end

  def handle_call({:get, id}, _from, state) do
    {:reply, fetch(state, id), state}
  end

  def handle_call({:upload_bundle, id, body}, _from, state) do
    case Map.fetch(state, id) do
      {:ok, transfer} ->
        File.mkdir_p!(transfer["slot_path"])
        File.write!(Path.join(transfer["slot_path"], "bundle.tar.gz"), body)
        next = Map.put(transfer, "state", "uploaded")
        {:reply, {:ok, public_transfer(next)}, Map.put(state, id, next)}

      :error ->
        {:reply, {:error, :not_found}, state}
    end
  end

  def handle_call({:read_bundle, id}, _from, state) do
    case Map.fetch(state, id) do
      {:ok, transfer} ->
        path = Path.join(transfer["slot_path"], "bundle.tar.gz")

        case File.read(path) do
          {:ok, body} -> {:reply, {:ok, body}, state}
          {:error, _reason} -> {:reply, {:error, :not_found}, state}
        end

      :error ->
        {:reply, {:error, :not_found}, state}
    end
  end

  def handle_call({:delete, id}, _from, state) do
    if Map.has_key?(state, id) do
      {:reply, :ok, Map.delete(state, id)}
    else
      {:reply, {:error, :not_found}, state}
    end
  end

  def handle_call(:count, _from, state), do: {:reply, map_size(state), state}
  def handle_call(:reset, _from, _state), do: {:reply, :ok, %{}}

  defp fetch(state, id) do
    case Map.fetch(state, id) do
      {:ok, transfer} -> {:ok, transfer}
      :error -> {:error, :not_found}
    end
  end

  defp public_transfer(transfer), do: Map.drop(transfer, ["slot_path", "slot_host_path"])

  defp slot_path(id) do
    Path.join([Application.fetch_env!(:cloud_orchestrator, :data_dir), "transfers", id])
  end

  defp slot_host_path(id) do
    Path.join([Application.fetch_env!(:cloud_orchestrator, :host_data_dir), "transfers", id])
  end

  defp endpoint_for("managed_ssh", params) do
    %{
      "host" => Map.get(params, "public_host") || host_from_public_url(),
      "port" =>
        Map.get(params, "port") ||
          Application.fetch_env!(:cloud_orchestrator, :transfer_port_start),
      "username" => "transfer",
      "host_key" => Map.get(params, "host_key")
    }
    |> Enum.reject(fn {_k, v} -> is_nil(v) end)
    |> Map.new()
  end

  defp endpoint_for(method, params) do
    Map.get(params, "endpoint", %{"method" => method})
  end

  defp host_from_public_url do
    public_url = Application.fetch_env!(:cloud_orchestrator, :public_url)
    URI.parse(public_url).host || "127.0.0.1"
  end

  defp now(seconds \\ System.system_time(:second)) do
    seconds |> DateTime.from_unix!() |> DateTime.to_iso8601()
  end
end

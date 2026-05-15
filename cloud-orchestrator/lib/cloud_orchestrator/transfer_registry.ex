defmodule CloudOrchestrator.TransferRegistry do
  use GenServer

  alias CloudOrchestrator.Id
  alias CloudOrchestrator.TransferService.ManagedSSH

  def start_link(_opts) do
    GenServer.start_link(__MODULE__, %{}, name: __MODULE__)
  end

  def create(params), do: GenServer.call(__MODULE__, {:create, params})
  def mark_ready(id), do: GenServer.call(__MODULE__, {:mark_ready, id})
  def get(id), do: GenServer.call(__MODULE__, {:get, id})
  def delete(id), do: GenServer.call(__MODULE__, {:delete, id})
  def count, do: GenServer.call(__MODULE__, :count)
  def reset, do: GenServer.call(__MODULE__, :reset)

  @impl true
  def init(_opts), do: {:ok, %{}}

  @impl true
  def handle_call({:create, params}, _from, state) do
    direction = Map.get(params, "direction", "upload")
    method = Map.get(params, "method", "managed_ssh")
    transfer_id = Id.new("tr")

    base_transfer = %{
      "transfer_id" => transfer_id,
      "direction" => direction,
      "method" => method,
      "state" => "created",
      "slot_path" => slot_path(transfer_id),
      "slot_host_path" => slot_host_path(transfer_id),
      "created_at" => now(),
      "expires_at" => now(System.system_time(:second) + Map.get(params, "ttl_seconds", 1800))
    }

    File.mkdir_p!(base_transfer["slot_path"])

    case attach_endpoint(base_transfer, params, state) do
      {:ok, transfer} ->
        {:reply, {:ok, public_transfer(transfer)},
         Map.put(state, transfer["transfer_id"], transfer)}

      {:error, reason} ->
        File.rm_rf!(base_transfer["slot_path"])
        {:reply, {:error, reason}, state}
    end
  end

  def handle_call({:mark_ready, id}, _from, state) do
    case Map.fetch(state, id) do
      {:ok, transfer} ->
        next =
          transfer
          |> maybe_stop_ready_endpoint()
          |> Map.put("state", "ready")

        {:reply, {:ok, public_transfer(next)}, Map.put(state, id, next)}

      :error ->
        {:reply, {:error, :not_found}, state}
    end
  end

  def handle_call({:get, id}, _from, state) do
    {:reply, fetch(state, id), state}
  end

  def handle_call({:delete, id}, _from, state) do
    case Map.fetch(state, id) do
      {:ok, transfer} ->
        stop_endpoint(transfer)
        File.rm_rf!(transfer["slot_path"])
        {:reply, :ok, Map.delete(state, id)}

      :error ->
        {:reply, {:error, :not_found}, state}
    end
  end

  def handle_call(:count, _from, state), do: {:reply, map_size(state), state}

  def handle_call(:reset, _from, state) do
    Enum.each(Map.values(state), &stop_endpoint/1)
    {:reply, :ok, %{}}
  end

  defp fetch(state, id) do
    case Map.fetch(state, id) do
      {:ok, transfer} -> {:ok, transfer}
      :error -> {:error, :not_found}
    end
  end

  defp public_transfer(transfer),
    do: Map.drop(transfer, ["slot_path", "slot_host_path", "container_id"])

  defp slot_path(id) do
    Path.join([Application.fetch_env!(:cloud_orchestrator, :data_dir), "transfers", id])
  end

  defp slot_host_path(id) do
    Path.join([Application.fetch_env!(:cloud_orchestrator, :host_data_dir), "transfers", id])
  end

  defp attach_endpoint(%{"method" => "managed_ssh"} = transfer, params, state) do
    port = Map.get(params, "port") || allocate_port(state)

    case ManagedSSH.start(transfer, params, port) do
      {:ok, service} ->
        {:ok,
         transfer
         |> Map.put("container_id", service["container_id"])
         |> Map.put("endpoint", service["endpoint"])}

      {:error, reason} ->
        {:error, reason}
    end
  end

  defp attach_endpoint(transfer, _params, _state) do
    {:error, "unsupported_transfer_method: #{transfer["method"]}"}
  end

  defp stop_endpoint(%{"method" => "managed_ssh"} = transfer), do: ManagedSSH.stop(transfer)
  defp stop_endpoint(_transfer), do: :ok

  defp maybe_stop_ready_endpoint(%{"direction" => "upload", "method" => "managed_ssh"} = transfer) do
    stop_endpoint(transfer)

    transfer
    |> Map.delete("container_id")
    |> Map.delete("endpoint")
    |> Map.put("service_state", "stopped")
  end

  defp maybe_stop_ready_endpoint(transfer), do: transfer

  defp allocate_port(state) do
    start_port = Application.fetch_env!(:cloud_orchestrator, :transfer_port_start)
    end_port = Application.fetch_env!(:cloud_orchestrator, :transfer_port_end)
    used = state |> Map.values() |> Enum.map(&get_in(&1, ["endpoint", "port"])) |> MapSet.new()

    Enum.find(start_port..end_port, start_port, fn port -> !MapSet.member?(used, port) end)
  end

  defp now(seconds \\ System.system_time(:second)) do
    seconds |> DateTime.from_unix!() |> DateTime.to_iso8601()
  end
end

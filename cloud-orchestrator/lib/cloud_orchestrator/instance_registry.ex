defmodule CloudOrchestrator.InstanceRegistry do
  use GenServer

  alias CloudOrchestrator.{Id, Token, TransferRegistry}

  def start_link(_opts) do
    GenServer.start_link(__MODULE__, %{}, name: __MODULE__)
  end

  def start_instance(params), do: GenServer.call(__MODULE__, {:start_instance, params}, 60_000)
  def get(id), do: GenServer.call(__MODULE__, {:get, id})
  def get_internal(id), do: GenServer.call(__MODULE__, {:get_internal, id})

  def export_instance(id, params),
    do: GenServer.call(__MODULE__, {:export_instance, id, params}, 60_000)

  def close_instance(id, params),
    do: GenServer.call(__MODULE__, {:close_instance, id, params}, 60_000)

  def handle_proxy_request(instance, conn, path),
    do: runner().handle_proxy_request(instance, conn, path)

  def count, do: GenServer.call(__MODULE__, :count)
  def reset, do: GenServer.call(__MODULE__, :reset)

  @impl true
  def init(_opts), do: {:ok, %{}}

  @impl true
  def handle_call({:start_instance, params}, _from, state) do
    with {:ok, transfer_id} <- transfer_id(params),
         {:ok, transfer} <- TransferRegistry.get(transfer_id),
         :ok <- require_ready(transfer) do
      instance = %{
        "instance_id" => Id.new("inst"),
        "session_id" => Map.get(params, "session_id"),
        "state" => "starting",
        "transfer_ref" => %{"transfer_id" => transfer_id},
        "transfer" => transfer,
        "created_at" => now()
      }

      case runner().start_instance(instance, params) do
        {:ok, started} ->
          token =
            Token.sign(%{
              "instance_id" => started["instance_id"],
              "session_id" => started["session_id"]
            })

          response = started |> public_instance() |> Map.put("token", token)
          {:reply, {:ok, response}, Map.put(state, started["instance_id"], started)}

        {:error, reason} ->
          {:reply, {:error, 500, %{error: "runner_start_failed", detail: inspect(reason)}}, state}
      end
    else
      {:error, :not_found} -> {:reply, {:error, 404, %{error: "transfer_not_found"}}, state}
      {:error, :not_ready} -> {:reply, {:error, 409, %{error: "transfer_not_ready"}}, state}
      {:error, reason} -> {:reply, {:error, 400, %{error: to_string(reason)}}, state}
    end
  end

  def handle_call({:get, id}, _from, state) do
    {:reply, state |> fetch(id) |> map_ok(&public_instance/1), state}
  end

  def handle_call({:get_internal, id}, _from, state) do
    {:reply, fetch(state, id), state}
  end

  def handle_call({:export_instance, id, params}, _from, state) do
    with {:ok, instance} <- fetch(state, id),
         {:ok, params} <- attach_transfer(params),
         {:ok, result} <- runner().export_instance(instance, params) do
      {:reply, {:ok, result}, state}
    else
      {:error, :not_found} ->
        {:reply, {:error, :not_found}, state}

      {:error, reason} ->
        {:reply, {:error, 500, %{error: "runner_export_failed", detail: inspect(reason)}}, state}
    end
  end

  def handle_call({:close_instance, id, params}, _from, state) do
    with {:ok, instance} <- fetch(state, id),
         {:ok, result} <- runner().close_instance(instance, params) do
      {:reply, {:ok, result}, Map.delete(state, id)}
    else
      {:error, :not_found} ->
        {:reply, {:error, :not_found}, state}

      {:error, reason} ->
        {:reply, {:error, 500, %{error: "runner_close_failed", detail: inspect(reason)}}, state}
    end
  end

  def handle_call(:count, _from, state), do: {:reply, map_size(state), state}
  def handle_call(:reset, _from, _state), do: {:reply, :ok, %{}}

  defp transfer_id(%{"transfer_ref" => %{"transfer_id" => id}}) when is_binary(id), do: {:ok, id}
  defp transfer_id(_params), do: {:error, :missing_transfer_id}

  defp attach_transfer(%{"transfer_ref" => %{"transfer_id" => id}} = params) when is_binary(id) do
    case TransferRegistry.get(id) do
      {:ok, transfer} -> {:ok, Map.put(params, "transfer", transfer)}
      error -> error
    end
  end

  defp attach_transfer(params), do: {:ok, params}

  defp require_ready(%{"state" => "ready"}), do: :ok
  defp require_ready(_), do: {:error, :not_ready}

  defp runner do
    Application.fetch_env!(:cloud_orchestrator, :runner)
  end

  defp fetch(state, id) do
    case Map.fetch(state, id) do
      {:ok, instance} -> {:ok, instance}
      :error -> {:error, :not_found}
    end
  end

  defp map_ok({:ok, value}, mapper), do: {:ok, mapper.(value)}
  defp map_ok(other, _mapper), do: other

  defp public_instance(instance) do
    Map.drop(instance, [
      "container_id",
      "proxy_base_url",
      "transfer",
      "instance_path",
      "instance_host_path",
      "workspace_path",
      "workspace_host_path"
    ])
  end

  defp now do
    System.system_time(:second) |> DateTime.from_unix!() |> DateTime.to_iso8601()
  end
end

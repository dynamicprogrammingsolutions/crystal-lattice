defmodule CloudOrchestrator.InstanceRegistry do
  use GenServer

  alias CloudOrchestrator.{Id, Token, TransferRegistry}
  import Plug.Conn

  def start_link(_opts) do
    GenServer.start_link(__MODULE__, %{}, name: __MODULE__)
  end

  def start_instance(params), do: GenServer.call(__MODULE__, {:start_instance, params}, 60_000)
  def get(id), do: GenServer.call(__MODULE__, {:get, id})
  def get_internal(id), do: GenServer.call(__MODULE__, {:get_internal, id})

  def update_startup(instance_id, attrs),
    do: GenServer.cast(__MODULE__, {:update_startup, instance_id, attrs})

  def mark_running(instance_id, attrs),
    do: GenServer.cast(__MODULE__, {:mark_running, instance_id, attrs})

  def mark_failed(instance_id, attrs),
    do: GenServer.cast(__MODULE__, {:mark_failed, instance_id, attrs})

  def export_instance(id, params),
    do: GenServer.call(__MODULE__, {:export_instance, id, params}, 60_000)

  def mark_sync_applied(id, params),
    do: GenServer.call(__MODULE__, {:mark_sync_applied, id, params}, 60_000)

  def close_instance(id, params),
    do: GenServer.call(__MODULE__, {:close_instance, id, params}, 60_000)

  def handle_proxy_request(%{"state" => "running"} = instance, conn, path),
    do: runner().handle_proxy_request(instance, conn, path)

  def handle_proxy_request(instance, conn, _path) do
    conn
    |> put_resp_content_type("application/json")
    |> send_resp(
      503,
      Jason.encode!(%{
        error: "runtime_not_ready",
        instance: public_instance(instance)
      })
    )
  end

  def handle_proxy_request_result(%{"state" => "running"} = instance, conn, path),
    do: runner().handle_proxy_request_result(instance, conn, path)

  def handle_proxy_request_result(instance, _conn, _path) do
    {:ok,
     %{
       status: 503,
       headers: [{"content-type", "application/json"}],
       body:
         Jason.encode!(%{
           error: "runtime_not_ready",
           instance: public_instance(instance)
         })
     }}
  end

  def proxyable?(%{"state" => "running"}), do: true
  def proxyable?(_instance), do: false

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
        "connection_id" => Map.get(params, "connection_id"),
        "session_id" => Map.get(params, "session_id"),
        "state" => "starting",
        "startup_stage" => "container_starting",
        "transfer_ref" => %{"transfer_id" => transfer_id},
        "transfer" => transfer,
        "created_at" => now(),
        "updated_at" => now()
      }

      case runner().start_instance(instance, params) do
        {:ok, started} ->
          started =
            started
            |> Map.put_new(
              "startup_stage",
              if(started["state"] == "running", do: "ready", else: "container_started")
            )
            |> Map.put("updated_at", now())

          token =
            Token.sign(%{
              "instance_id" => started["instance_id"],
              "connection_id" => started["connection_id"],
              "session_id" => started["session_id"]
            })

          response = started |> public_instance() |> Map.put("token", token)
          maybe_start_readiness_monitor(started)
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
         :ok <- require_running(instance),
         {:ok, params} <- attach_transfer(params),
         {:ok, result} <- runner().export_instance(instance, params) do
      {:reply, {:ok, result}, state}
    else
      {:error, :not_found} ->
        {:reply, {:error, :not_found}, state}

      {:error, :runtime_not_ready, instance} ->
        {:reply,
         {:error, 503, %{error: "runtime_not_ready", instance: public_instance(instance)}}, state}

      {:error, reason} ->
        {:reply, {:error, 500, %{error: "runner_export_failed", detail: inspect(reason)}}, state}
    end
  end

  def handle_call({:mark_sync_applied, id, params}, _from, state) do
    with {:ok, instance} <- fetch(state, id),
         :ok <- require_running(instance),
         {:ok, result} <- runner().mark_sync_applied(instance, params) do
      {:reply, {:ok, result}, state}
    else
      {:error, :not_found} ->
        {:reply, {:error, :not_found}, state}

      {:error, :runtime_not_ready, instance} ->
        {:reply,
         {:error, 503, %{error: "runtime_not_ready", instance: public_instance(instance)}}, state}

      {:error, reason} ->
        {:reply, {:error, 500, %{error: "runner_sync_applied_failed", detail: inspect(reason)}},
         state}
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

  @impl true
  def handle_cast({:update_startup, instance_id, attrs}, state) do
    {:noreply, update_instance(state, instance_id, attrs)}
  end

  def handle_cast({:mark_running, instance_id, attrs}, state) do
    attrs =
      attrs
      |> Map.put("state", "running")
      |> Map.put("startup_stage", "ready")
      |> Map.put("ready_at", now())
      |> Map.delete("startup_error")
      |> Map.delete("startup_error_detail")

    {:noreply, update_instance(state, instance_id, attrs)}
  end

  def handle_cast({:mark_failed, instance_id, attrs}, state) do
    attrs =
      attrs
      |> Map.put("state", "failed")
      |> Map.put_new("startup_stage", "failed")
      |> Map.put("failed_at", now())

    {:noreply, update_instance(state, instance_id, attrs)}
  end

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

  defp require_running(%{"state" => "running"}), do: :ok
  defp require_running(instance), do: {:error, :runtime_not_ready, instance}

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

  defp maybe_start_readiness_monitor(%{"state" => "starting"} = instance) do
    Task.Supervisor.start_child(CloudOrchestrator.TaskSupervisor, fn ->
      monitor_readiness(instance, readiness_deadline())
    end)
  end

  defp maybe_start_readiness_monitor(_instance), do: :ok

  defp monitor_readiness(instance, deadline) do
    case runner().runtime_status(instance) do
      {:ready, attrs} ->
        mark_running(instance["instance_id"], attrs)

      {:failed, attrs} ->
        mark_failed(instance["instance_id"], attach_recent_logs(attrs, instance))

      {:starting, attrs} ->
        update_startup(instance["instance_id"], attrs)

        if System.monotonic_time(:millisecond) < deadline do
          Process.sleep(readiness_poll_interval_ms())
          monitor_readiness(instance, deadline)
        else
          detail =
            [
              "runtime did not become ready before timeout",
              runner().recent_logs(instance)
            ]
            |> Enum.filter(&is_binary/1)
            |> Enum.join("\n\n")

          mark_failed(instance["instance_id"], %{
            "startup_stage" => "readiness_timeout",
            "startup_error" => "runtime_readiness_timeout",
            "startup_error_detail" => detail
          })
        end

      {:error, reason} ->
        mark_failed(instance["instance_id"], %{
          "startup_stage" => "readiness_probe_failed",
          "startup_error" => "runtime_readiness_probe_failed",
          "startup_error_detail" => inspect(reason)
        })
    end
  end

  defp update_instance(state, instance_id, attrs) do
    case Map.fetch(state, instance_id) do
      {:ok, instance} ->
        Map.put(state, instance_id, Map.merge(instance, Map.put(attrs, "updated_at", now())))

      :error ->
        state
    end
  end

  defp attach_recent_logs(attrs, instance) do
    case runner().recent_logs(instance) do
      logs when is_binary(logs) and logs != "" ->
        Map.update(attrs, "startup_error_detail", logs, fn detail ->
          [detail, "Container logs:", logs]
          |> Enum.filter(&is_binary/1)
          |> Enum.join("\n\n")
        end)

      _ ->
        attrs
    end
  end

  defp readiness_deadline do
    System.monotonic_time(:millisecond) + runtime_ready_timeout_ms()
  end

  defp runtime_ready_timeout_ms do
    case System.get_env("CLOUD_ORCHESTRATOR_RUNTIME_READY_TIMEOUT_MS") ||
           System.get_env("CLOUD_ORCHESTRATOR_RUNTIME_START_TIMEOUT_MS") do
      nil -> 300_000
      raw -> String.to_integer(raw)
    end
  end

  defp readiness_poll_interval_ms do
    case System.get_env("CLOUD_ORCHESTRATOR_RUNTIME_READY_POLL_INTERVAL_MS") do
      nil -> 500
      raw -> String.to_integer(raw)
    end
  end

  defp now do
    System.system_time(:second) |> DateTime.from_unix!() |> DateTime.to_iso8601()
  end
end

defmodule CloudOrchestrator.Runner.Docker do
  @behaviour CloudOrchestrator.Runner

  alias CloudOrchestrator.Proxy

  @container_instance_dir "/cloud-agent/instance"
  @container_workspace_dir "/cloud-agent/instance/workspace"
  @container_sessions_dir "/cloud-agent/instance/sessions"
  @container_config_path "/cloud-agent/instance/config/config.json"
  @container_config_assets_dir "/cloud-agent/instance/config/assets"
  @container_cache_dir "/cloud-agent/cache"

  @impl true
  def start_instance(instance, params) do
    image =
      Map.get(params, "runtime_image") || System.get_env("CLOUD_AGENT_RUNTIME_IMAGE") ||
        "cloud-agent-runtime:latest"

    port = 30_000 + :rand.uniform(999)
    instance_path = instance_path(instance["instance_id"])
    instance_host_path = instance_host_path(instance["instance_id"])
    workspace_path = Path.join(instance_path, "workspace")
    workspace_host_path = Path.join(instance_host_path, "workspace")
    prepare_instance_layout!(instance_path)
    prepare_runtime_cache!()

    args = runtime_container_args(instance, params, port, image)

    case System.cmd("docker", args, stderr_to_stdout: true) do
      {container_id, 0} ->
        container_id = String.trim(container_id)
        proxy_base_url = "http://#{proxy_host()}:#{port}"

        {:ok,
         instance
         |> Map.put("state", "starting")
         |> Map.put("startup_stage", "container_started")
         |> Map.put("runner", "docker")
         |> Map.put("container_id", container_id)
         |> Map.put("instance_path", instance_path)
         |> Map.put("instance_host_path", instance_host_path)
         |> Map.put("workspace_path", workspace_path)
         |> Map.put("workspace_host_path", workspace_host_path)
         |> Map.put("proxy_base_url", proxy_base_url)}

      {output, code} ->
        {:error, "docker run failed with #{code}: #{output}"}
    end
  end

  @impl true
  def runtime_status(%{"proxy_base_url" => base_url}) when is_binary(base_url) do
    health_request = Finch.build(:get, "#{base_url}/health")

    case Finch.request(health_request, CloudOrchestrator.Finch, receive_timeout: 1_000) do
      {:ok, %{status: status}} when status in 200..299 ->
        ready_status(base_url)

      {:ok, %{status: status, body: body}} ->
        {:starting,
         %{
           "startup_stage" => "process_unhealthy",
           "startup_error_detail" => bounded(body),
           "runtime_health_status" => status
         }}

      {:error, reason} ->
        {:starting,
         %{
           "startup_stage" => "process_waiting",
           "startup_error_detail" => inspect(reason)
         }}
    end
  end

  def runtime_status(_instance), do: {:error, "instance is missing proxy_base_url"}

  @impl true
  def recent_logs(%{"container_id" => container_id}) when is_binary(container_id) do
    case System.cmd("docker", ["logs", "--tail", "200", container_id], stderr_to_stdout: true) do
      {output, 0} -> bounded(output)
      {output, code} -> bounded("docker logs failed with #{code}: #{output}")
    end
  end

  def recent_logs(_instance), do: nil

  def runtime_container_args(instance, _params, port, image) do
    name = "cloud-agent-" <> instance["instance_id"]
    transfer = instance["transfer"] || %{}
    transfer_host_path = transfer["slot_host_path"]
    instance_host_path = instance_host_path(instance["instance_id"])

    [
      "run",
      "-d",
      "--name",
      name,
      "-e",
      "CLOUD_AGENT_INSTANCE_DIR=#{@container_instance_dir}",
      "-e",
      "CLOUD_AGENT_WORKSPACE_DIR=#{@container_workspace_dir}",
      "-e",
      "CLOUD_AGENT_SESSIONS_DIR=#{@container_sessions_dir}",
      "-e",
      "CLOUD_AGENT_CONFIG_PATH=#{@container_config_path}",
      "-e",
      "CONFIG_DIR=#{@container_config_assets_dir}",
      "-e",
      "WORKING_DIR=#{@container_workspace_dir}",
      "-e",
      "CLOUD_WORKSPACE_DIR=#{@container_workspace_dir}",
      "-e",
      "TRANSFER_DIR=/transfer",
      "-e",
      "SESSION_DIR=#{@container_sessions_dir}",
      "-e",
      "SESSION_ID=#{instance["session_id"] || ""}",
      "-e",
      "CLOUD_AGENT_CACHE_DIR=#{@container_cache_dir}",
      "-e",
      "PIP_CACHE_DIR=#{@container_cache_dir}/pip",
      "-e",
      "XDG_CACHE_HOME=#{@container_cache_dir}/xdg",
      "-v",
      "#{instance_host_path}:#{@container_instance_dir}",
      "-v",
      "#{transfer_host_path}:/transfer:ro",
      "-v",
      "#{runtime_cache_host_path()}:#{@container_cache_dir}",
      "-p",
      "#{bind_host()}:#{port}:8000",
      image
    ]
  end

  @impl true
  def export_instance(instance, params) do
    with :ok <- maybe_export_workspace(instance, params["transfer"]) do
      {:ok,
       %{
         "instance_id" => instance["instance_id"],
         "transfer_ref" => Map.get(params, "transfer_ref")
       }}
    end
  end

  @impl true
  def mark_sync_applied(instance, _params) do
    with :ok <- maybe_mark_sync_applied(instance) do
      {:ok, %{"instance_id" => instance["instance_id"], "status" => "ok"}}
    end
  end

  @impl true
  def close_instance(instance, _params) do
    session = fetch_session(instance)

    if container_id = instance["container_id"] do
      System.cmd("docker", ["rm", "-f", container_id], stderr_to_stdout: true)
    end

    result = %{
      "instance_id" => instance["instance_id"],
      "state" => "closed",
      "session_id" => instance["session_id"]
    }

    {:ok, if(is_binary(session), do: Map.put(result, "session", session), else: result)}
  end

  @impl true
  def handle_proxy_request(instance, conn, path) do
    Proxy.forward(conn, instance, path)
  end

  @impl true
  def handle_proxy_request_result(instance, conn, path) do
    Proxy.forward_result(conn, instance, path)
  end

  defp instance_path(instance_id) do
    Path.join([Application.fetch_env!(:cloud_orchestrator, :data_dir), "instances", instance_id])
  end

  defp instance_host_path(instance_id) do
    Path.join([
      Application.fetch_env!(:cloud_orchestrator, :host_data_dir),
      "instances",
      instance_id
    ])
  end

  defp prepare_instance_layout!(instance_path) do
    for child <- [
          "workspace",
          "sessions",
          "config/assets",
          "env/runtime.env.d",
          "transfer",
          "logs",
          "state"
        ] do
      File.mkdir_p!(Path.join(instance_path, child))
    end
  end

  defp prepare_runtime_cache! do
    File.mkdir_p!(runtime_cache_host_path())
  end

  defp runtime_cache_host_path do
    System.get_env("CLOUD_ORCHESTRATOR_RUNTIME_CACHE_HOST_DIR") ||
      Path.join(Application.fetch_env!(:cloud_orchestrator, :host_data_dir), "runtime-cache")
  end

  defp proxy_host do
    System.get_env("CLOUD_ORCHESTRATOR_DOCKER_PROXY_HOST") || "127.0.0.1"
  end

  defp bind_host do
    System.get_env("CLOUD_ORCHESTRATOR_DOCKER_BIND_HOST") || "127.0.0.1"
  end

  defp fetch_session(%{"proxy_base_url" => base_url, "session_id" => session_id})
       when is_binary(base_url) and is_binary(session_id) do
    request =
      Finch.build(:get, "#{base_url}/cloud-agent/sessions/#{URI.encode(session_id)}/export")

    case Finch.request(request, CloudOrchestrator.Finch, receive_timeout: 10_000) do
      {:ok, %{status: 200, body: body}} -> body
      _ -> nil
    end
  end

  defp fetch_session(_instance), do: nil

  defp maybe_export_workspace(_instance, nil), do: :ok
  defp maybe_export_workspace(instance, transfer), do: export_workspace(instance, transfer)

  defp maybe_mark_sync_applied(%{"proxy_base_url" => base_url}) when is_binary(base_url) do
    request = Finch.build(:post, "#{base_url}/cloud-agent/runtime/sync-applied", [], "")

    case Finch.request(request, CloudOrchestrator.Finch, receive_timeout: 120_000) do
      {:ok, %{status: status}} when status in 200..299 ->
        :ok

      {:ok, %{status: status, body: body}} ->
        {:error, "runtime sync-applied failed with #{status}: #{bounded(body)}"}

      {:error, reason} ->
        {:error, "runtime sync-applied request failed: #{inspect(reason)}"}
    end
  end

  defp maybe_mark_sync_applied(_instance), do: {:error, "instance is missing proxy_base_url"}

  defp export_workspace(
         %{"proxy_base_url" => base_url, "instance_path" => instance_path},
         %{
           "slot_path" => slot_path
         }
       )
       when is_binary(base_url) and is_binary(instance_path) and is_binary(slot_path) do
    request = Finch.build(:post, "#{base_url}/cloud-agent/runtime/export")

    with {:ok, %{status: status, body: _body}} when status in 200..299 <-
           Finch.request(request, CloudOrchestrator.Finch, receive_timeout: 120_000),
         :ok <- replace_directory_contents(Path.join(instance_path, "transfer/export"), slot_path) do
      :ok
    else
      {:ok, %{status: status, body: body}} ->
        {:error, "workspace export failed with HTTP #{status}: #{body}"}

      {:error, reason} ->
        {:error, "workspace export failed: #{inspect(reason)}"}
    end
  end

  defp export_workspace(_instance, _transfer), do: nil

  defp replace_directory_contents(source, destination) do
    with true <- File.dir?(source),
         :ok <- File.mkdir_p(destination),
         :ok <- clear_directory(destination),
         {:ok, entries} <- File.ls(source) do
      Enum.reduce_while(entries, :ok, fn entry, :ok ->
        case File.cp_r(Path.join(source, entry), Path.join(destination, entry)) do
          {:ok, _} ->
            {:cont, :ok}

          {:error, reason, file} ->
            {:halt, {:error, "copy failed for #{file}: #{inspect(reason)}"}}
        end
      end)
    else
      false -> {:error, "runtime export directory does not exist: #{source}"}
      {:error, reason} -> {:error, reason}
    end
  end

  defp clear_directory(path) do
    case File.ls(path) do
      {:ok, entries} ->
        Enum.each(entries, fn entry -> File.rm_rf!(Path.join(path, entry)) end)
        :ok

      {:error, reason} ->
        {:error, reason}
    end
  end

  defp ready_status(base_url) do
    request = Finch.build(:get, "#{base_url}/cloud-agent/runtime/ready")

    case Finch.request(request, CloudOrchestrator.Finch, receive_timeout: 1_000) do
      {:ok, %{status: status, body: body}} when status in 200..299 ->
        {:ready, body |> decode_body() |> Map.put_new("startup_stage", "ready")}

      {:ok, %{status: status, body: body}} ->
        status_payload = decode_body(body)
        attrs = normalize_runtime_status(status_payload, status)

        if Map.get(attrs, "startup_error") do
          {:failed, attrs}
        else
          {:starting, attrs}
        end

      {:error, reason} ->
        {:starting,
         %{
           "startup_stage" => "readiness_waiting",
           "startup_error_detail" => inspect(reason)
         }}
    end
  end

  defp decode_body(body) when is_binary(body) do
    case Jason.decode(body) do
      {:ok, decoded} when is_map(decoded) -> decoded
      _ -> %{"startup_error_detail" => bounded(body)}
    end
  end

  defp decode_body(_body), do: %{}

  defp normalize_runtime_status(payload, http_status) do
    payload =
      case payload["detail"] do
        detail when is_map(detail) -> detail
        _ -> payload
      end

    stage = payload["startup_stage"] || payload["stage"] || "agent_application_initializing"
    error = payload["startup_error"] || payload["error"]
    detail = payload["startup_error_detail"] || payload["detail"]

    %{
      "startup_stage" => stage,
      "runtime_readiness_status" => http_status
    }
    |> maybe_put("startup_error", error)
    |> maybe_put("startup_error_detail", detail)
  end

  defp maybe_put(map, _key, nil), do: map
  defp maybe_put(map, _key, ""), do: map
  defp maybe_put(map, key, value), do: Map.put(map, key, bounded(value))

  defp bounded(value) when is_binary(value) do
    if byte_size(value) > 12_000 do
      binary_part(value, byte_size(value) - 12_000, 12_000)
    else
      value
    end
  end

  defp bounded(value), do: value |> inspect() |> bounded()
end

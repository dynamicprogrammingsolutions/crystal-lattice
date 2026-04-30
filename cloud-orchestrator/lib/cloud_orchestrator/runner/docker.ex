defmodule CloudOrchestrator.Runner.Docker do
  @behaviour CloudOrchestrator.Runner

  alias CloudOrchestrator.Proxy

  @container_instance_dir "/cloud-agent/instance"
  @container_workspace_dir "/cloud-agent/instance/workspace"
  @container_sessions_dir "/cloud-agent/instance/sessions"
  @container_config_path "/cloud-agent/instance/config/config.json"
  @container_config_assets_dir "/cloud-agent/instance/config/assets"

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

    args = runtime_container_args(instance, params, port, image)

    case System.cmd("docker", args, stderr_to_stdout: true) do
      {container_id, 0} ->
        container_id = String.trim(container_id)
        proxy_base_url = "http://#{proxy_host()}:#{port}"

        case wait_for_health(proxy_base_url) do
          :ok ->
            {:ok,
             instance
             |> Map.put("state", "running")
             |> Map.put("runner", "docker")
             |> Map.put("container_id", container_id)
             |> Map.put("instance_path", instance_path)
             |> Map.put("instance_host_path", instance_host_path)
             |> Map.put("workspace_path", workspace_path)
             |> Map.put("workspace_host_path", workspace_host_path)
             |> Map.put("proxy_base_url", proxy_base_url)}

          :timeout ->
            System.cmd("docker", ["rm", "-f", container_id], stderr_to_stdout: true)
            {:error, "runtime did not become healthy at #{proxy_base_url}"}
        end

      {output, code} ->
        {:error, "docker run failed with #{code}: #{output}"}
    end
  end

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
      "-v",
      "#{instance_host_path}:#{@container_instance_dir}",
      "-v",
      "#{transfer_host_path}:/transfer:ro",
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

  defp wait_for_health(base_url) do
    deadline = System.monotonic_time(:millisecond) + runtime_start_timeout_ms()
    do_wait_for_health(base_url, deadline)
  end

  defp runtime_start_timeout_ms do
    case System.get_env("CLOUD_ORCHESTRATOR_RUNTIME_START_TIMEOUT_MS") do
      nil -> 300_000
      raw -> String.to_integer(raw)
    end
  end

  defp do_wait_for_health(base_url, deadline) do
    request = Finch.build(:get, "#{base_url}/health")

    case Finch.request(request, CloudOrchestrator.Finch, receive_timeout: 1_000) do
      {:ok, %{status: status}} when status in 200..299 ->
        :ok

      _ ->
        if System.monotonic_time(:millisecond) < deadline do
          Process.sleep(500)
          do_wait_for_health(base_url, deadline)
        else
          :timeout
        end
    end
  end
end

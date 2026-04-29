defmodule CloudOrchestrator.Runner.Docker do
  @behaviour CloudOrchestrator.Runner

  @impl true
  def start_instance(instance, params) do
    image =
      Map.get(params, "runtime_image") || System.get_env("CLOUD_AGENT_RUNTIME_IMAGE") ||
        "cloud-agent-runtime:latest"

    name = "cloud-agent-" <> instance["instance_id"]
    port = 30_000 + :rand.uniform(999)
    transfer = instance["transfer"] || %{}
    transfer_host_path = transfer["slot_host_path"]
    workspace_path = workspace_path(instance["instance_id"])
    workspace_host_path = workspace_host_path(instance["instance_id"])
    File.mkdir_p!(workspace_path)

    args = [
      "run",
      "-d",
      "--name",
      name,
      "-e",
      "CLOUD_WORKSPACE_DIR=#{Application.fetch_env!(:cloud_orchestrator, :cloud_workspace_dir)}",
      "-e",
      "TRANSFER_DIR=/transfer",
      "-e",
      "SESSION_ID=#{instance["session_id"] || ""}",
      "-v",
      "#{workspace_host_path}:#{Application.fetch_env!(:cloud_orchestrator, :cloud_workspace_dir)}",
      "-v",
      "#{transfer_host_path}:/transfer:ro",
      "-p",
      "#{bind_host()}:#{port}:8000",
      image
    ]

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

  defp workspace_path(instance_id) do
    Path.join([Application.fetch_env!(:cloud_orchestrator, :data_dir), "workspaces", instance_id])
  end

  defp workspace_host_path(instance_id) do
    Path.join([
      Application.fetch_env!(:cloud_orchestrator, :host_data_dir),
      "workspaces",
      instance_id
    ])
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

  defp export_workspace(%{"workspace_path" => workspace_path}, %{
         "slot_path" => slot_path
       })
       when is_binary(workspace_path) and is_binary(slot_path) do
    File.mkdir_p!(slot_path)

    case System.cmd(
           "tar",
           ["-czf", Path.join(slot_path, "bundle.tar.gz"), "-C", workspace_path, "."],
           stderr_to_stdout: true
         ) do
      {_output, 0} -> :ok
      {output, code} -> {:error, "workspace export failed with #{code}: #{output}"}
    end
  end

  defp export_workspace(_instance, _transfer), do: nil

  defp wait_for_health(base_url) do
    deadline = System.monotonic_time(:millisecond) + 30_000
    do_wait_for_health(base_url, deadline)
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

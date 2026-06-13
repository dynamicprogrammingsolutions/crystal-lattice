defmodule CloudOrchestrator.TransferService.ManagedSSH do
  @moduledoc false

  def start(transfer, params, port) do
    image =
      System.get_env("CLOUD_ORCHESTRATOR_TRANSFER_SSH_IMAGE") || "cloud-agent-transfer-ssh:latest"

    name = "cloud-transfer-" <> transfer["transfer_id"]
    public_key = Map.get(params, "public_key")

    cond do
      !is_binary(public_key) or String.trim(public_key) == "" ->
        {:error, :missing_public_key}

      System.get_env("CLOUD_ORCHESTRATOR_FAKE_MANAGED_SSH") == "1" ->
        fake_start(params, port)

      true ->
        args = [
          "run",
          "-d",
          "--name",
          name,
          "--rm",
          "-e",
          "TRANSFER_PUBLIC_KEY=#{public_key}",
          "-v",
          "#{transfer["slot_host_path"]}:/transfer",
          "-p",
          "#{bind_host()}:#{port}:2222",
          image
        ]

        case System.cmd("docker", args, stderr_to_stdout: true) do
          {container_id, 0} ->
            container_id = String.trim(container_id)

            case wait_for_host_key(container_id) do
              {:ok, host_key} ->
                {:ok,
                 %{
                   "container_id" => container_id,
                   "endpoint" =>
                     endpoint_for(params)
                     |> Map.put("port", port)
                     |> Map.put("username", "transfer")
                     |> Map.put("path", ".")
                     |> Map.put("host_key", host_key)
                 }}

              {:error, reason} ->
                stop(%{"container_id" => container_id})
                {:error, reason}
            end

          {output, code} ->
            reason = "managed SSH container failed with #{code}: #{String.trim(output)}"

            if port_conflict_output?(output) do
              {:error, {:port_unavailable, reason}}
            else
              {:error, reason}
            end
        end
    end
  end

  def stop(%{"container_id" => container_id}) when is_binary(container_id) do
    System.cmd("docker", ["rm", "-f", container_id], stderr_to_stdout: true)
    :ok
  end

  def stop(_transfer), do: :ok

  defp endpoint_for(params) do
    %{
      "host" =>
        present(Map.get(params, "public_host")) ||
          present(Application.get_env(:cloud_orchestrator, :transfer_public_host)) ||
          host_from_public_url()
    }
  end

  defp present(value) when is_binary(value),
    do: if(String.trim(value) == "", do: nil, else: value)

  defp present(_value), do: nil

  defp wait_for_host_key(container_id) do
    deadline = System.monotonic_time(:millisecond) + 15_000
    do_wait_for_host_key(container_id, deadline)
  end

  defp do_wait_for_host_key(container_id, deadline) do
    case System.cmd(
           "docker",
           ["exec", container_id, "cat", "/etc/ssh/ssh_host_ed25519_key.pub"],
           stderr_to_stdout: true
         ) do
      {key, 0} ->
        [_type, _key | _rest] = String.split(String.trim(key), ~r/\s+/)
        {:ok, String.trim(key)}

      _ ->
        if System.monotonic_time(:millisecond) < deadline do
          Process.sleep(250)
          do_wait_for_host_key(container_id, deadline)
        else
          {:error, :host_key_timeout}
        end
    end
  rescue
    MatchError ->
      if System.monotonic_time(:millisecond) < deadline do
        Process.sleep(250)
        do_wait_for_host_key(container_id, deadline)
      else
        {:error, :host_key_timeout}
      end
  end

  defp bind_host do
    System.get_env("CLOUD_ORCHESTRATOR_TRANSFER_BIND_HOST") || "0.0.0.0"
  end

  defp fake_start(params, port) do
    if port in fake_busy_ports() do
      {:error,
       {:port_unavailable,
        "managed SSH container failed with 125: docker: Error response from daemon: Bind for #{bind_host()}:#{port} failed: port is already allocated."}}
    else
      {:ok,
       %{
         "container_id" => nil,
         "endpoint" =>
           endpoint_for(params)
           |> Map.put("port", port)
           |> Map.put("username", "transfer")
           |> Map.put("path", ".")
           |> Map.put(
             "host_key",
             "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFakeManagedSshHostKeyForTests"
           )
       }}
    end
  end

  defp fake_busy_ports do
    System.get_env("CLOUD_ORCHESTRATOR_FAKE_MANAGED_SSH_BUSY_PORTS", "")
    |> String.split(",", trim: true)
    |> Enum.flat_map(fn value ->
      case Integer.parse(String.trim(value)) do
        {port, ""} -> [port]
        _ -> []
      end
    end)
  end

  defp port_conflict_output?(output) do
    String.contains?(output, "port is already allocated") ||
      String.contains?(output, "address already in use")
  end

  defp host_from_public_url do
    public_url = Application.fetch_env!(:cloud_orchestrator, :public_url)
    URI.parse(public_url).host || "127.0.0.1"
  end
end

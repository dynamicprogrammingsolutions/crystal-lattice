defmodule CloudOrchestrator.BuildContextStore do
  @moduledoc false

  alias CloudOrchestrator.TransferRegistry

  def get(digest) when is_binary(digest) do
    path = context_path(digest)

    if File.dir?(path) do
      {:ok, public_context(digest, path)}
    else
      {:error, :not_found}
    end
  end

  def create(params) do
    with {:ok, digest} <- required_string(params, "digest"),
         {:ok, transfer_id} <- transfer_id(params),
         {:ok, transfer} <- TransferRegistry.get(transfer_id),
         :ok <- require_ready(transfer),
         {:ok, source_path} <- source_path(transfer, Map.get(params, "path", "context")),
         true <- File.dir?(source_path) do
      destination = context_path(digest)

      if File.dir?(destination) do
        {:ok, public_context(digest, destination)}
      else
        File.mkdir_p!(Path.dirname(destination))
        File.cp_r!(source_path, destination)
        {:ok, public_context(digest, destination)}
      end
    else
      {:error, :not_found} -> {:error, :transfer_not_found}
      {:error, :not_ready} -> {:error, :transfer_not_ready}
      {:error, :unsafe_path} -> {:error, :unsafe_path}
      false -> {:error, :build_context_not_found}
      error -> error
    end
  end

  defp public_context(digest, path) do
    %{
      "digest" => digest,
      "state" => "ready",
      "path" => path,
      "host_path" => context_host_path(digest)
    }
  end

  defp transfer_id(params) do
    case get_in(params, ["transfer_ref", "transfer_id"]) do
      value when is_binary(value) and value != "" -> {:ok, value}
      _ -> {:error, :missing_transfer_ref}
    end
  end

  defp required_string(params, key) do
    case Map.get(params, key) do
      value when is_binary(value) and value != "" -> {:ok, value}
      _ -> {:error, :"missing_#{key}"}
    end
  end

  defp require_ready(%{"state" => "ready"}), do: :ok
  defp require_ready(_transfer), do: {:error, :not_ready}

  defp source_path(transfer, raw_path) do
    slot_path = Path.expand(transfer["slot_path"])
    relative = if(is_binary(raw_path) and raw_path != "", do: raw_path, else: "context")
    candidate = Path.expand(Path.join(slot_path, relative))

    if candidate == slot_path or String.starts_with?(candidate, slot_path <> "/") do
      {:ok, candidate}
    else
      {:error, :unsafe_path}
    end
  end

  defp context_path(digest) do
    Path.join([
      Application.fetch_env!(:cloud_orchestrator, :data_dir),
      "build-contexts",
      safe_segment(digest),
      "context"
    ])
  end

  defp context_host_path(digest) do
    Path.join([
      Application.fetch_env!(:cloud_orchestrator, :host_data_dir),
      "build-contexts",
      safe_segment(digest),
      "context"
    ])
  end

  defp safe_segment(value) do
    value
    |> to_string()
    |> String.replace(~r/[^A-Za-z0-9_.:-]+/, "-")
    |> String.trim(".-")
    |> case do
      "" -> "default"
      segment -> segment
    end
  end
end

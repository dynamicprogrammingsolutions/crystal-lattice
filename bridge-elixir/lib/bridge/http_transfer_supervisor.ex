defmodule Bridge.HttpTransferSupervisor do
  use DynamicSupervisor

  def start_link(_options) do
    DynamicSupervisor.start_link(__MODULE__, :ok, name: __MODULE__)
  end

  @impl true
  def init(:ok) do
    DynamicSupervisor.init(
      strategy: :one_for_one,
      max_children: positive_env("BRIDGE_MAX_PENDING_HTTP_TRANSFERS", 128)
    )
  end

  defp positive_env(name, default) do
    case System.get_env(name) do
      nil ->
        default

      "" ->
        default

      value ->
        case Integer.parse(value) do
          {parsed, ""} when parsed > 0 -> parsed
          _ -> default
        end
    end
  end
end

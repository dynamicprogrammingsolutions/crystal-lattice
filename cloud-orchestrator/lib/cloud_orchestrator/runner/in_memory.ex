defmodule CloudOrchestrator.Runner.InMemory do
  @behaviour CloudOrchestrator.Runner

  @impl true
  def start_instance(instance, _params) do
    {:ok,
     instance
     |> Map.put("state", "running")
     |> Map.put("proxy_base_url", "http://127.0.0.1:9")
     |> Map.put("runner", "memory")}
  end

  @impl true
  def export_instance(instance, params) do
    {:ok,
     %{
       "instance_id" => instance["instance_id"],
       "transfer_ref" => Map.get(params, "transfer_ref")
     }}
  end

  @impl true
  def close_instance(instance, _params) do
    {:ok, %{"instance_id" => instance["instance_id"], "state" => "closed"}}
  end
end

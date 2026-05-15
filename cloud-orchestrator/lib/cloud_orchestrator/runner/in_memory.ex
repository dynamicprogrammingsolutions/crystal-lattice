defmodule CloudOrchestrator.Runner.InMemory do
  @behaviour CloudOrchestrator.Runner

  import Plug.Conn

  @impl true
  def start_instance(instance, _params) do
    {:ok,
     instance
     |> Map.put("state", "running")
     |> Map.put("startup_stage", "ready")
     |> Map.put("proxy_base_url", "http://127.0.0.1:9")
     |> Map.put("runner", "memory")}
  end

  @impl true
  def runtime_status(_instance), do: {:ready, %{"startup_stage" => "ready"}}

  @impl true
  def recent_logs(_instance), do: nil

  @impl true
  def export_instance(instance, params) do
    {:ok,
     %{
       "instance_id" => instance["instance_id"],
       "transfer_ref" => Map.get(params, "transfer_ref")
     }}
  end

  @impl true
  def mark_sync_applied(instance, _params) do
    {:ok, %{"instance_id" => instance["instance_id"], "status" => "ok"}}
  end

  @impl true
  def close_instance(instance, _params) do
    {:ok, %{"instance_id" => instance["instance_id"], "state" => "closed"}}
  end

  @impl true
  def handle_proxy_request(_instance, conn, _path) do
    conn
    |> put_resp_content_type("application/json")
    |> send_resp(501, Jason.encode!(%{error: "memory_runner_not_proxyable"}))
  end

  @impl true
  def handle_proxy_request_result(_instance, _conn, _path) do
    {:ok,
     %{
       status: 501,
       headers: [{"content-type", "application/json"}],
       body: Jason.encode!(%{error: "memory_runner_not_proxyable"})
     }}
  end
end

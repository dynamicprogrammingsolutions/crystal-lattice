defmodule CloudOrchestrator.TestSessionCreateRunner do
  @behaviour CloudOrchestrator.Runner

  alias CloudOrchestrator.Proxy
  import Plug.Conn

  @impl true
  def start_instance(instance, _params) do
    {:ok,
     instance
     |> Map.put("state", "running")
     |> Map.put("startup_stage", "ready")
     |> Map.put(
       "proxy_base_url",
       Application.fetch_env!(:cloud_orchestrator, :test_proxy_base_url)
     )
     |> Map.put("runner", "test_session_create")}
  end

  @impl true
  def runtime_status(_instance), do: {:ready, %{"startup_stage" => "ready"}}

  @impl true
  def recent_logs(_instance), do: nil

  @impl true
  def export_instance(instance, params) do
    {:ok, %{"instance_id" => instance["instance_id"], "transfer_ref" => params["transfer_ref"]}}
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
  def handle_proxy_request(instance, conn, path), do: Proxy.forward(conn, instance, path)

  @impl true
  def handle_proxy_request_result(instance, conn, path),
    do: Proxy.forward_result(conn, instance, path)
end

defmodule CloudOrchestrator.TestSessionRuntime do
  use Plug.Router

  plug(:match)
  plug(:dispatch)

  post "/sessions" do
    send_json(conn, 201, %{
      "session" => %{"session_id" => "session-cloud-created", "agent_id" => "default"}
    })
  end

  get "/sessions" do
    send_json(conn, 200, %{
      "sessions" => [
        %{"session_id" => "session-original"},
        %{"session_id" => "session-cloud-created"},
        %{"session_id" => "session-unrouted"}
      ]
    })
  end

  match _ do
    send_json(conn, 404, %{error: "not_found"})
  end

  defp send_json(conn, status, data) do
    conn
    |> put_resp_content_type("application/json")
    |> send_resp(status, Jason.encode!(data))
  end
end

defmodule CloudOrchestrator.RouterTest do
  use ExUnit.Case
  import Plug.Conn
  import Plug.Test

  @opts CloudOrchestrator.Endpoint.init([])

  setup do
    System.put_env("CLOUD_ORCHESTRATOR_FAKE_MANAGED_SSH", "1")
    previous_runner = Application.get_env(:cloud_orchestrator, :runner)
    previous_proxy_base_url = Application.get_env(:cloud_orchestrator, :test_proxy_base_url)
    CloudOrchestrator.TransferRegistry.reset()
    CloudOrchestrator.InstanceRegistry.reset()
    CloudOrchestrator.ConnectionRegistry.reset()

    on_exit(fn ->
      restore_env(:runner, previous_runner)
      restore_env(:test_proxy_base_url, previous_proxy_base_url)
      CloudOrchestrator.TransferRegistry.reset()
      CloudOrchestrator.InstanceRegistry.reset()
      CloudOrchestrator.ConnectionRegistry.reset()
      System.delete_env("CLOUD_ORCHESTRATOR_FAKE_MANAGED_SSH")
    end)

    :ok
  end

  test "health returns service status" do
    conn = conn(:get, "/health")
    conn = CloudOrchestrator.Endpoint.call(conn, @opts)

    assert conn.status == 200

    assert %{"status" => "healthy", "service" => "cloud-orchestrator"} =
             Jason.decode!(conn.resp_body)
  end

  test "transfer and instance lifecycle through HTTP" do
    conn =
      conn(
        :post,
        "/transfers",
        Jason.encode!(%{
          "direction" => "upload",
          "public_key" => "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKey test"
        })
      )
      |> put_req_header("content-type", "application/json")

    conn = CloudOrchestrator.Endpoint.call(conn, @opts)
    assert conn.status == 201
    transfer = Jason.decode!(conn.resp_body)

    ready_conn = conn(:post, "/transfers/#{transfer["transfer_id"]}/ready")
    ready_conn = CloudOrchestrator.Endpoint.call(ready_conn, @opts)
    assert ready_conn.status == 200

    instance_conn =
      conn(
        :post,
        "/instances",
        Jason.encode!(%{
          "session_id" => "session-1",
          "transfer_ref" => %{"transfer_id" => transfer["transfer_id"]}
        })
      )
      |> put_req_header("content-type", "application/json")

    instance_conn = CloudOrchestrator.Endpoint.call(instance_conn, @opts)
    assert instance_conn.status == 201
    instance = Jason.decode!(instance_conn.resp_body)
    assert instance["state"] == "running"
    assert is_binary(instance["token"])

    sync_applied_conn =
      conn(:post, "/instances/#{instance["instance_id"]}/sync-applied", Jason.encode!(%{}))
      |> put_req_header("content-type", "application/json")
      |> CloudOrchestrator.Endpoint.call(@opts)

    assert sync_applied_conn.status == 200
    assert %{"status" => "ok"} = Jason.decode!(sync_applied_conn.resp_body)
  end

  test "proxy route validates token and delegates request handling to runner" do
    transfer_conn =
      conn(
        :post,
        "/transfers",
        Jason.encode!(%{
          "direction" => "upload",
          "public_key" => "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKey test"
        })
      )
      |> put_req_header("content-type", "application/json")
      |> CloudOrchestrator.Endpoint.call(@opts)

    transfer = Jason.decode!(transfer_conn.resp_body)

    conn(:post, "/transfers/#{transfer["transfer_id"]}/ready")
    |> CloudOrchestrator.Endpoint.call(@opts)

    instance_conn =
      conn(
        :post,
        "/instances",
        Jason.encode!(%{
          "session_id" => "session-1",
          "transfer_ref" => %{"transfer_id" => transfer["transfer_id"]}
        })
      )
      |> put_req_header("content-type", "application/json")
      |> CloudOrchestrator.Endpoint.call(@opts)

    instance = Jason.decode!(instance_conn.resp_body)

    proxy_conn =
      conn(:get, "/instances/#{instance["instance_id"]}/proxy/agents")
      |> put_req_header("authorization", "Bearer #{instance["token"]}")
      |> CloudOrchestrator.Endpoint.call(@opts)

    assert proxy_conn.status == 501
    assert %{"error" => "memory_runner_not_proxyable"} = Jason.decode!(proxy_conn.resp_body)
  end

  test "connection proxy route resolves session routes and keeps instance proxy compatibility" do
    transfer_1 = create_ready_transfer()
    transfer_2 = create_ready_transfer()

    instance_1 =
      create_instance(%{
        "connection_ref" => %{"connection_key" => "router-shared", "reuse" => true},
        "session_id" => "session-1",
        "transfer_ref" => %{"transfer_id" => transfer_1["transfer_id"]}
      })

    instance_2 =
      create_instance(%{
        "connection_ref" => %{"connection_key" => "router-shared", "reuse" => true},
        "session_id" => "session-2",
        "transfer_ref" => %{"transfer_id" => transfer_2["transfer_id"]}
      })

    assert instance_1["connection_id"] == instance_2["connection_id"]
    assert instance_1["instance_id"] != instance_2["instance_id"]

    unauthorized =
      conn(:get, "/connections/#{instance_1["connection_id"]}/proxy/sessions/session-1/messages")
      |> put_req_header("authorization", "Bearer #{instance_2["token"] <> "bad"}")
      |> CloudOrchestrator.Endpoint.call(@opts)

    assert unauthorized.status == 401

    routed =
      conn(:get, "/connections/#{instance_1["connection_id"]}/proxy/sessions/session-2/messages")
      |> put_req_header("authorization", "Bearer #{instance_1["token"]}")
      |> CloudOrchestrator.Endpoint.call(@opts)

    assert routed.status == 501
    assert %{"error" => "memory_runner_not_proxyable"} = Jason.decode!(routed.resp_body)

    legacy =
      conn(:get, "/instances/#{instance_1["instance_id"]}/proxy/agents")
      |> put_req_header("authorization", "Bearer #{instance_1["token"]}")
      |> CloudOrchestrator.Endpoint.call(@opts)

    assert legacy.status == 501
  end

  test "connection proxy falls back from failed default to newer running instance" do
    transfer_1 = create_ready_transfer()
    transfer_2 = create_ready_transfer()

    instance_1 =
      create_instance(%{
        "connection_ref" => %{"connection_key" => "router-default-fallback", "reuse" => true},
        "session_id" => "session-failed-default",
        "transfer_ref" => %{"transfer_id" => transfer_1["transfer_id"]}
      })

    CloudOrchestrator.InstanceRegistry.mark_failed(instance_1["instance_id"], %{
      "startup_error" => "test_failure"
    })

    assert eventually(fn ->
             {:ok, failed} =
               CloudOrchestrator.InstanceRegistry.get(instance_1["instance_id"])

             failed["state"] == "failed"
           end)

    instance_2 =
      create_instance(%{
        "connection_ref" => %{"connection_key" => "router-default-fallback", "reuse" => true},
        "session_id" => "session-running",
        "transfer_ref" => %{"transfer_id" => transfer_2["transfer_id"]}
      })

    assert instance_1["connection_id"] == instance_2["connection_id"]

    proxied =
      conn(:post, "/connections/#{instance_1["connection_id"]}/proxy/actions", Jason.encode!(%{}))
      |> put_req_header("authorization", "Bearer #{instance_1["token"]}")
      |> put_req_header("content-type", "application/json")
      |> CloudOrchestrator.Endpoint.call(@opts)

    assert proxied.status == 501
    assert %{"error" => "memory_runner_not_proxyable"} = Jason.decode!(proxied.resp_body)
  end

  test "connection proxy registers sessions created by proxied POST sessions" do
    base_url = start_test_session_runtime!()
    Application.put_env(:cloud_orchestrator, :runner, CloudOrchestrator.TestSessionCreateRunner)
    Application.put_env(:cloud_orchestrator, :test_proxy_base_url, base_url)

    transfer = create_ready_transfer()

    instance =
      create_instance(%{
        "connection_ref" => %{"connection_key" => "created-session-routing", "reuse" => true},
        "session_id" => "session-original",
        "transfer_ref" => %{"transfer_id" => transfer["transfer_id"]}
      })

    created =
      conn(
        :post,
        "/connections/#{instance["connection_id"]}/proxy/sessions",
        Jason.encode!(%{"agent_id" => "default"})
      )
      |> put_req_header("authorization", "Bearer #{instance["token"]}")
      |> put_req_header("content-type", "application/json")
      |> CloudOrchestrator.Endpoint.call(@opts)

    assert created.status == 201

    assert %{"session" => %{"session_id" => "session-cloud-created"}} =
             Jason.decode!(created.resp_body)

    assert {:ok, routed} =
             CloudOrchestrator.ConnectionRegistry.resolve_route(
               instance["connection_id"],
               "session-cloud-created"
             )

    assert routed["instance_id"] == instance["instance_id"]

    listed =
      conn(:get, "/connections/#{instance["connection_id"]}/sessions")
      |> put_req_header("authorization", "Bearer #{instance["token"]}")
      |> CloudOrchestrator.Endpoint.call(@opts)

    assert listed.status == 200

    session_ids =
      listed.resp_body
      |> Jason.decode!()
      |> Map.fetch!("sessions")
      |> Enum.map(& &1["session_id"])

    assert "session-original" in session_ids
    assert "session-cloud-created" in session_ids
    refute "session-unrouted" in session_ids
  end

  test "control token protects mutation routes when configured" do
    previous = Application.get_env(:cloud_orchestrator, :control_token)
    Application.put_env(:cloud_orchestrator, :control_token, "secret")

    try do
      unauthorized =
        conn(
          :post,
          "/transfers",
          Jason.encode!(%{
            "direction" => "upload",
            "public_key" => "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKey test"
          })
        )
        |> put_req_header("content-type", "application/json")
        |> CloudOrchestrator.Endpoint.call(@opts)

      assert unauthorized.status == 401

      authorized =
        conn(
          :post,
          "/transfers",
          Jason.encode!(%{
            "direction" => "upload",
            "public_key" => "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKey test"
          })
        )
        |> put_req_header("content-type", "application/json")
        |> put_req_header("authorization", "Bearer secret")
        |> CloudOrchestrator.Endpoint.call(@opts)

      assert authorized.status == 201
    after
      Application.put_env(:cloud_orchestrator, :control_token, previous)
    end
  end

  test "does not expose HTTP bundle transfer routes" do
    transfer_conn =
      conn(
        :post,
        "/transfers",
        Jason.encode!(%{
          "direction" => "upload",
          "public_key" => "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKey test"
        })
      )
      |> put_req_header("content-type", "application/json")
      |> CloudOrchestrator.Endpoint.call(@opts)

    transfer = Jason.decode!(transfer_conn.resp_body)

    upload_conn =
      conn(:put, "/transfers/#{transfer["transfer_id"]}/upload", "bundle")
      |> put_req_header("content-type", "application/gzip")
      |> CloudOrchestrator.Endpoint.call(@opts)

    assert upload_conn.status == 404
  end

  defp create_ready_transfer do
    transfer_conn =
      conn(
        :post,
        "/transfers",
        Jason.encode!(%{
          "direction" => "upload",
          "public_key" => "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKey test"
        })
      )
      |> put_req_header("content-type", "application/json")
      |> CloudOrchestrator.Endpoint.call(@opts)

    transfer = Jason.decode!(transfer_conn.resp_body)

    conn(:post, "/transfers/#{transfer["transfer_id"]}/ready")
    |> CloudOrchestrator.Endpoint.call(@opts)

    transfer
  end

  defp create_instance(payload) do
    conn(:post, "/instances", Jason.encode!(payload))
    |> put_req_header("content-type", "application/json")
    |> CloudOrchestrator.Endpoint.call(@opts)
    |> then(fn conn ->
      assert conn.status == 201
      Jason.decode!(conn.resp_body)
    end)
  end

  defp start_test_session_runtime! do
    ref = :"test_session_runtime_#{System.unique_integer([:positive])}"
    {:ok, _pid} = Plug.Cowboy.http(CloudOrchestrator.TestSessionRuntime, [], port: 0, ref: ref)
    port = :ranch.get_port(ref)

    on_exit(fn ->
      Plug.Cowboy.shutdown(ref)
    end)

    "http://127.0.0.1:#{port}"
  end

  defp restore_env(key, nil), do: Application.delete_env(:cloud_orchestrator, key)
  defp restore_env(key, value), do: Application.put_env(:cloud_orchestrator, key, value)

  defp eventually(predicate) do
    deadline = System.monotonic_time(:millisecond) + 2_000
    eventually(predicate, deadline)
  end

  defp eventually(predicate, deadline) do
    if predicate.() do
      true
    else
      if System.monotonic_time(:millisecond) < deadline do
        Process.sleep(25)
        eventually(predicate, deadline)
      else
        false
      end
    end
  end
end

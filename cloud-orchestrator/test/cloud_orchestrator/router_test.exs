defmodule CloudOrchestrator.RouterTest do
  use ExUnit.Case
  import Plug.Conn
  import Plug.Test

  @opts CloudOrchestrator.Endpoint.init([])

  setup do
    System.put_env("CLOUD_ORCHESTRATOR_FAKE_MANAGED_SSH", "1")
    CloudOrchestrator.TransferRegistry.reset()
    CloudOrchestrator.InstanceRegistry.reset()
    CloudOrchestrator.ConnectionRegistry.reset()

    on_exit(fn ->
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
end

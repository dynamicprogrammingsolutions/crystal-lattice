defmodule CloudOrchestrator.RouterTest do
  use ExUnit.Case
  import Plug.Conn
  import Plug.Test

  @opts CloudOrchestrator.Endpoint.init([])

  setup do
    CloudOrchestrator.TransferRegistry.reset()
    CloudOrchestrator.InstanceRegistry.reset()
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
      conn(:post, "/transfers", Jason.encode!(%{"direction" => "upload"}))
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

  test "control token protects mutation routes when configured" do
    previous = Application.get_env(:cloud_orchestrator, :control_token)
    Application.put_env(:cloud_orchestrator, :control_token, "secret")

    try do
      unauthorized =
        conn(:post, "/transfers", Jason.encode!(%{"direction" => "upload"}))
        |> put_req_header("content-type", "application/json")
        |> CloudOrchestrator.Endpoint.call(@opts)

      assert unauthorized.status == 401

      authorized =
        conn(:post, "/transfers", Jason.encode!(%{"direction" => "upload"}))
        |> put_req_header("content-type", "application/json")
        |> put_req_header("authorization", "Bearer secret")
        |> CloudOrchestrator.Endpoint.call(@opts)

      assert authorized.status == 201
    after
      Application.put_env(:cloud_orchestrator, :control_token, previous)
    end
  end

  test "uploads a default transfer bundle into an opaque transfer slot" do
    transfer_conn =
      conn(:post, "/transfers", Jason.encode!(%{"direction" => "upload"}))
      |> put_req_header("content-type", "application/json")
      |> CloudOrchestrator.Endpoint.call(@opts)

    transfer = Jason.decode!(transfer_conn.resp_body)

    upload_conn =
      conn(:put, "/transfers/#{transfer["transfer_id"]}/upload", "bundle")
      |> put_req_header("content-type", "application/gzip")
      |> CloudOrchestrator.Endpoint.call(@opts)

    assert upload_conn.status == 200
    uploaded = Jason.decode!(upload_conn.resp_body)
    assert uploaded["state"] == "uploaded"
  end
end

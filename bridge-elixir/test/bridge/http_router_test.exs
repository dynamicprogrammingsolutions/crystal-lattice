defmodule Bridge.HttpRouterTest do
  use ExUnit.Case, async: false
  import Plug.Conn
  import Plug.Test

  @opts Bridge.HttpRouter.init([])

  setup do
    :ets.delete_all_objects(:bridge_servers)
    :ets.delete_all_objects(:bridge_pairing_codes)
    :ets.delete_all_objects(:bridge_sessions)
    :ok
  end

  test "capabilities advertise opt-in HTTP transfer support" do
    conn =
      conn(:get, "/bridge/v1/capabilities")
      |> Bridge.HttpRouter.call(@opts)

    assert conn.status == 200

    assert Jason.decode!(conn.resp_body) == %{
             "protocol_version" => 1,
             "http_proxy" => true,
             "request_body_download" => true,
             "response_body_upload" => true,
             "modes" => ["http", "hybrid"]
           }
  end

  test "HTTP pairing issues a token and resume validates the server" do
    %{server_id: server_id, server_pid: server_pid} = register_server()
    client_id = UUID.uuid4()

    request_conn =
      json_conn(:post, "/bridge/v1/pairings/request", %{
        server_id: server_id,
        client_id: client_id
      })
      |> Bridge.HttpRouter.call(@opts)

    assert request_conn.status == 200
    request_body = Jason.decode!(request_conn.resp_body)
    assert is_binary(request_body["pairing_request_token"])
    assert_receive {:server_message, {:pairing_requested, ^client_id, code, _expires_at}}

    confirm_conn =
      json_conn(:post, "/bridge/v1/pairings/confirm", %{
        pairing_request_token: request_body["pairing_request_token"],
        code: code
      })
      |> Bridge.HttpRouter.call(@opts)

    assert confirm_conn.status == 200
    pairing_token = Jason.decode!(confirm_conn.resp_body)["pairing_token"]
    assert is_binary(pairing_token)

    resume_conn =
      json_conn(:post, "/bridge/v1/pairings/resume", %{server_id: server_id})
      |> put_req_header("x-crystal-bridge-token", pairing_token)
      |> Bridge.HttpRouter.call(@opts)

    assert resume_conn.status == 200
    assert Jason.decode!(resume_conn.resp_body)["server_id"] == server_id

    stop_server(server_id, server_pid)
  end

  test "HTTP proxy streams raw response bytes from the server upload" do
    %{server_id: server_id, server_pid: server_pid} = register_server()
    {:ok, pairing_token} = Bridge.PairingToken.issue(server_id, UUID.uuid4())

    frontend_task =
      Task.async(fn ->
        conn(:get, "/bridge/v1/proxy/binary?value=1")
        |> put_req_header("x-crystal-bridge-token", pairing_token)
        |> Bridge.HttpRouter.call(@opts)
      end)

    assert_receive {:server_message, {:http_request_v2, request}}, 1_000
    assert request.path == "/binary?value=1"
    assert request.request_body_present == false
    refute Map.has_key?(request, :body)

    Phoenix.PubSub.broadcast(
      Bridge.PubSub,
      Bridge.HttpTransfer.topic(request.request_id),
      {:http_response_v2_init, server_id,
       %{
         "status" => 200,
         "headers" => %{
           "content-type" => "application/octet-stream",
           "content-length" => "999"
         }
       }}
    )

    payload = <<0, 1, 2, 255, 10, 20>>

    upload_task =
      Task.async(fn ->
        conn(
          :put,
          request.response_body_path,
          payload
        )
        |> put_req_header(
          "authorization",
          "Bearer #{request.response_body_token}"
        )
        |> Bridge.HttpRouter.call(@opts)
      end)

    frontend_conn = Task.await(frontend_task, 2_000)
    upload_conn = Task.await(upload_task, 2_000)

    assert frontend_conn.status == 200
    assert IO.iodata_to_binary(frontend_conn.resp_body) == payload
    assert get_resp_header(frontend_conn, "content-length") == []
    assert upload_conn.status == 204

    stop_server(server_id, server_pid)
  end

  test "HTTP proxy exposes request bodies to the server as raw bytes" do
    %{server_id: server_id, server_pid: server_pid} = register_server()
    {:ok, pairing_token} = Bridge.PairingToken.issue(server_id, UUID.uuid4())
    payload = <<255, 0, 42, 10, 99>>

    frontend_task =
      Task.async(fn ->
        conn(:post, "/bridge/v1/proxy/upload", payload)
        |> put_req_header("content-type", "application/octet-stream")
        |> put_req_header("content-length", Integer.to_string(byte_size(payload)))
        |> put_req_header("x-crystal-bridge-token", pairing_token)
        |> Bridge.HttpRouter.call(@opts)
      end)

    assert_receive {:server_message, {:http_request_v2, request}}, 1_000
    assert request.request_body_present == true
    refute Map.has_key?(request.headers, "x-crystal-bridge-token")
    refute Map.has_key?(request.headers, "x-crystal-bridge-body-present")

    download_task =
      Task.async(fn ->
        conn(:get, request.request_body_path)
        |> put_req_header(
          "authorization",
          "Bearer #{request.request_body_token}"
        )
        |> Bridge.HttpRouter.call(@opts)
      end)

    download_conn = Task.await(download_task, 2_000)
    assert download_conn.status == 200
    assert IO.iodata_to_binary(download_conn.resp_body) == payload

    replay_conn =
      conn(:get, request.request_body_path)
      |> put_req_header(
        "authorization",
        "Bearer #{request.request_body_token}"
      )
      |> Bridge.HttpRouter.call(@opts)

    assert replay_conn.status == 401
    assert Jason.decode!(replay_conn.resp_body)["error"] == "already_consumed"

    Phoenix.PubSub.broadcast(
      Bridge.PubSub,
      Bridge.HttpTransfer.topic(request.request_id),
      {:http_response_v2_init, server_id,
       %{
         "status" => 201,
         "headers" => %{"content-type" => "application/json"}
       }}
    )

    upload_task =
      Task.async(fn ->
        conn(:put, request.response_body_path, ~s({"ok":true}))
        |> put_req_header(
          "authorization",
          "Bearer #{request.response_body_token}"
        )
        |> Bridge.HttpRouter.call(@opts)
      end)

    frontend_conn = Task.await(frontend_task, 2_000)
    upload_conn = Task.await(upload_task, 2_000)
    assert frontend_conn.status == 201
    assert IO.iodata_to_binary(frontend_conn.resp_body) == ~s({"ok":true})
    assert upload_conn.status == 204

    stop_server(server_id, server_pid)
  end

  defp register_server do
    test_pid = self()
    server_id = UUID.uuid4()

    server_pid =
      spawn(fn ->
        server_loop(test_pid)
      end)

    assert {:ok, _} =
             Bridge.ServerRegistry.register_server(server_id, %{
               display_name: "HTTP Test Server",
               computer_name: "test.local",
               location: nil,
               channel_pid: server_pid
             })

    on_exit(fn -> stop_server(server_id, server_pid) end)
    %{server_id: server_id, server_pid: server_pid}
  end

  defp server_loop(test_pid) do
    receive do
      :stop ->
        :ok

      message ->
        send(test_pid, {:server_message, message})
        server_loop(test_pid)
    end
  end

  defp stop_server(server_id, server_pid) do
    Bridge.ServerRegistry.unregister_server(server_id, server_pid)
    send(server_pid, :stop)
  end

  defp json_conn(method, path, body) do
    conn(method, path, Jason.encode!(body))
    |> put_req_header("content-type", "application/json")
  end
end

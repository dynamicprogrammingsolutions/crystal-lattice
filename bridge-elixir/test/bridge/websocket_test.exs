defmodule Bridge.WebSocketTest do
  use ExUnit.Case, async: false

  alias Bridge.TestClient

  @moduletag :websocket

  setup do
    server_id = UUID.uuid4()
    client_id = UUID.uuid4()

    :ets.delete_all_objects(:bridge_servers)
    :ets.delete_all_objects(:bridge_pairing_codes)
    :ets.delete_all_objects(:bridge_sessions)

    {:ok, server_id: server_id, client_id: client_id}
  end

  @tag :skip
  test "server can register", %{server_id: server_id} do
    {:ok, server_pid} = TestClient.start_server_client("ws://localhost:4002", server_id, self())
    
    assert_receive {:connected, :server}, 1000

    TestClient.register_server(server_pid, server_id, "Test Server", "test.local")

    assert_receive {:message, :server, %{"type" => "register_ack"}}, 2000

    Process.sleep(100)
    assert {:ok, _info} = Bridge.ServerRegistry.get_server(server_id)

    WebSockex.cast(server_pid, :close)
  end

  @tag :skip
  test "app can list servers", %{server_id: server_id, client_id: client_id} do
    {:ok, server_pid} = TestClient.start_server_client("ws://localhost:4002", server_id, self())
    assert_receive {:connected, :server}, 1000

    TestClient.register_server(server_pid, server_id, "Test Server", "test.local", "NYC")
    Process.sleep(200)

    {:ok, app_pid} = TestClient.start_app_client("ws://localhost:4002", client_id, self())
    assert_receive {:connected, :app}, 1000

    TestClient.list_servers(app_pid)

    assert_receive {:message, :app, %{"type" => "server_list", "servers" => servers}}, 2000
    assert length(servers) >= 1
    assert Enum.any?(servers, fn s -> s["server_id"] == server_id end)

    WebSockex.cast(server_pid, :close)
    WebSockex.cast(app_pid, :close)
  end

  @tag :skip
  test "full pairing flow", %{server_id: server_id, client_id: client_id} do
    {:ok, server_pid} = TestClient.start_server_client("ws://localhost:4002", server_id, self())
    assert_receive {:connected, :server}, 1000

    TestClient.register_server(server_pid, server_id, "Test Server", "test.local")
    Process.sleep(200)

    {:ok, app_pid} = TestClient.start_app_client("ws://localhost:4002", client_id, self())
    assert_receive {:connected, :app}, 1000

    TestClient.pair_request(app_pid, server_id)

    assert_receive {:message, :server, %{"type" => "pairing_requested", "code" => code}}, 2000

    TestClient.pair_submit(app_pid, server_id, code)

    assert_receive {:message, :app, %{"type" => "paired", "session_id" => _session_id}}, 2000

    WebSockex.cast(server_pid, :close)
    WebSockex.cast(app_pid, :close)
  end
end

defmodule Bridge.SingleTargetRoutingTest do
  use ExUnit.Case, async: false

  defp start_channel_process(id, test_pid) do
    spawn(fn ->
      receive_loop(id, test_pid)
    end)
  end

  defp receive_loop(id, test_pid) do
    receive do
      :stop ->
        :ok

      msg ->
        send(test_pid, {:channel_received, id, msg})
        receive_loop(id, test_pid)
    end
  end

  defp stop_channel_process(pid) do
    send(pid, :stop)
  end

  setup do
    :ets.delete_all_objects(:bridge_servers)
    :ets.delete_all_objects(:bridge_sessions)
    :ok
  end

  test "duplicate register takes over and supersedes old pid" do
    server_id = UUID.uuid4()
    old_pid = start_channel_process(:old, self())
    new_pid = start_channel_process(:new, self())

    assert {:ok, :registered} =
             Bridge.ServerRegistry.register_server(server_id, %{
               display_name: "Server",
               computer_name: "old.local",
               location: nil,
               channel_pid: old_pid
             })

    assert {:ok, {:took_over, ^old_pid}} =
             Bridge.ServerRegistry.register_server(server_id, %{
               display_name: "Server",
               computer_name: "new.local",
               location: nil,
               channel_pid: new_pid
             })

    assert_receive {:channel_received, :old, {:superseded, ^server_id, ^new_pid}}, 1000

    assert {:ok, info} = Bridge.ServerRegistry.get_server(server_id)
    assert info.channel_pid == new_pid

    # Old pid should not be able to unregister the new one
    assert :ok = Bridge.ServerRegistry.unregister_server(server_id, old_pid)
    assert {:ok, info_after} = Bridge.ServerRegistry.get_server(server_id)
    assert info_after.channel_pid == new_pid

    assert :ok = Bridge.ServerRegistry.unregister_server(server_id, new_pid)
    stop_channel_process(old_pid)
    stop_channel_process(new_pid)
  end

  test "duplicate register can be rejected" do
    server_id = UUID.uuid4()
    old_pid = start_channel_process(:old, self())
    new_pid = start_channel_process(:new, self())

    assert {:ok, :registered} =
             Bridge.ServerRegistry.register_server(server_id, %{
               display_name: "Server",
               computer_name: "old.local",
               location: nil,
               channel_pid: old_pid
             })

    assert {:error, :already_registered} =
             Bridge.ServerRegistry.register_server(
               server_id,
               %{
                 display_name: "Server",
                 computer_name: "new.local",
                 location: nil,
                 channel_pid: new_pid
               },
               conflict_policy: :reject
             )

    assert {:ok, info} = Bridge.ServerRegistry.get_server(server_id)
    assert info.channel_pid == old_pid

    assert :ok = Bridge.ServerRegistry.unregister_server(server_id, old_pid)
    stop_channel_process(old_pid)
    stop_channel_process(new_pid)
  end

  test "app channel routes chunked http_request_init to only active server" do
    server_id = UUID.uuid4()
    client_id = UUID.uuid4()

    old_pid = start_channel_process(:old, self())
    new_pid = start_channel_process(:new, self())

    Bridge.ServerRegistry.register_server(server_id, %{
      display_name: "Server",
      computer_name: "old.local",
      location: nil,
      channel_pid: old_pid
    })

    Bridge.ServerRegistry.register_server(server_id, %{
      display_name: "Server",
      computer_name: "new.local",
      location: nil,
      channel_pid: new_pid
    })

    {:ok, session_id} = Bridge.SessionManager.create_session(server_id, client_id, node(), node())

    # Drain any session pairing message delivered to the active server.
    assert_receive {:channel_received, :new, {:paired, ^client_id, ^session_id}}, 1000

    request_id = UUID.uuid4()

    socket = %Phoenix.Socket{}

    assert {:reply, {:ok, %{status: "accepted"}}, _socket} =
             Bridge.AppChannel.handle_in(
               "http_request_init",
               %{
                 "request_id" => request_id,
                 "session_id" => session_id,
                 "method" => "POST",
                 "path" => "/api/test",
                 "headers" => %{}
               },
               socket
             )

    assert_receive {:channel_received, :new, {:http_request_init, req}}, 1000
    assert req.request_id == request_id
    assert req.method == "POST"
    assert req.path == "/api/test"

    refute_receive {:channel_received, :old, {:http_request_init, _req}}, 50

    Bridge.ServerRegistry.unregister_server(server_id, new_pid)
    stop_channel_process(old_pid)
    stop_channel_process(new_pid)
  end

  test "DOWN cleanup unregisters dead server" do
    Phoenix.PubSub.subscribe(Bridge.PubSub, "servers:registry")

    server_id = UUID.uuid4()
    dead_pid = start_channel_process(:dead, self())

    assert {:ok, :registered} =
             Bridge.ServerRegistry.register_server(server_id, %{
               display_name: "Server",
               computer_name: "dead.local",
               location: nil,
               channel_pid: dead_pid
             })

    Process.exit(dead_pid, :kill)

    assert_receive {:server_unregistered, ^server_id, ^dead_pid}, 1000
    assert {:error, :not_found} = Bridge.ServerRegistry.get_server(server_id)
  end
end

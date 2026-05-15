defmodule Bridge.AppChannelResumeTest do
  use ExUnit.Case, async: false

  defp start_server_process(test_pid) do
    spawn(fn -> receive_loop(test_pid) end)
  end

  defp receive_loop(test_pid) do
    receive do
      :stop ->
        :ok

      msg ->
        send(test_pid, {:server_received, msg})
        receive_loop(test_pid)
    end
  end

  defp stop_server_process(pid), do: send(pid, :stop)

  setup do
    :ets.delete_all_objects(:bridge_servers)
    :ets.delete_all_objects(:bridge_sessions)

    :ok
  end

  test "resume_session verifies token and creates a fresh ephemeral session" do
    server_id = UUID.uuid4()
    client_id = UUID.uuid4()
    channel_pid = start_server_process(self())

    Bridge.ServerRegistry.register_server(server_id, %{
      display_name: "Test Server",
      computer_name: "test.local",
      location: nil,
      channel_pid: channel_pid
    })

    {:ok, token} = Bridge.PersistentPairingManager.create_or_get_token(server_id, client_id)

    {:ok, first_session_id} =
      Bridge.SessionManager.create_session(server_id, client_id, node(), node())

    assert_receive {:server_received, {:paired, ^client_id, ^first_session_id}}, 1000

    socket = %Phoenix.Socket{assigns: %{client_id: client_id}}

    assert {:reply, {:ok, %{session_id: second_session_id}}, _socket} =
             Bridge.AppChannel.handle_in(
               "resume_session",
               %{"pairing_token" => token, "server_id" => server_id},
               socket
             )

    assert is_binary(second_session_id)
    assert second_session_id != first_session_id
    assert {:ok, session} = Bridge.SessionManager.get_session(second_session_id)
    assert session.server_id == server_id
    assert session.client_id == client_id

    assert_receive {:server_received, {:paired, ^client_id, ^second_session_id}}, 1000

    Bridge.ServerRegistry.unregister_server(server_id, channel_pid)
    stop_server_process(channel_pid)
  end

  test "resume_session rejects a token routed to a different server id" do
    client_id = UUID.uuid4()
    token_server_id = UUID.uuid4()
    requested_server_id = UUID.uuid4()
    socket = %Phoenix.Socket{assigns: %{client_id: client_id}}

    {:ok, token} = Bridge.PersistentPairingManager.create_or_get_token(token_server_id, client_id)

    assert {:reply, {:error, %{reason: "server_mismatch"}}, _socket} =
             Bridge.AppChannel.handle_in(
               "resume_session",
               %{"pairing_token" => token, "server_id" => requested_server_id},
               socket
             )
  end

  test "resume_session rejects invalid pairing tokens" do
    socket = %Phoenix.Socket{assigns: %{client_id: UUID.uuid4()}}

    assert {:reply, {:error, %{reason: "invalid_pairing_token"}}, _socket} =
             Bridge.AppChannel.handle_in(
               "resume_session",
               %{"pairing_token" => "bad-token"},
               socket
             )
  end
end
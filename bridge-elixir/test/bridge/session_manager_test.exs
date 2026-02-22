defmodule Bridge.SessionManagerTest do
  use ExUnit.Case, async: false

  defp start_server_process(test_pid) do
    spawn(fn ->
      receive_loop(test_pid)
    end)
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

  defp stop_server_process(pid) do
    send(pid, :stop)
  end

  setup do
    :ets.delete_all_objects(:bridge_sessions)
    :ets.delete_all_objects(:bridge_servers)
    :ok
  end

  describe "create_session/4" do
    test "creates a new session" do
      server_id = UUID.uuid4()
      client_id = UUID.uuid4()

      channel_pid = start_server_process(self())

      Bridge.ServerRegistry.register_server(server_id, %{
        display_name: "Test Server",
        computer_name: "test.local",
        location: nil,
        channel_pid: channel_pid
      })

      {:ok, session_id} =
        Bridge.SessionManager.create_session(
          server_id,
          client_id,
          node(),
          node()
        )

      assert is_binary(session_id)
      assert {:ok, session} = Bridge.SessionManager.get_session(session_id)
      assert session.server_id == server_id
      assert session.client_id == client_id

      Bridge.ServerRegistry.unregister_server(server_id, channel_pid)
      stop_server_process(channel_pid)
    end

    test "broadcasts pairing success" do
      server_id = UUID.uuid4()
      client_id = UUID.uuid4()

      channel_pid = start_server_process(self())

      Bridge.ServerRegistry.register_server(server_id, %{
        display_name: "Test Server",
        computer_name: "test.local",
        location: nil,
        channel_pid: channel_pid
      })

      {:ok, session_id} =
        Bridge.SessionManager.create_session(
          server_id,
          client_id,
          node(),
          node()
        )

      assert_receive {:server_received, {:paired, ^client_id, ^session_id}}, 1000

      Bridge.ServerRegistry.unregister_server(server_id, channel_pid)
      stop_server_process(channel_pid)
    end
  end

  describe "get_session/1" do
    test "returns existing session" do
      server_id = UUID.uuid4()
      client_id = UUID.uuid4()

      channel_pid = start_server_process(self())

      Bridge.ServerRegistry.register_server(server_id, %{
        display_name: "Test Server",
        computer_name: "test.local",
        location: nil,
        channel_pid: channel_pid
      })

      {:ok, session_id} =
        Bridge.SessionManager.create_session(
          server_id,
          client_id,
          node(),
          node()
        )

      assert {:ok, session} = Bridge.SessionManager.get_session(session_id)
      assert session.session_id == session_id

      Bridge.ServerRegistry.unregister_server(server_id, channel_pid)
      stop_server_process(channel_pid)
    end

    test "returns error for non-existent session" do
      assert {:error, :not_found} = Bridge.SessionManager.get_session("invalid-id")
    end
  end

  describe "update_activity/1" do
    test "updates last activity timestamp" do
      server_id = UUID.uuid4()
      client_id = UUID.uuid4()

      channel_pid = start_server_process(self())

      Bridge.ServerRegistry.register_server(server_id, %{
        display_name: "Test Server",
        computer_name: "test.local",
        location: nil,
        channel_pid: channel_pid
      })

      {:ok, session_id} =
        Bridge.SessionManager.create_session(
          server_id,
          client_id,
          node(),
          node()
        )

      {:ok, session1} = Bridge.SessionManager.get_session(session_id)

      Process.sleep(100)

      Bridge.SessionManager.update_activity(session_id)

      # Wait for async cast to complete
      Process.sleep(50)

      {:ok, session2} = Bridge.SessionManager.get_session(session_id)

      assert DateTime.compare(session2.last_activity, session1.last_activity) == :gt

      Bridge.ServerRegistry.unregister_server(server_id, channel_pid)
      stop_server_process(channel_pid)
    end
  end

  describe "delete_session/1" do
    test "removes session" do
      server_id = UUID.uuid4()
      client_id = UUID.uuid4()

      channel_pid = start_server_process(self())

      Bridge.ServerRegistry.register_server(server_id, %{
        display_name: "Test Server",
        computer_name: "test.local",
        location: nil,
        channel_pid: channel_pid
      })

      {:ok, session_id} =
        Bridge.SessionManager.create_session(
          server_id,
          client_id,
          node(),
          node()
        )

      assert {:ok, _} = Bridge.SessionManager.get_session(session_id)

      Bridge.SessionManager.delete_session(session_id)

      assert {:error, :not_found} = Bridge.SessionManager.get_session(session_id)

      Bridge.ServerRegistry.unregister_server(server_id, channel_pid)
      stop_server_process(channel_pid)
    end
  end

  describe "count_sessions/0" do
    test "returns correct count" do
      assert Bridge.SessionManager.count_sessions() == 0

      server_id = UUID.uuid4()
      channel_pid = start_server_process(self())

      Bridge.ServerRegistry.register_server(server_id, %{
        display_name: "Test Server",
        computer_name: "test.local",
        location: nil,
        channel_pid: channel_pid
      })

      Bridge.SessionManager.create_session(
        server_id,
        UUID.uuid4(),
        node(),
        node()
      )

      assert Bridge.SessionManager.count_sessions() == 1

      Bridge.ServerRegistry.unregister_server(server_id, channel_pid)
      stop_server_process(channel_pid)
    end
  end
end

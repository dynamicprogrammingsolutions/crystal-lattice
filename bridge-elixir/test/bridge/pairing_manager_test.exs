defmodule Bridge.PairingManagerTest do
  use ExUnit.Case, async: false

  defp start_server_process do
    test_pid = self()

    spawn(fn ->
      receive_loop(test_pid)
    end)
  end

  defp receive_loop(test_pid) do
    receive do
      :stop ->
        :ok

      msg ->
        send(test_pid, msg)
        receive_loop(test_pid)
    end
  end

  defp stop_server_process(pid) do
    send(pid, :stop)
  end

  setup do
    :ets.delete_all_objects(:bridge_pairing_codes)
    :ets.delete_all_objects(:bridge_servers)
    :ok
  end

  describe "create_pairing_request/2" do
    test "generates a 6-digit code" do
      server_id = UUID.uuid4()
      client_id = UUID.uuid4()

      channel_pid = start_server_process()

      Bridge.ServerRegistry.register_server(server_id, %{
        display_name: "Test Server",
        computer_name: "test.local",
        location: nil,
        channel_pid: channel_pid
      })

      {:ok, code, _expires_at} =
        Bridge.PairingManager.create_pairing_request(server_id, client_id)

      assert String.length(code) == 6
      assert String.match?(code, ~r/^\d{6}$/)

      Bridge.ServerRegistry.unregister_server(server_id, channel_pid)
      stop_server_process(channel_pid)
    end

    test "broadcasts pairing request" do
      server_id = UUID.uuid4()
      client_id = UUID.uuid4()

      channel_pid = start_server_process()

      Bridge.ServerRegistry.register_server(server_id, %{
        display_name: "Test Server",
        computer_name: "test.local",
        location: nil,
        channel_pid: channel_pid
      })

      {:ok, code, expires_at} = Bridge.PairingManager.create_pairing_request(server_id, client_id)

      assert_receive {:pairing_requested, ^client_id, ^code, ^expires_at}, 1000

      Bridge.ServerRegistry.unregister_server(server_id, channel_pid)
      stop_server_process(channel_pid)
    end
  end

  describe "validate_code/3" do
    test "accepts correct code" do
      server_id = UUID.uuid4()
      client_id = UUID.uuid4()

      channel_pid = start_server_process()

      Bridge.ServerRegistry.register_server(server_id, %{
        display_name: "Test Server",
        computer_name: "test.local",
        location: nil,
        channel_pid: channel_pid
      })

      {:ok, code, _} = Bridge.PairingManager.create_pairing_request(server_id, client_id)

      assert :ok = Bridge.PairingManager.validate_code(server_id, client_id, code)

      Bridge.ServerRegistry.unregister_server(server_id, channel_pid)
      stop_server_process(channel_pid)
    end

    test "rejects incorrect code" do
      server_id = UUID.uuid4()
      client_id = UUID.uuid4()

      channel_pid = start_server_process()

      Bridge.ServerRegistry.register_server(server_id, %{
        display_name: "Test Server",
        computer_name: "test.local",
        location: nil,
        channel_pid: channel_pid
      })

      Bridge.PairingManager.create_pairing_request(server_id, client_id)

      assert {:error, :invalid_code} =
               Bridge.PairingManager.validate_code(server_id, client_id, "999999")

      Bridge.ServerRegistry.unregister_server(server_id, channel_pid)
      stop_server_process(channel_pid)
    end

    test "tracks failed attempts" do
      server_id = UUID.uuid4()
      client_id = UUID.uuid4()

      channel_pid = start_server_process()

      Bridge.ServerRegistry.register_server(server_id, %{
        display_name: "Test Server",
        computer_name: "test.local",
        location: nil,
        channel_pid: channel_pid
      })

      Bridge.PairingManager.create_pairing_request(server_id, client_id)

      assert {:error, :invalid_code} =
               Bridge.PairingManager.validate_code(server_id, client_id, "111111")

      assert {:error, :invalid_code} =
               Bridge.PairingManager.validate_code(server_id, client_id, "222222")

      assert {:error, :invalid_code} =
               Bridge.PairingManager.validate_code(server_id, client_id, "333333")

      assert {:error, :too_many_attempts} =
               Bridge.PairingManager.validate_code(server_id, client_id, "444444")

      Bridge.ServerRegistry.unregister_server(server_id, channel_pid)
      stop_server_process(channel_pid)
    end

    test "returns error for non-existent pairing" do
      server_id = UUID.uuid4()
      client_id = UUID.uuid4()

      assert {:error, :not_found} =
               Bridge.PairingManager.validate_code(server_id, client_id, "123456")
    end
  end

  describe "cancel_pairing/2" do
    test "removes pairing request" do
      server_id = UUID.uuid4()
      client_id = UUID.uuid4()

      channel_pid = start_server_process()

      Bridge.ServerRegistry.register_server(server_id, %{
        display_name: "Test Server",
        computer_name: "test.local",
        location: nil,
        channel_pid: channel_pid
      })

      {:ok, code, _} = Bridge.PairingManager.create_pairing_request(server_id, client_id)

      Bridge.PairingManager.cancel_pairing(server_id, client_id)

      assert {:error, :not_found} =
               Bridge.PairingManager.validate_code(server_id, client_id, code)

      Bridge.ServerRegistry.unregister_server(server_id, channel_pid)
      stop_server_process(channel_pid)
    end
  end
end

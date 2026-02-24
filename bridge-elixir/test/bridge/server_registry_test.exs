defmodule Bridge.ServerRegistryTest do
  use ExUnit.Case, async: false

  defp start_server_process do
    spawn(fn ->
      receive do
        :stop ->
          :ok
      end
    end)
  end

  defp stop_server_process(pid) do
    send(pid, :stop)
  end

  setup do
    :ets.delete_all_objects(:bridge_servers)
    :ok
  end

  describe "register_server/2" do
    test "registers a server with metadata" do
      server_id = UUID.uuid4()
      channel_pid = start_server_process()

      info = %{
        display_name: "Test Server",
        computer_name: "test-computer.local",
        location: "Test Location",
        channel_pid: channel_pid
      }

      assert {:ok, :registered} = Bridge.ServerRegistry.register_server(server_id, info)
      assert {:ok, server_info} = Bridge.ServerRegistry.get_server(server_id)
      assert server_info.display_name == "Test Server"
      assert server_info.node == node()

      assert :ok = Bridge.ServerRegistry.unregister_server(server_id, channel_pid)
      stop_server_process(channel_pid)
    end

    test "broadcasts registration to cluster" do
      Phoenix.PubSub.subscribe(Bridge.PubSub, "servers:registry")

      server_id = UUID.uuid4()
      channel_pid = start_server_process()

      info = %{
        display_name: "Test Server",
        computer_name: "test-computer.local",
        location: nil,
        channel_pid: channel_pid
      }

      Bridge.ServerRegistry.register_server(server_id, info)

      assert_receive {:server_registered, ^server_id, _info}, 1000

      assert :ok = Bridge.ServerRegistry.unregister_server(server_id, channel_pid)
      stop_server_process(channel_pid)
    end
  end

  describe "unregister_server/1" do
    test "removes server from registry" do
      server_id = UUID.uuid4()
      channel_pid = start_server_process()

      info = %{
        display_name: "Test Server",
        computer_name: "test-computer.local",
        location: nil,
        channel_pid: channel_pid
      }

      Bridge.ServerRegistry.register_server(server_id, info)
      assert {:ok, _} = Bridge.ServerRegistry.get_server(server_id)

      Bridge.ServerRegistry.unregister_server(server_id, channel_pid)
      assert {:error, :not_found} = Bridge.ServerRegistry.get_server(server_id)

      stop_server_process(channel_pid)
    end

    test "broadcasts unregistration to cluster" do
      Phoenix.PubSub.subscribe(Bridge.PubSub, "servers:registry")

      server_id = UUID.uuid4()
      channel_pid = start_server_process()

      info = %{
        display_name: "Test Server",
        computer_name: "test-computer.local",
        location: nil,
        channel_pid: channel_pid
      }

      Bridge.ServerRegistry.register_server(server_id, info)
      Bridge.ServerRegistry.unregister_server(server_id, channel_pid)

      assert_receive {:server_unregistered, ^server_id, ^channel_pid}, 1000

      stop_server_process(channel_pid)
    end
  end

  describe "list_servers/0" do
    test "returns all registered servers" do
      server1_id = UUID.uuid4()
      server2_id = UUID.uuid4()

      channel1_pid = start_server_process()
      channel2_pid = start_server_process()

      Bridge.ServerRegistry.register_server(server1_id, %{
        display_name: "Server 1",
        computer_name: "server1.local",
        location: nil,
        channel_pid: channel1_pid
      })

      Bridge.ServerRegistry.register_server(server2_id, %{
        display_name: "Server 2",
        computer_name: "server2.local",
        location: "NYC",
        channel_pid: channel2_pid
      })

      servers = Bridge.ServerRegistry.list_servers()
      assert length(servers) == 2
      assert Enum.any?(servers, fn s -> s.server_id == server1_id end)
      assert Enum.any?(servers, fn s -> s.server_id == server2_id end)

      Bridge.ServerRegistry.unregister_server(server1_id, channel1_pid)
      Bridge.ServerRegistry.unregister_server(server2_id, channel2_pid)
      stop_server_process(channel1_pid)
      stop_server_process(channel2_pid)
    end
  end

  describe "count_servers/0" do
    test "returns correct count" do
      assert Bridge.ServerRegistry.count_servers() == 0

      server_id = UUID.uuid4()
      channel_pid = start_server_process()

      Bridge.ServerRegistry.register_server(server_id, %{
        display_name: "Server 1",
        computer_name: "server1.local",
        location: nil,
        channel_pid: channel_pid
      })

      assert Bridge.ServerRegistry.count_servers() == 1

      Bridge.ServerRegistry.unregister_server(server_id, channel_pid)
      stop_server_process(channel_pid)
    end
  end
end

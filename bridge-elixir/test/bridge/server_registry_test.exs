defmodule Bridge.ServerRegistryTest do
  use ExUnit.Case, async: false

  setup do
    :ets.delete_all_objects(:bridge_servers)
    :ok
  end

  describe "register_server/2" do
    test "registers a server with metadata" do
      server_id = UUID.uuid4()
      info = %{
        display_name: "Test Server",
        computer_name: "test-computer.local",
        location: "Test Location"
      }

      assert :ok = Bridge.ServerRegistry.register_server(server_id, info)
      assert {:ok, server_info} = Bridge.ServerRegistry.get_server(server_id)
      assert server_info.display_name == "Test Server"
      assert server_info.node == node()
    end

    test "broadcasts registration to cluster" do
      Phoenix.PubSub.subscribe(Bridge.PubSub, "servers:registry")
      
      server_id = UUID.uuid4()
      info = %{
        display_name: "Test Server",
        computer_name: "test-computer.local",
        location: nil
      }

      Bridge.ServerRegistry.register_server(server_id, info)

      assert_receive {:server_registered, ^server_id, _info}, 1000
    end
  end

  describe "unregister_server/1" do
    test "removes server from registry" do
      server_id = UUID.uuid4()
      info = %{
        display_name: "Test Server",
        computer_name: "test-computer.local",
        location: nil
      }

      Bridge.ServerRegistry.register_server(server_id, info)
      assert {:ok, _} = Bridge.ServerRegistry.get_server(server_id)

      Bridge.ServerRegistry.unregister_server(server_id)
      assert {:error, :not_found} = Bridge.ServerRegistry.get_server(server_id)
    end

    test "broadcasts unregistration to cluster" do
      Phoenix.PubSub.subscribe(Bridge.PubSub, "servers:registry")
      
      server_id = UUID.uuid4()
      info = %{
        display_name: "Test Server",
        computer_name: "test-computer.local",
        location: nil
      }

      Bridge.ServerRegistry.register_server(server_id, info)
      Bridge.ServerRegistry.unregister_server(server_id)

      assert_receive {:server_unregistered, ^server_id}, 1000
    end
  end

  describe "list_servers/0" do
    test "returns all registered servers" do
      server1_id = UUID.uuid4()
      server2_id = UUID.uuid4()

      Bridge.ServerRegistry.register_server(server1_id, %{
        display_name: "Server 1",
        computer_name: "server1.local",
        location: nil
      })

      Bridge.ServerRegistry.register_server(server2_id, %{
        display_name: "Server 2",
        computer_name: "server2.local",
        location: "NYC"
      })

      servers = Bridge.ServerRegistry.list_servers()
      assert length(servers) == 2
      assert Enum.any?(servers, fn s -> s.server_id == server1_id end)
      assert Enum.any?(servers, fn s -> s.server_id == server2_id end)
    end
  end

  describe "count_servers/0" do
    test "returns correct count" do
      assert Bridge.ServerRegistry.count_servers() == 0

      Bridge.ServerRegistry.register_server(UUID.uuid4(), %{
        display_name: "Server 1",
        computer_name: "server1.local",
        location: nil
      })

      assert Bridge.ServerRegistry.count_servers() == 1
    end
  end
end

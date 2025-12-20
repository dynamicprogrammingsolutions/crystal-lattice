defmodule Bridge.PersistentPairingManagerTest do
  use ExUnit.Case, async: false

  setup do
    :ets.delete_all_objects(:bridge_pairings_by_token)
    :ets.delete_all_objects(:bridge_pairings_by_key)
    :ok
  end

  test "create_or_get_token returns stable token per server/client" do
    server_id = UUID.uuid4()
    client_id = UUID.uuid4()

    {:ok, token1} = Bridge.PersistentPairingManager.create_or_get_token(server_id, client_id)
    {:ok, token2} = Bridge.PersistentPairingManager.create_or_get_token(server_id, client_id)

    assert token1 == token2

    assert {:ok, pairing} = Bridge.PersistentPairingManager.get_by_token(token1)
    assert pairing.server_id == server_id
    assert pairing.client_id == client_id
  end

  test "get_by_token returns error for unknown token" do
    assert {:error, :not_found} = Bridge.PersistentPairingManager.get_by_token("non-existent-token")
  end
end

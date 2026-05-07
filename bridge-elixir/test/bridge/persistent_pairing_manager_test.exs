defmodule Bridge.PersistentPairingManagerTest do
  use ExUnit.Case, async: false

  setup do
    previous_secret = Application.get_env(:bridge, :pairing_token_secret)
    previous_salt = Application.get_env(:bridge, :pairing_token_salt)
    previous_ttl = Application.get_env(:bridge, :pairing_token_ttl_seconds)

    Application.put_env(:bridge, :pairing_token_secret, "bridge-test-pairing-token-secret")
    Application.put_env(:bridge, :pairing_token_salt, "pairing-token-test-v1")
    Application.put_env(:bridge, :pairing_token_ttl_seconds, 2_592_000)

    on_exit(fn ->
      restore_env(:pairing_token_secret, previous_secret)
      restore_env(:pairing_token_salt, previous_salt)
      restore_env(:pairing_token_ttl_seconds, previous_ttl)
    end)

    :ok
  end

  test "create_or_get_token returns a signed token for server/client claims" do
    server_id = UUID.uuid4()
    client_id = UUID.uuid4()

    {:ok, token} = Bridge.PersistentPairingManager.create_or_get_token(server_id, client_id)

    assert is_binary(token)
    assert String.contains?(token, ".")

    assert {:ok, pairing} = Bridge.PersistentPairingManager.get_by_token(token)
    assert pairing.server_id == server_id
    assert pairing.client_id == client_id
    assert pairing.token == token
    assert %DateTime{} = pairing.created_at
    assert %DateTime{} = pairing.expires_at
    assert is_binary(pairing.jti)
  end

  test "tokens are stateless and do not remember session ids" do
    server_id = UUID.uuid4()
    client_id = UUID.uuid4()

    {:ok, token} = Bridge.PersistentPairingManager.create_or_get_token(server_id, client_id)

    assert :ok = Bridge.PersistentPairingManager.set_last_session(token, "sess-123")
    assert :ok = Bridge.PersistentPairingManager.touch(token)

    assert {:ok, pairing} = Bridge.PersistentPairingManager.get_by_token(token)
    refute Map.has_key?(Map.from_struct(pairing), :last_session_id)
  end

  test "get_by_token rejects unknown or tampered tokens" do
    assert {:error, :not_found} = Bridge.PersistentPairingManager.get_by_token("non-existent-token")

    {:ok, token} = Bridge.PersistentPairingManager.create_or_get_token(UUID.uuid4(), UUID.uuid4())
    tampered = String.replace_suffix(token, String.last(token), "x")

    assert {:error, :not_found} = Bridge.PersistentPairingManager.get_by_token(tampered)
  end

  test "get_by_token rejects expired tokens" do
    Application.put_env(:bridge, :pairing_token_ttl_seconds, -1)

    {:ok, token} = Bridge.PersistentPairingManager.create_or_get_token(UUID.uuid4(), UUID.uuid4())

    assert {:error, :not_found} = Bridge.PersistentPairingManager.get_by_token(token)
  end

  defp restore_env(key, nil), do: Application.delete_env(:bridge, key)
  defp restore_env(key, value), do: Application.put_env(:bridge, key, value)
end

defmodule Bridge.PairingManagerTest do
  use ExUnit.Case, async: false

  setup do
    :ets.delete_all_objects(:bridge_pairing_codes)
    :ok
  end

  describe "create_pairing_request/2" do
    test "generates a 6-digit code" do
      server_id = UUID.uuid4()
      client_id = UUID.uuid4()

      {:ok, code, _expires_at} = Bridge.PairingManager.create_pairing_request(server_id, client_id)

      assert String.length(code) == 6
      assert String.match?(code, ~r/^\d{6}$/)
    end

    test "broadcasts pairing request" do
      server_id = UUID.uuid4()
      client_id = UUID.uuid4()

      Phoenix.PubSub.subscribe(Bridge.PubSub, "pairing:#{server_id}")

      {:ok, code, expires_at} = Bridge.PairingManager.create_pairing_request(server_id, client_id)

      assert_receive {:pairing_requested, ^client_id, ^code, ^expires_at}, 1000
    end
  end

  describe "validate_code/3" do
    test "accepts correct code" do
      server_id = UUID.uuid4()
      client_id = UUID.uuid4()

      {:ok, code, _} = Bridge.PairingManager.create_pairing_request(server_id, client_id)

      assert :ok = Bridge.PairingManager.validate_code(server_id, client_id, code)
    end

    test "rejects incorrect code" do
      server_id = UUID.uuid4()
      client_id = UUID.uuid4()

      Bridge.PairingManager.create_pairing_request(server_id, client_id)

      assert {:error, :invalid_code} = Bridge.PairingManager.validate_code(server_id, client_id, "999999")
    end

    test "tracks failed attempts" do
      server_id = UUID.uuid4()
      client_id = UUID.uuid4()

      Bridge.PairingManager.create_pairing_request(server_id, client_id)

      assert {:error, :invalid_code} = Bridge.PairingManager.validate_code(server_id, client_id, "111111")
      assert {:error, :invalid_code} = Bridge.PairingManager.validate_code(server_id, client_id, "222222")
      assert {:error, :invalid_code} = Bridge.PairingManager.validate_code(server_id, client_id, "333333")
      assert {:error, :too_many_attempts} = Bridge.PairingManager.validate_code(server_id, client_id, "444444")
    end

    test "returns error for non-existent pairing" do
      server_id = UUID.uuid4()
      client_id = UUID.uuid4()

      assert {:error, :not_found} = Bridge.PairingManager.validate_code(server_id, client_id, "123456")
    end
  end

  describe "cancel_pairing/2" do
    test "removes pairing request" do
      server_id = UUID.uuid4()
      client_id = UUID.uuid4()

      {:ok, code, _} = Bridge.PairingManager.create_pairing_request(server_id, client_id)

      Bridge.PairingManager.cancel_pairing(server_id, client_id)

      assert {:error, :not_found} = Bridge.PairingManager.validate_code(server_id, client_id, code)
    end
  end
end

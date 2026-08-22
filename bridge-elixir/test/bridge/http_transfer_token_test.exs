defmodule Bridge.HttpTransferTokenTest do
  use ExUnit.Case, async: false

  setup do
    previous_ttl = Application.get_env(:bridge, :http_transfer_token_ttl_seconds)

    on_exit(fn ->
      if previous_ttl == nil do
        Application.delete_env(:bridge, :http_transfer_token_ttl_seconds)
      else
        Application.put_env(:bridge, :http_transfer_token_ttl_seconds, previous_ttl)
      end
    end)

    :ok
  end

  test "pairing request handles bind server, client, and an existing node" do
    expires_at = DateTime.utc_now() |> DateTime.add(60, :second)

    assert {:ok, token} =
             Bridge.HttpTransferToken.issue_pairing_request(
               "server-1",
               "client-1",
               expires_at
             )

    assert {:ok, claims} =
             Bridge.HttpTransferToken.verify_pairing_request(token)

    assert claims.server_id == "server-1"
    assert claims.client_id == "client-1"

    assert {:ok, resolved_node} =
             Bridge.HttpTransferToken.resolve_existing_node(claims.owner_node)

    assert resolved_node == node()
  end

  test "transfer tokens are direction scoped" do
    assert {:ok, token} =
             Bridge.HttpTransferToken.issue_transfer(
               "request-1",
               "server-1",
               "request_body"
             )

    assert {:ok, claims} =
             Bridge.HttpTransferToken.verify_transfer(token, "request_body")

    assert claims.request_id == "request-1"
    assert claims.server_id == "server-1"

    assert {:error, :invalid} =
             Bridge.HttpTransferToken.verify_transfer(token, "response_body")
  end

  test "tampered transfer tokens are rejected" do
    assert {:ok, token} =
             Bridge.HttpTransferToken.issue_transfer(
               "request-1",
               "server-1",
               "response_body"
             )

    assert {:error, :invalid} =
             Bridge.HttpTransferToken.verify_transfer(
               token <> "tampered",
               "response_body"
             )
  end

  test "expired pairing request and transfer credentials are rejected" do
    expired_at = DateTime.utc_now() |> DateTime.add(-1, :second)

    assert {:ok, pairing_request_token} =
             Bridge.HttpTransferToken.issue_pairing_request(
               "server-1",
               "client-1",
               expired_at
             )

    assert {:error, :expired} =
             Bridge.HttpTransferToken.verify_pairing_request(pairing_request_token)

    Application.put_env(:bridge, :http_transfer_token_ttl_seconds, -1)

    assert {:ok, transfer_token} =
             Bridge.HttpTransferToken.issue_transfer(
               "request-1",
               "server-1",
               "response_body"
             )

    assert {:error, :expired} =
             Bridge.HttpTransferToken.verify_transfer(transfer_token, "response_body")
  end

  test "pairing owner resolution accepts only an existing cluster node" do
    assert {:error, :owner_unavailable} =
             Bridge.HttpTransferToken.resolve_existing_node("missing-owner@invalid")
  end
end

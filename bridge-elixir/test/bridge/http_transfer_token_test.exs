defmodule Bridge.HttpTransferTokenTest do
  use ExUnit.Case, async: true

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
end

defmodule CloudOrchestrator.TokenTest do
  use ExUnit.Case, async: true

  alias CloudOrchestrator.Token

  test "signs and verifies instance claims" do
    token = Token.sign(%{"instance_id" => "inst_1", "session_id" => "s1"})

    assert {:ok, claims} = Token.verify(token)
    assert claims["instance_id"] == "inst_1"
    assert claims["session_id"] == "s1"
  end

  test "rejects tampered tokens" do
    token = Token.sign(%{"instance_id" => "inst_1"})
    assert {:error, :invalid_token} = Token.verify(token <> "x")
  end
end

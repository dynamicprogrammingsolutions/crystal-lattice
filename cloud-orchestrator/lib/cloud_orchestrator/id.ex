defmodule CloudOrchestrator.Id do
  def new(prefix) when is_binary(prefix) do
    bytes = :crypto.strong_rand_bytes(12) |> Base.url_encode64(padding: false)
    prefix <> "_" <> bytes
  end
end

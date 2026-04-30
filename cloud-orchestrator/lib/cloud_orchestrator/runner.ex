defmodule CloudOrchestrator.Runner do
  @callback start_instance(map(), map()) :: {:ok, map()} | {:error, term()}
  @callback export_instance(map(), map()) :: {:ok, map()} | {:error, term()}
  @callback close_instance(map(), map()) :: {:ok, map()} | {:error, term()}
  @callback handle_proxy_request(map(), Plug.Conn.t(), String.t()) :: Plug.Conn.t()
end

defmodule CloudOrchestrator.Runner do
  @callback start_instance(map(), map()) :: {:ok, map()} | {:error, term()}
  @callback runtime_status(map()) ::
              {:ready, map()} | {:starting, map()} | {:failed, map()} | {:error, term()}
  @callback recent_logs(map()) :: String.t() | nil
  @callback export_instance(map(), map()) :: {:ok, map()} | {:error, term()}
  @callback close_instance(map(), map()) :: {:ok, map()} | {:error, term()}
  @callback handle_proxy_request(map(), Plug.Conn.t(), String.t()) :: Plug.Conn.t()
  @callback handle_proxy_request_result(map(), Plug.Conn.t(), String.t()) ::
              {:ok, %{status: integer(), headers: [{String.t(), String.t()}], body: String.t()}}
              | {:error, term()}
end

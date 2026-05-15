defmodule Bridge.PersistentPairingManager do
  use GenServer

  defmodule Pairing do
    defstruct [:token, :server_id, :client_id, :created_at, :expires_at, :jti]
  end

  def start_link(_opts) do
    GenServer.start_link(__MODULE__, [], name: __MODULE__)
  end

  @doc """
  Create or return an existing persistent pairing token.

  Tokens are stateless and signed. A token identifies a logical pairing
  with a server, while bridge `session_id` values remain ephemeral.
  """
  @spec create_or_get_token(String.t(), String.t()) :: {:ok, String.t()}
  def create_or_get_token(server_id, client_id) do
    Bridge.PairingToken.issue(server_id, client_id)
  end

  @doc """
  Verify a pairing by its token.
  """
  @spec get_by_token(String.t()) :: {:ok, map()} | {:error, :not_found}
  def get_by_token(token) do
    case Bridge.PairingToken.verify(token) do
      {:ok, claims} ->
        {:ok,
         %Pairing{
           token: claims.token,
           server_id: claims.server_id,
           client_id: claims.client_id,
           created_at: claims.issued_at,
           expires_at: claims.expires_at,
           jti: claims.jti
         }}

      {:error, _reason} ->
        {:error, :not_found}
    end
  end

  @doc """
  Backwards-compatible no-op for callers from the older ETS-backed model.
  """
  @spec touch(String.t()) :: :ok
  def touch(_token), do: :ok

  @doc """
  Backwards-compatible no-op. Session ids are intentionally ephemeral.
  """
  @spec set_last_session(String.t(), String.t()) :: :ok
  def set_last_session(_token, _session_id), do: :ok

  @impl true
  def init(_) do
    {:ok, %{}}
  end
end

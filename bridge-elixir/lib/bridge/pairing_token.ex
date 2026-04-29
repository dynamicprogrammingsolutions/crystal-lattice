defmodule Bridge.PairingToken do
  @moduledoc """
  Stateless signed pairing tokens.

  The token identifies a logical app/server pairing. Bridge sessions remain
  ephemeral and are recreated from a verified token whenever an app resumes.
  """

  @type claims :: %{
          token: String.t(),
          server_id: String.t(),
          client_id: String.t() | nil,
          issued_at: DateTime.t(),
          expires_at: DateTime.t(),
          jti: String.t()
        }

  @type verify_error :: :not_found | :invalid | :expired

  @doc """
  Issue a signed pairing token for a server/client pair.
  """
  @spec issue(String.t(), String.t() | nil) :: {:ok, String.t()}
  def issue(server_id, client_id \\ nil) when is_binary(server_id) do
    now = DateTime.utc_now() |> DateTime.truncate(:second)
    ttl = ttl_seconds()
    expires_at = DateTime.add(now, ttl, :second)

    payload = %{
      "v" => 1,
      "typ" => "bridge_pairing",
      "server_id" => server_id,
      "client_id" => client_id,
      "iat" => DateTime.to_unix(now),
      "exp" => DateTime.to_unix(expires_at),
      "jti" => UUID.uuid4()
    }

    encoded_payload = payload |> Jason.encode!() |> Base.url_encode64(padding: false)
    signature = sign(encoded_payload)

    {:ok, encoded_payload <> "." <> signature}
  end

  @doc """
  Verify a signed pairing token and return normalized claims.
  """
  @spec verify(String.t()) :: {:ok, claims()} | {:error, verify_error()}
  def verify(token) when is_binary(token) do
    with [encoded_payload, signature] <- String.split(token, ".", parts: 2),
         true <- secure_compare(signature, sign(encoded_payload)),
         {:ok, json} <- Base.url_decode64(encoded_payload, padding: false),
         {:ok, payload} <- Jason.decode(json),
         :ok <- validate_payload(payload),
         :ok <- validate_expiry(payload) do
      {:ok, claims_from_payload(token, payload)}
    else
      false -> {:error, :invalid}
      {:error, :expired} -> {:error, :expired}
      _ -> {:error, :invalid}
    end
  end

  def verify(_token), do: {:error, :invalid}

  defp validate_payload(%{
         "v" => 1,
         "typ" => "bridge_pairing",
         "server_id" => server_id,
         "iat" => iat,
         "exp" => exp,
         "jti" => jti
       })
       when is_binary(server_id) and is_integer(iat) and is_integer(exp) and is_binary(jti),
       do: :ok

  defp validate_payload(_payload), do: {:error, :invalid}

  defp validate_expiry(%{"exp" => exp}) do
    if exp > DateTime.utc_now() |> DateTime.to_unix() do
      :ok
    else
      {:error, :expired}
    end
  end

  defp claims_from_payload(token, payload) do
    %{
      token: token,
      server_id: payload["server_id"],
      client_id: payload["client_id"],
      issued_at: DateTime.from_unix!(payload["iat"]),
      expires_at: DateTime.from_unix!(payload["exp"]),
      jti: payload["jti"]
    }
  end

  defp sign(encoded_payload) do
    :hmac
    |> :crypto.mac(:sha256, secret(), salt() <> ":" <> encoded_payload)
    |> Base.url_encode64(padding: false)
  end

  defp secure_compare(left, right) when is_binary(left) and is_binary(right) do
    Plug.Crypto.secure_compare(left, right)
  rescue
    _ -> false
  end

  defp secret do
    Application.get_env(:bridge, :pairing_token_secret) ||
      System.get_env("BRIDGE_TOKEN_SECRET") ||
      "crystal-lattice-local-dev-pairing-token-secret"
  end

  defp salt do
    Application.get_env(:bridge, :pairing_token_salt) ||
      System.get_env("BRIDGE_TOKEN_SALT") ||
      "pairing-token-v1"
  end

  defp ttl_seconds do
    Application.get_env(:bridge, :pairing_token_ttl_seconds) ||
      case System.get_env("BRIDGE_PAIRING_TOKEN_TTL_SECONDS") do
        nil -> 2_592_000
        "" -> 2_592_000
        value -> parse_positive_integer(value, 2_592_000)
      end
  end

  defp parse_positive_integer(value, default) do
    case Integer.parse(value) do
      {parsed, ""} when parsed > 0 -> parsed
      _ -> default
    end
  end
end
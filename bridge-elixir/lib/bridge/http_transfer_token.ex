defmodule Bridge.HttpTransferToken do
  @moduledoc false

  @pairing_request_type "bridge_http_pairing_request"
  @transfer_type "bridge_http_transfer"

  def issue_pairing_request(server_id, client_id, expires_at)
      when is_binary(server_id) and is_binary(client_id) do
    payload = %{
      "v" => 1,
      "typ" => @pairing_request_type,
      "server_id" => server_id,
      "client_id" => client_id,
      "owner_node" => Atom.to_string(node()),
      "exp" => DateTime.to_unix(expires_at),
      "jti" => UUID.uuid4()
    }

    {:ok, encode(payload)}
  end

  def verify_pairing_request(token) do
    with {:ok, payload} <- decode(token),
         @pairing_request_type <- payload["typ"],
         server_id when is_binary(server_id) <- payload["server_id"],
         client_id when is_binary(client_id) <- payload["client_id"],
         owner_node when is_binary(owner_node) <- payload["owner_node"],
         :ok <- validate_expiry(payload) do
      {:ok,
       %{
         server_id: server_id,
         client_id: client_id,
         owner_node: owner_node,
         expires_at: DateTime.from_unix!(payload["exp"])
       }}
    else
      {:error, reason} -> {:error, reason}
      _ -> {:error, :invalid}
    end
  end

  def issue_transfer(request_id, server_id, direction)
      when is_binary(request_id) and is_binary(server_id) and
             direction in ["request_body", "response_body"] do
    now = DateTime.utc_now() |> DateTime.truncate(:second)

    payload = %{
      "v" => 1,
      "typ" => @transfer_type,
      "request_id" => request_id,
      "server_id" => server_id,
      "direction" => direction,
      "iat" => DateTime.to_unix(now),
      "exp" => DateTime.to_unix(DateTime.add(now, transfer_ttl_seconds(), :second)),
      "jti" => UUID.uuid4()
    }

    {:ok, encode(payload)}
  end

  def verify_transfer(token, expected_direction) when is_binary(expected_direction) do
    with {:ok, payload} <- decode(token),
         @transfer_type <- payload["typ"],
         ^expected_direction <- payload["direction"],
         request_id when is_binary(request_id) <- payload["request_id"],
         server_id when is_binary(server_id) <- payload["server_id"],
         :ok <- validate_expiry(payload) do
      {:ok,
       %{
         request_id: request_id,
         server_id: server_id,
         direction: expected_direction,
         expires_at: DateTime.from_unix!(payload["exp"])
       }}
    else
      {:error, reason} -> {:error, reason}
      _ -> {:error, :invalid}
    end
  end

  def resolve_existing_node(owner_node) when is_binary(owner_node) do
    case Enum.find([node() | Node.list()], &(Atom.to_string(&1) == owner_node)) do
      nil -> {:error, :owner_unavailable}
      existing_node -> {:ok, existing_node}
    end
  end

  defp encode(payload) do
    encoded_payload = payload |> Jason.encode!() |> Base.url_encode64(padding: false)
    encoded_payload <> "." <> sign(encoded_payload)
  end

  defp decode(token) when is_binary(token) do
    with [encoded_payload, signature] <- String.split(token, ".", parts: 2),
         true <- secure_compare(signature, sign(encoded_payload)),
         {:ok, json} <- Base.url_decode64(encoded_payload, padding: false),
         {:ok, payload} <- Jason.decode(json),
         1 <- payload["v"] do
      {:ok, payload}
    else
      false -> {:error, :invalid}
      _ -> {:error, :invalid}
    end
  end

  defp decode(_token), do: {:error, :invalid}

  defp validate_expiry(%{"exp" => exp}) when is_integer(exp) do
    if exp > DateTime.utc_now() |> DateTime.to_unix() do
      :ok
    else
      {:error, :expired}
    end
  end

  defp validate_expiry(_payload), do: {:error, :invalid}

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
    Application.get_env(:bridge, :http_transfer_token_salt) ||
      System.get_env("BRIDGE_HTTP_TRANSFER_TOKEN_SALT") ||
      "http-transfer-token-v1"
  end

  defp transfer_ttl_seconds do
    Application.get_env(:bridge, :http_transfer_token_ttl_seconds) ||
      parse_positive_integer(System.get_env("BRIDGE_HTTP_TRANSFER_TOKEN_TTL_SECONDS"), 180)
  end

  defp parse_positive_integer(nil, default), do: default
  defp parse_positive_integer("", default), do: default

  defp parse_positive_integer(value, default) do
    case Integer.parse(value) do
      {parsed, ""} when parsed > 0 -> parsed
      _ -> default
    end
  end
end

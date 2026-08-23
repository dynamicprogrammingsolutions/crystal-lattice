defmodule Bridge.HttpRouter do
  @moduledoc false

  use Plug.Router
  import Plug.Conn

  @frontend_token_header "x-crystal-bridge-token"
  @chunk_size 64 * 1024

  plug(:match)
  plug(:dispatch)

  options "/bridge/v1/*_path" do
    conn
    |> put_common_headers()
    |> send_resp(204, "")
    |> halt()
  end

  get "/bridge/v1/capabilities" do
    send_json(conn, 200, %{
      protocol_version: 1,
      http_proxy: true,
      request_body_download: true,
      response_body_upload: true,
      modes: ["http", "hybrid"]
    })
  end

  get "/bridge/v1/servers" do
    servers =
      Bridge.ServerRegistry.list_servers()
      |> Enum.map(&public_server/1)

    send_json(conn, 200, %{servers: servers})
  end

  post "/bridge/v1/pairings/request" do
    with {:ok, params, conn} <- read_json(conn),
         server_id when is_binary(server_id) <- params["server_id"],
         client_id when is_binary(client_id) <- params["client_id"],
         {:ok, _code, expires_at} <-
           Bridge.PairingManager.create_pairing_request(server_id, client_id),
         {:ok, pairing_request_token} <-
           Bridge.HttpTransferToken.issue_pairing_request(
             server_id,
             client_id,
             expires_at
           ) do
      send_json(conn, 200, %{
        status: "requested",
        pairing_request_token: pairing_request_token,
        expires_at: DateTime.to_iso8601(expires_at)
      })
    else
      {:error, :server_not_found} -> send_error(conn, 404, "server_not_found")
      {:error, reason} -> send_error(conn, 400, reason)
      _ -> send_error(conn, 400, "invalid_request")
    end
  end

  post "/bridge/v1/pairings/confirm" do
    with {:ok, params, conn} <- read_json(conn),
         pairing_request_token when is_binary(pairing_request_token) <-
           params["pairing_request_token"],
         code when is_binary(code) <- params["code"],
         {:ok, claims} <-
           Bridge.HttpTransferToken.verify_pairing_request(pairing_request_token),
         {:ok, owner_node} <-
           Bridge.HttpTransferToken.resolve_existing_node(claims.owner_node),
         :ok <-
           validate_pairing_on_node(
             owner_node,
             claims.server_id,
             claims.client_id,
             code
           ),
         {:ok, _server} <-
           Bridge.ServerRegistry.get_server(claims.server_id),
         {:ok, pairing_token} <-
           Bridge.PersistentPairingManager.create_or_get_token(
             claims.server_id,
             claims.client_id
           ) do
      send_json(conn, 200, %{
        server_id: claims.server_id,
        pairing_token: pairing_token
      })
    else
      {:error, :expired} -> send_error(conn, 410, "pairing_request_expired")
      {:error, :owner_unavailable} -> send_error(conn, 409, "pairing_owner_unavailable")
      {:error, :server_not_found} -> send_error(conn, 404, "server_not_found")
      {:error, :not_found} -> send_error(conn, 400, "pairing_not_found")
      {:error, reason} -> send_error(conn, 400, reason)
      _ -> send_error(conn, 400, "invalid_request")
    end
  end

  post "/bridge/v1/pairings/resume" do
    with {:ok, params, conn} <- read_json(conn),
         {:ok, token} <- frontend_token(conn),
         {:ok, claims} <- Bridge.PairingToken.verify(token),
         :ok <- validate_expected_server(params["server_id"], claims.server_id),
         {:ok, server} <- Bridge.ServerRegistry.get_server(claims.server_id) do
      send_json(conn, 200, %{
        server_id: claims.server_id,
        server: public_server(server)
      })
    else
      {:error, :server_mismatch} -> send_error(conn, 409, "server_mismatch")
      {:error, :not_found} -> send_error(conn, 404, "server_not_found")
      {:error, :server_not_found} -> send_error(conn, 404, "server_not_found")
      {:error, :expired} -> send_error(conn, 401, "invalid_pairing_token")
      {:error, :invalid} -> send_error(conn, 401, "invalid_pairing_token")
      {:error, :unauthorized} -> send_error(conn, 401, "invalid_pairing_token")
      _ -> send_error(conn, 400, "invalid_request")
    end
  end

  get "/bridge/v1/transfers/:request_id/request-body" do
    with {:ok, claims} <- authorize_transfer(conn, "request_body", request_id),
         {:ok, conn} <- attach_transfer(conn, claims, "request_body") do
      stream_request_body(conn)
    else
      {:error, :expired} -> send_error(conn, 410, "transfer_expired")
      {:error, :gone} -> send_error(conn, 410, "transfer_gone")
      {:error, reason} -> send_error(conn, 401, reason)
    end
  end

  put "/bridge/v1/transfers/:request_id/response-body" do
    with {:ok, claims} <- authorize_transfer(conn, "response_body", request_id),
         {:ok, conn} <- attach_transfer(conn, claims, "response_body") do
      receive_response_upload(conn)
    else
      {:error, :expired} -> send_error(conn, 410, "transfer_expired")
      {:error, :gone} -> send_error(conn, 410, "transfer_gone")
      {:error, reason} -> send_error(conn, 401, reason)
    end
  end

  match "/bridge/v1/proxy/*path" do
    with {:ok, token} <- frontend_token(conn),
         {:ok, pairing} <- Bridge.PairingToken.verify(token),
         {:ok, server} <- Bridge.ServerRegistry.get_server(pairing.server_id),
         {:ok, transfer_pid, request} <-
           start_frontend_transfer(conn, path, pairing.server_id, server.channel_pid),
         :ok <- safe_send(server.channel_pid, {:http_request_v2, request}) do
      serve_frontend_transfer(conn, transfer_pid, request.request_body_present)
    else
      {:error, :too_many_transfers} -> send_error(conn, 429, "too_many_requests")
      {:error, :not_found} -> send_error(conn, 404, "server_not_found")
      {:error, :expired} -> send_error(conn, 401, "invalid_pairing_token")
      {:error, :invalid} -> send_error(conn, 401, "invalid_pairing_token")
      {:error, :unauthorized} -> send_error(conn, 401, "invalid_pairing_token")
      {:error, :server_not_found} -> send_error(conn, 404, "server_not_found")
      {:error, reason} -> send_error(conn, 502, reason)
    end
  end

  match _ do
    conn
  end

  defp start_frontend_transfer(conn, path, server_id, server_pid) do
    request_id = UUID.uuid4()
    request_body_present = request_body_present?(conn)

    with {:ok, request_token} <-
           Bridge.HttpTransferToken.issue_transfer(
             request_id,
             server_id,
             "request_body"
           ),
         {:ok, response_token} <-
           Bridge.HttpTransferToken.issue_transfer(
             request_id,
             server_id,
             "response_body"
           ),
         {:ok, transfer_pid} <-
           Bridge.HttpTransfer.start(%{
             request_id: request_id,
             server_id: server_id,
             server_pid: server_pid,
             frontend_pid: self(),
             request_body_present: request_body_present
           }) do
      backend_path =
        case conn.query_string do
          "" -> "/" <> Enum.join(path, "/")
          query -> "/" <> Enum.join(path, "/") <> "?" <> query
        end

      request = %{
        type: "http_request_v2",
        request_id: request_id,
        method: conn.method,
        path: backend_path,
        headers: request_headers(conn),
        request_body_present: request_body_present,
        request_body_path: "/bridge/v1/transfers/#{request_id}/request-body",
        request_body_token: request_token,
        response_body_path: "/bridge/v1/transfers/#{request_id}/response-body",
        response_body_token: response_token
      }

      {:ok, transfer_pid, request}
    end
  end

  defp serve_frontend_transfer(conn, transfer_pid, true) do
    case relay_frontend_request(conn, transfer_pid) do
      {:ok, conn} -> await_frontend_response(conn, transfer_pid)
      {:error, conn} -> conn
    end
  end

  defp serve_frontend_transfer(conn, transfer_pid, false) do
    await_frontend_response(conn, transfer_pid)
  end

  defp relay_frontend_request(conn, transfer_pid) do
    receive do
      {:http_transfer_request_demand, ^transfer_pid} ->
        case read_body(conn, length: @chunk_size, read_length: @chunk_size) do
          {:more, data, conn} ->
            send(transfer_pid, {:frontend_request_chunk, self(), data, false})
            relay_frontend_request(conn, transfer_pid)

          {:ok, data, conn} ->
            send(transfer_pid, {:frontend_request_chunk, self(), data, true})
            await_request_complete(conn, transfer_pid)

          {:error, reason} ->
            send(
              transfer_pid,
              {:http_transfer_peer_error, self(), inspect(reason)}
            )

            {:error, send_error(conn, 400, "invalid_request_body")}
        end

      {:http_transfer_error, ^transfer_pid, status, reason} ->
        {:error, send_error(conn, status, reason)}
    after
      transfer_timeout_ms() ->
        send(transfer_pid, {:http_transfer_peer_error, self(), "frontend_request_timeout"})
        {:error, send_error(conn, 504, "transfer_timeout")}
    end
  end

  defp await_request_complete(conn, transfer_pid) do
    receive do
      {:http_transfer_request_complete, ^transfer_pid} ->
        {:ok, conn}

      {:http_transfer_error, ^transfer_pid, status, reason} ->
        {:error, send_error(conn, status, reason)}
    after
      transfer_timeout_ms() ->
        send(transfer_pid, {:http_transfer_peer_error, self(), "frontend_request_timeout"})
        {:error, send_error(conn, 504, "transfer_timeout")}
    end
  end

  defp await_frontend_response(conn, transfer_pid) do
    receive do
      {:http_transfer_response_init, ^transfer_pid, status, headers} ->
        conn =
          headers
          |> response_headers()
          |> Enum.reduce(conn, fn {name, value}, acc ->
            put_resp_header(acc, name, value)
          end)
          |> put_common_headers()
          |> send_chunked(status)

        send(transfer_pid, {:frontend_response_ready, self()})
        stream_frontend_response(conn, transfer_pid)

      {:http_transfer_error, ^transfer_pid, status, reason} ->
        send_error(conn, status, reason)
    after
      transfer_timeout_ms() ->
        send(transfer_pid, {:http_transfer_peer_error, self(), "frontend_response_timeout"})
        send_error(conn, 504, "transfer_timeout")
    end
  end

  defp stream_frontend_response(conn, transfer_pid) do
    receive do
      {:http_transfer_response_chunk, ^transfer_pid, data, final} ->
        case chunk_if_present(conn, data) do
          {:ok, conn} ->
            send(transfer_pid, {:frontend_response_ack, self(), final})

            if final do
              halt(conn)
            else
              stream_frontend_response(conn, transfer_pid)
            end

          {:error, reason} ->
            send(
              transfer_pid,
              {:http_transfer_peer_error, self(), inspect(reason)}
            )

            conn
        end

      {:http_transfer_error, ^transfer_pid, _status, _reason} ->
        conn
    after
      transfer_timeout_ms() ->
        send(transfer_pid, {:http_transfer_peer_error, self(), "frontend_response_timeout"})
        conn
    end
  end

  defp attach_transfer(conn, claims, direction) do
    ref = make_ref()

    Phoenix.PubSub.broadcast(
      Bridge.PubSub,
      Bridge.HttpTransfer.topic(claims.request_id),
      {:http_transfer_attach, direction, claims, self(), ref}
    )

    receive do
      {:http_transfer_attached, ^ref} -> {:ok, conn}
      {:http_transfer_rejected, ^ref, reason} -> {:error, reason}
    after
      5_000 -> {:error, :gone}
    end
  end

  defp stream_request_body(conn) do
    conn =
      conn
      |> put_resp_content_type("application/octet-stream")
      |> put_resp_header("content-encoding", "identity")
      |> put_common_headers()
      |> send_chunked(200)

    stream_request_body_chunks(conn)
  end

  defp stream_request_body_chunks(conn) do
    receive do
      {:http_transfer_request_chunk, transfer_pid, data, final} ->
        case chunk_if_present(conn, data) do
          {:ok, conn} ->
            send(transfer_pid, {:request_chunk_ack, self(), final})

            if final do
              halt(conn)
            else
              stream_request_body_chunks(conn)
            end

          {:error, reason} ->
            send(
              transfer_pid,
              {:http_transfer_peer_error, self(), inspect(reason)}
            )

            conn
        end

      {:http_transfer_error, _transfer_pid, _reason} ->
        conn
    after
      transfer_timeout_ms() -> conn
    end
  end

  defp receive_response_upload(conn) do
    receive_response_upload_chunks(conn)
  end

  defp receive_response_upload_chunks(conn) do
    receive do
      {:http_transfer_response_demand, transfer_pid} ->
        case read_body(conn, length: @chunk_size, read_length: @chunk_size) do
          {:more, data, conn} ->
            send(transfer_pid, {:response_upload_chunk, self(), data, false})
            receive_response_upload_chunks(conn)

          {:ok, data, conn} ->
            send(transfer_pid, {:response_upload_chunk, self(), data, true})
            await_response_upload_complete(conn, transfer_pid)

          {:error, reason} ->
            send(
              transfer_pid,
              {:http_transfer_peer_error, self(), inspect(reason)}
            )

            send_error(conn, 400, "invalid_response_body")
        end

      {:http_transfer_error, _transfer_pid, reason} ->
        send_error(conn, 502, reason)
    after
      transfer_timeout_ms() -> send_error(conn, 504, "transfer_timeout")
    end
  end

  defp await_response_upload_complete(conn, transfer_pid) do
    receive do
      {:http_transfer_response_complete, ^transfer_pid} ->
        conn
        |> put_common_headers()
        |> send_resp(204, "")
        |> halt()

      {:http_transfer_error, ^transfer_pid, reason} ->
        send_error(conn, 502, reason)
    after
      transfer_timeout_ms() -> send_error(conn, 504, "transfer_timeout")
    end
  end

  defp authorize_transfer(conn, direction, request_id) do
    with ["Bearer " <> token] <- get_req_header(conn, "authorization"),
         {:ok, claims} <-
           Bridge.HttpTransferToken.verify_transfer(token, direction),
         true <- claims.request_id == request_id do
      {:ok, claims}
    else
      {:error, reason} -> {:error, reason}
      _ -> {:error, :invalid_transfer_token}
    end
  end

  defp validate_pairing_on_node(owner_node, server_id, client_id, code) do
    try do
      :erpc.call(
        owner_node,
        Bridge.PairingManager,
        :validate_code,
        [server_id, client_id, code],
        5_000
      )
    catch
      _kind, _reason -> {:error, :owner_unavailable}
    end
  end

  defp validate_expected_server(nil, _actual), do: :ok
  defp validate_expected_server("", _actual), do: :ok
  defp validate_expected_server(server_id, server_id), do: :ok
  defp validate_expected_server(_expected, _actual), do: {:error, :server_mismatch}

  defp frontend_token(conn) do
    case get_req_header(conn, @frontend_token_header) do
      [token] when is_binary(token) and token != "" -> {:ok, token}
      _ -> {:error, :unauthorized}
    end
  end

  defp read_json(conn) do
    case read_body(conn, length: 1_000_000, read_length: 1_000_000) do
      {:ok, body, conn} ->
        case Jason.decode(body) do
          {:ok, params} when is_map(params) -> {:ok, params, conn}
          _ -> {:error, :invalid_json}
        end

      _ ->
        {:error, :invalid_json}
    end
  end

  defp request_body_present?(conn) do
    explicit_body =
      get_req_header(conn, "x-crystal-bridge-body-present") == ["1"]

    content_length =
      case get_req_header(conn, "content-length") do
        [value] ->
          case Integer.parse(value) do
            {size, ""} -> size
            _ -> 0
          end

        _ ->
          0
      end

    explicit_body or content_length > 0 or
      get_req_header(conn, "transfer-encoding") != []
  end

  defp request_headers(conn) do
    conn.req_headers
    |> Enum.reject(fn {name, _value} ->
      String.downcase(name) in [
        "host",
        @frontend_token_header,
        "x-crystal-bridge-body-present",
        "content-length",
        "transfer-encoding",
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailer",
        "upgrade"
      ]
    end)
    |> Map.new()
  end

  defp response_headers(headers) do
    headers
    |> Enum.map(fn {name, value} ->
      {String.downcase(to_string(name)), to_string(value)}
    end)
    |> Enum.reject(fn {name, _value} ->
      name in [
        "content-length",
        "content-encoding",
        "transfer-encoding",
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailer",
        "upgrade"
      ]
    end)
  end

  defp public_server(server) do
    %{
      server_id: server.server_id,
      display_name: server.display_name,
      computer_name: server.computer_name,
      location: server.location
    }
  end

  defp chunk_if_present(conn, ""), do: {:ok, conn}
  defp chunk_if_present(conn, data), do: chunk(conn, data)

  defp safe_send(pid, message) do
    try do
      send(pid, message)
      :ok
    rescue
      ArgumentError -> {:error, :server_not_found}
    end
  end

  defp send_error(conn, status, reason) do
    send_json(conn, status, %{error: to_string(reason)})
  end

  defp send_json(conn, status, data) do
    conn
    |> put_common_headers()
    |> put_resp_content_type("application/json")
    |> send_resp(status, Jason.encode!(data))
    |> halt()
  end

  defp put_common_headers(conn) do
    conn
    |> put_resp_header("cache-control", "no-store")
    |> put_resp_header("access-control-allow-origin", "*")
    |> put_resp_header(
      "access-control-allow-headers",
      "content-type, authorization, x-crystal-bridge-token" <>
        ", x-crystal-bridge-body-present"
    )
    |> put_resp_header(
      "access-control-allow-methods",
      "GET, POST, PUT, PATCH, DELETE, OPTIONS"
    )
  end

  defp transfer_timeout_ms do
    case System.get_env("BRIDGE_HTTP_TIMEOUT_MS") do
      nil ->
        120_000

      "" ->
        120_000

      value ->
        case Integer.parse(value) do
          {parsed, ""} when parsed > 0 -> parsed
          _ -> 120_000
        end
    end
  end
end

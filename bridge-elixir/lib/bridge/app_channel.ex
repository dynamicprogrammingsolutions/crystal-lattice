defmodule Bridge.AppChannel do
  use Phoenix.Channel
  require Logger

  defp safe_send(pid, message) do
    try do
      send(pid, message)
      :ok
    rescue
      ArgumentError ->
        :error
    end
  end

  defp http_timeout_ms() do
    case System.get_env("BRIDGE_HTTP_TIMEOUT_MS") do
      nil ->
        120_000

      "" ->
        120_000

      value ->
        case Integer.parse(value) do
          {n, _} when n > 0 -> n
          _ -> 120_000
        end
    end
  end

  defp await_http_response(socket, request_id) do
    receive do
      {:http_response, response} ->
        Phoenix.PubSub.unsubscribe(Bridge.PubSub, "tunnel:request:#{request_id}")
        {:reply, {:ok, response}, socket}

      {:http_response_init, payload} ->
        push(socket, "http_response_init", payload)
        await_http_response(socket, request_id)

      {:http_response_chunk, payload} ->
        push(socket, "http_response_chunk", payload)
        await_http_response(socket, request_id)

      {:http_response_end, payload} ->
        push(socket, "http_response_end", payload)
        Phoenix.PubSub.unsubscribe(Bridge.PubSub, "tunnel:request:#{request_id}")
        {:reply, {:ok, %{type: "http_response_chunked", request_id: request_id}}, socket}
    after
      http_timeout_ms() ->
        Phoenix.PubSub.unsubscribe(Bridge.PubSub, "tunnel:request:#{request_id}")
        {:reply, {:error, %{reason: "timeout"}}, socket}
    end
  end

  @impl true
  def join("app:" <> client_id, _params, socket) do
    socket = assign(socket, :client_id, client_id)
    {:ok, socket}
  end

  @impl true
  def handle_in("list_servers", _params, socket) do
    servers = Bridge.ServerRegistry.list_servers()

    server_list =
      Enum.map(servers, fn server ->
        %{
          server_id: server.server_id,
          display_name: server.display_name,
          computer_name: server.computer_name,
          location: server.location
        }
      end)

    {:reply, {:ok, %{servers: server_list}}, socket}
  end

  @impl true
  def handle_in("pair_request", %{"server_id" => server_id}, socket) do
    client_id = socket.assigns.client_id

    case Bridge.PairingManager.create_pairing_request(server_id, client_id) do
      {:ok, _code, expires_at} ->
        {:reply, {:ok, %{status: "requested", expires_at: DateTime.to_iso8601(expires_at)}},
         socket}

      {:error, reason} ->
        {:reply, {:error, %{reason: reason}}, socket}
    end
  end

  @impl true
  def handle_in("pair_submit", params, socket) do
    %{
      "server_id" => server_id,
      "code" => code
    } = params

    client_id = socket.assigns.client_id

    case Bridge.PairingManager.validate_code(server_id, client_id, code) do
      :ok ->
        case Bridge.ServerRegistry.get_server(server_id) do
          {:ok, server_info} ->
            {:ok, pairing_token} =
              Bridge.PersistentPairingManager.create_or_get_token(server_id, client_id)

            case Bridge.SessionManager.create_session(
                   server_id,
                   client_id,
                   server_info.node,
                   node()
                 ) do
              {:ok, session_id} ->
                Bridge.PersistentPairingManager.set_last_session(pairing_token, session_id)

                socket = assign(socket, :session_id, session_id)
                Phoenix.PubSub.subscribe(Bridge.PubSub, "tunnel:app:#{client_id}")

                {:reply, {:ok, %{session_id: session_id, pairing_token: pairing_token}}, socket}

              {:error, :server_not_found} ->
                {:reply, {:error, %{reason: "server_not_found"}}, socket}

              {:error, reason} ->
                {:reply, {:error, %{reason: Atom.to_string(reason)}}, socket}
            end

          {:error, :not_found} ->
            {:reply, {:error, %{reason: "server_not_found"}}, socket}
        end

      {:error, reason} ->
        {:reply, {:error, %{reason: Atom.to_string(reason)}}, socket}
    end
  end

  @impl true
  def handle_in("resume_session", %{"pairing_token" => token} = params, socket) do
    client_id = socket.assigns.client_id

    case Bridge.PersistentPairingManager.get_by_token(token) do
      {:ok, pairing} ->
        server_id_param = Map.get(params, "server_id")

        # If a server_id is provided by the client, ensure it matches the
        # stored pairing to avoid accidental mixes.
        if is_binary(server_id_param) and server_id_param != pairing.server_id do
          {:reply, {:error, %{reason: "server_mismatch"}}, socket}
        else
          case Bridge.ServerRegistry.get_server(pairing.server_id) do
            {:ok, server_info} ->
              # Prefer to reuse the last known session_id for this pairing
              # when it still exists, so the bridge session remains stable
              # across app reconnects. If it no longer exists (e.g. timed
              # out), create a new one and remember it.
              reused_session_id =
                case pairing.last_session_id do
                  nil ->
                    nil

                  last_id ->
                    case Bridge.SessionManager.get_session(last_id) do
                      {:ok, _session} -> last_id
                      {:error, :not_found} -> nil
                    end
                end

              session_id_result =
                case reused_session_id do
                  nil ->
                    case Bridge.SessionManager.create_session(
                           pairing.server_id,
                           client_id,
                           server_info.node,
                           node()
                         ) do
                      {:ok, new_id} ->
                        Bridge.PersistentPairingManager.set_last_session(token, new_id)
                        {:ok, new_id}

                      {:error, reason} ->
                        {:error, reason}
                    end

                  existing_id ->
                    Bridge.SessionManager.update_activity(existing_id)
                    {:ok, existing_id}
                end

              case session_id_result do
                {:ok, session_id} ->
                  Bridge.PersistentPairingManager.touch(token)

                  socket = assign(socket, :session_id, session_id)
                  Phoenix.PubSub.subscribe(Bridge.PubSub, "tunnel:app:#{client_id}")

                  {:reply, {:ok, %{session_id: session_id}}, socket}

                {:error, :server_not_found} ->
                  {:reply, {:error, %{reason: "server_not_found"}}, socket}

                {:error, reason} ->
                  {:reply, {:error, %{reason: Atom.to_string(reason)}}, socket}
              end

            {:error, :not_found} ->
              {:reply, {:error, %{reason: "server_not_found"}}, socket}
          end
        end

      {:error, :not_found} ->
        {:reply, {:error, %{reason: "invalid_pairing_token"}}, socket}
    end
  end

  @impl true
  def handle_in("http_request", params, socket) do
    %{
      "request_id" => request_id,
      "session_id" => session_id,
      "method" => method,
      "path" => path,
      "headers" => headers,
      "body" => body
    } = params

    case Bridge.SessionManager.get_session(session_id) do
      {:ok, session} ->
        Bridge.SessionManager.update_activity(session_id)

        request = %{
          type: "http_request",
          request_id: request_id,
          method: method,
          path: path,
          headers: headers,
          body: body
        }

        case Bridge.ServerRegistry.get_server(session.server_id) do
          {:ok, server_info} ->
            Phoenix.PubSub.subscribe(Bridge.PubSub, "tunnel:request:#{request_id}")

            case safe_send(server_info.channel_pid, {:http_request, request}) do
              :ok ->
                await_http_response(socket, request_id)

              :error ->
                Phoenix.PubSub.unsubscribe(Bridge.PubSub, "tunnel:request:#{request_id}")
                {:reply, {:error, %{reason: "server_not_found"}}, socket}
            end

          {:error, :not_found} ->
            {:reply, {:error, %{reason: "server_not_found"}}, socket}
        end

      {:error, :not_found} ->
        {:reply, {:error, %{reason: "invalid_session"}}, socket}
    end
  end

  @impl true
  def handle_in("http_request_init", params, socket) do
    %{
      "request_id" => request_id,
      "session_id" => session_id,
      "method" => method,
      "path" => path,
      "headers" => headers
    } = params

    body_encoding = Map.get(params, "body_encoding")
    body_length_bytes = Map.get(params, "body_length_bytes")
    chunk_size_bytes = Map.get(params, "chunk_size_bytes")

    case Bridge.SessionManager.get_session(session_id) do
      {:ok, session} ->
        Bridge.SessionManager.update_activity(session_id)

        request = %{
          type: "http_request_init",
          request_id: request_id,
          method: method,
          path: path,
          headers: headers,
          body_encoding: body_encoding,
          body_length_bytes: body_length_bytes,
          chunk_size_bytes: chunk_size_bytes
        }

        case Bridge.ServerRegistry.get_server(session.server_id) do
          {:ok, server_info} ->
            case safe_send(server_info.channel_pid, {:http_request_init, request}) do
              :ok ->
                {:reply, {:ok, %{status: "accepted"}}, socket}

              :error ->
                {:reply, {:error, %{reason: "server_not_found"}}, socket}
            end

          {:error, :not_found} ->
            {:reply, {:error, %{reason: "server_not_found"}}, socket}
        end

      {:error, :not_found} ->
        {:reply, {:error, %{reason: "invalid_session"}}, socket}
    end
  end

  @impl true
  def handle_in("http_request_chunk", params, socket) do
    %{
      "request_id" => request_id,
      "session_id" => session_id,
      "seq" => seq,
      "chunk" => chunk
    } = params

    case Bridge.SessionManager.get_session(session_id) do
      {:ok, session} ->
        Bridge.SessionManager.update_activity(session_id)

        request = %{
          type: "http_request_chunk",
          request_id: request_id,
          seq: seq,
          chunk: chunk
        }

        case Bridge.ServerRegistry.get_server(session.server_id) do
          {:ok, server_info} ->
            case safe_send(server_info.channel_pid, {:http_request_chunk, request}) do
              :ok ->
                {:reply, {:ok, %{status: "accepted"}}, socket}

              :error ->
                {:reply, {:error, %{reason: "server_not_found"}}, socket}
            end

          {:error, :not_found} ->
            {:reply, {:error, %{reason: "server_not_found"}}, socket}
        end

      {:error, :not_found} ->
        {:reply, {:error, %{reason: "invalid_session"}}, socket}
    end
  end

  @impl true
  def handle_in("http_request_end", params, socket) do
    %{
      "request_id" => request_id,
      "session_id" => session_id,
      "final_seq" => final_seq
    } = params

    case Bridge.SessionManager.get_session(session_id) do
      {:ok, session} ->
        Bridge.SessionManager.update_activity(session_id)

        request = %{
          type: "http_request_end",
          request_id: request_id,
          final_seq: final_seq
        }

        case Bridge.ServerRegistry.get_server(session.server_id) do
          {:ok, server_info} ->
            Phoenix.PubSub.subscribe(Bridge.PubSub, "tunnel:request:#{request_id}")

            case safe_send(server_info.channel_pid, {:http_request_end, request}) do
              :ok ->
                await_http_response(socket, request_id)

              :error ->
                Phoenix.PubSub.unsubscribe(Bridge.PubSub, "tunnel:request:#{request_id}")
                {:reply, {:error, %{reason: "server_not_found"}}, socket}
            end

          {:error, :not_found} ->
            {:reply, {:error, %{reason: "server_not_found"}}, socket}
        end

      {:error, :not_found} ->
        {:reply, {:error, %{reason: "invalid_session"}}, socket}
    end
  end

  @impl true
  def terminate(_reason, _socket) do
    :ok
  end
end

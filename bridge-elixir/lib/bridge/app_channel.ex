defmodule Bridge.AppChannel do
  use Phoenix.Channel
  require Logger

  @impl true
  def join("app:" <> client_id, _params, socket) do
    socket = assign(socket, :client_id, client_id)
    {:ok, socket}
  end

  @impl true
  def handle_in("list_servers", _params, socket) do
    servers = Bridge.ServerRegistry.list_servers()
    
    server_list = Enum.map(servers, fn server ->
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
        {:reply, {:ok, %{status: "requested", expires_at: DateTime.to_iso8601(expires_at)}}, socket}
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

            {:ok, session_id} = Bridge.SessionManager.create_session(
              server_id,
              client_id,
              server_info.node,
              node()
            )

            Bridge.PersistentPairingManager.set_last_session(pairing_token, session_id)

            socket = assign(socket, :session_id, session_id)
            Phoenix.PubSub.subscribe(Bridge.PubSub, "tunnel:app:#{client_id}")

            {:reply, {:ok, %{session_id: session_id, pairing_token: pairing_token}}, socket}

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

              session_id =
                case reused_session_id do
                  nil ->
                    {:ok, new_id} =
                      Bridge.SessionManager.create_session(
                        pairing.server_id,
                        client_id,
                        server_info.node,
                        node()
                      )

                    Bridge.PersistentPairingManager.set_last_session(token, new_id)
                    new_id

                  existing_id ->
                    Bridge.SessionManager.update_activity(existing_id)
                    existing_id
                end

              Bridge.PersistentPairingManager.touch(token)

              socket = assign(socket, :session_id, session_id)
              Phoenix.PubSub.subscribe(Bridge.PubSub, "tunnel:app:#{client_id}")

              {:reply, {:ok, %{session_id: session_id}}, socket}

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

        Phoenix.PubSub.subscribe(Bridge.PubSub, "tunnel:request:#{request_id}")

        Phoenix.PubSub.broadcast(
          Bridge.PubSub,
          "tunnel:server:#{session.server_id}",
          {:http_request, request}
        )

        receive do
          {:http_response, response} ->
            Phoenix.PubSub.unsubscribe(Bridge.PubSub, "tunnel:request:#{request_id}")
            {:reply, {:ok, response}, socket}
        after
          60_000 ->
            Phoenix.PubSub.unsubscribe(Bridge.PubSub, "tunnel:request:#{request_id}")
            {:reply, {:error, %{reason: "timeout"}}, socket}
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

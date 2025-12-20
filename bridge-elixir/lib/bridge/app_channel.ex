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
            {:ok, session_id} = Bridge.SessionManager.create_session(
              server_id,
              client_id,
              server_info.node,
              node()
            )

            socket = assign(socket, :session_id, session_id)
            Phoenix.PubSub.subscribe(Bridge.PubSub, "tunnel:app:#{client_id}")

            {:reply, {:ok, %{session_id: session_id}}, socket}

          {:error, :not_found} ->
            {:reply, {:error, %{reason: "server_not_found"}}, socket}
        end

      {:error, reason} ->
        {:reply, {:error, %{reason: Atom.to_string(reason)}}, socket}
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
  def terminate(_reason, socket) do
    if socket.assigns[:session_id] do
      Bridge.SessionManager.delete_session(socket.assigns.session_id)
    end
    :ok
  end
end

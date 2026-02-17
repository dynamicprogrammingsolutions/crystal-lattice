defmodule Bridge.ServerChannel do
  use Phoenix.Channel
  require Logger

  @impl true
  def join("server:" <> _server_id, _params, socket) do
    {:ok, socket}
  end

  @impl true
  def handle_in("register", params, socket) do
    %{
      "server_id" => server_id,
      "display_name" => display_name,
      "computer_name" => computer_name
    } = params

    location = Map.get(params, "location")

    server_info = %{
      server_id: server_id,
      display_name: display_name,
      computer_name: computer_name,
      location: location,
      channel_pid: self()
    }

    case Bridge.ServerRegistry.register_server(server_id, server_info) do
      {:ok, _result} ->
        socket =
          socket
          |> assign(:server_id, server_id)
          |> assign(:registered, true)

        {:reply, {:ok, %{status: "registered"}}, socket}

      {:error, :already_registered} ->
        {:reply, {:error, %{reason: "already_registered"}}, socket}

      {:error, reason} ->
        {:reply, {:error, %{reason: Atom.to_string(reason)}}, socket}
    end
  end

  @impl true
  def handle_in("http_response", params, socket) do
    %{
      "request_id" => request_id,
      "status" => status,
      "headers" => headers,
      "body" => body
    } = params

    response = %{
      type: "http_response",
      request_id: request_id,
      status: status,
      headers: headers,
      body: body
    }

    Phoenix.PubSub.broadcast(
      Bridge.PubSub,
      "tunnel:request:#{request_id}",
      {:http_response, response}
    )

    {:noreply, socket}
  end

  @impl true
  def handle_in("http_response_init", params, socket) do
    %{
      "request_id" => request_id
    } = params

    Phoenix.PubSub.broadcast(
      Bridge.PubSub,
      "tunnel:request:#{request_id}",
      {:http_response_init, params}
    )

    {:noreply, socket}
  end

  @impl true
  def handle_in("http_response_chunk", params, socket) do
    %{
      "request_id" => request_id
    } = params

    Phoenix.PubSub.broadcast(
      Bridge.PubSub,
      "tunnel:request:#{request_id}",
      {:http_response_chunk, params}
    )

    {:noreply, socket}
  end

  @impl true
  def handle_in("http_response_end", params, socket) do
    %{
      "request_id" => request_id
    } = params

    Phoenix.PubSub.broadcast(
      Bridge.PubSub,
      "tunnel:request:#{request_id}",
      {:http_response_end, params}
    )

    {:noreply, socket}
  end

  @impl true
  def handle_info({:superseded, server_id, _new_pid}, socket) do
    push(socket, "superseded", %{server_id: server_id, reason: "new_connection"})
    {:stop, :normal, socket}
  end

  @impl true
  def handle_info({:pairing_requested, client_id, code, expires_at}, socket) do
    push(socket, "pairing_requested", %{
      client_id: client_id,
      code: code,
      expires_at: DateTime.to_iso8601(expires_at)
    })

    {:noreply, socket}
  end

  @impl true
  def handle_info({:paired, client_id, session_id}, socket) do
    push(socket, "paired", %{
      client_id: client_id,
      session_id: session_id
    })

    {:noreply, socket}
  end

  @impl true
  def handle_info({:http_request, request}, socket) do
    push(socket, "http_request", request)
    {:noreply, socket}
  end

  @impl true
  def handle_info({:http_request_init, request}, socket) do
    push(socket, "http_request_init", request)
    {:noreply, socket}
  end

  @impl true
  def handle_info({:http_request_chunk, request}, socket) do
    push(socket, "http_request_chunk", request)
    {:noreply, socket}
  end

  @impl true
  def handle_info({:http_request_end, request}, socket) do
    push(socket, "http_request_end", request)
    {:noreply, socket}
  end

  @impl true
  def terminate(_reason, socket) do
    if socket.assigns[:registered] && socket.assigns[:server_id] do
      Bridge.ServerRegistry.unregister_server(socket.assigns.server_id, self())
    end

    :ok
  end
end

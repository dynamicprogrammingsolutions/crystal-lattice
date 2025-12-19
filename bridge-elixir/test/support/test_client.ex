defmodule Bridge.TestClient do
  use WebSockex
  require Logger

  def start_server_client(url, server_id, test_pid) do
    state = %{
      type: :server,
      server_id: server_id,
      test_pid: test_pid,
      channel_joined: false
    }

    ws_url = "#{url}/ws?type=server"
    WebSockex.start_link(ws_url, __MODULE__, state)
  end

  def start_app_client(url, client_id, test_pid) do
    state = %{
      type: :app,
      client_id: client_id,
      test_pid: test_pid,
      channel_joined: false
    }

    ws_url = "#{url}/ws?type=app"
    WebSockex.start_link(ws_url, __MODULE__, state)
  end

  def register_server(pid, server_id, display_name, computer_name, location \\ nil) do
    msg = %{
      type: "register",
      server_id: server_id,
      display_name: display_name,
      computer_name: computer_name,
      location: location
    }
    
    send_message(pid, msg)
  end

  def list_servers(pid) do
    msg = %{type: "list_servers"}
    send_message(pid, msg)
  end

  def pair_request(pid, server_id) do
    msg = %{
      type: "pair_request",
      server_id: server_id
    }
    send_message(pid, msg)
  end

  def pair_submit(pid, server_id, code) do
    msg = %{
      type: "pair_submit",
      server_id: server_id,
      code: code
    }
    send_message(pid, msg)
  end

  def http_request(pid, request_id, session_id, method, path, headers \\ %{}, body \\ nil) do
    msg = %{
      type: "http_request",
      request_id: request_id,
      session_id: session_id,
      method: method,
      path: path,
      headers: headers,
      body: body
    }
    send_message(pid, msg)
  end

  def http_response(pid, request_id, status, headers \\ %{}, body \\ nil) do
    msg = %{
      type: "http_response",
      request_id: request_id,
      status: status,
      headers: headers,
      body: body
    }
    send_message(pid, msg)
  end

  defp send_message(pid, msg) do
    json = Jason.encode!(msg)
    WebSockex.send_frame(pid, {:text, json})
  end

  @impl WebSockex
  def handle_connect(_conn, state) do
    Logger.debug("#{state.type} connected to bridge")
    send(state.test_pid, {:connected, state.type})
    {:ok, state}
  end

  @impl WebSockex
  def handle_frame({:text, msg}, state) do
    case Jason.decode(msg) do
      {:ok, data} ->
        Logger.debug("#{state.type} received: #{inspect(data)}")
        send(state.test_pid, {:message, state.type, data})
        {:ok, state}
      
      {:error, _} ->
        {:ok, state}
    end
  end

  @impl WebSockex
  def handle_frame(_frame, state) do
    {:ok, state}
  end

  @impl WebSockex
  def handle_disconnect(_disconnect_map, state) do
    Logger.debug("#{state.type} disconnected")
    send(state.test_pid, {:disconnected, state.type})
    {:ok, state}
  end

  @impl WebSockex
  def terminate(reason, state) do
    Logger.debug("#{state.type} terminated: #{inspect(reason)}")
    :ok
  end
end

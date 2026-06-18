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

  defp max_pending_http_requests() do
    case System.get_env("BRIDGE_MAX_PENDING_HTTP_REQUESTS") do
      nil ->
        128

      "" ->
        128

      value ->
        case Integer.parse(value) do
          {n, _} when n > 0 -> n
          _ -> 128
        end
    end
  end

  defp pending_http_waiters(socket) do
    socket.assigns[:pending_http_waiters] || MapSet.new()
  end

  defp start_http_response_waiter(socket, request_id, server_pid, server_message) do
    waiters = pending_http_waiters(socket)

    if MapSet.size(waiters) >= max_pending_http_requests() do
      {:reply, {:error, %{reason: "too_many_requests"}}, socket}
    else
      channel_pid = self()
      socket_ref = socket_ref(socket)

      case Task.Supervisor.start_child(Bridge.HttpProxyTaskSupervisor, fn ->
             await_http_response(channel_pid, socket_ref, request_id, server_pid, server_message)
           end) do
        {:ok, _pid} ->
          socket = assign(socket, :pending_http_waiters, MapSet.put(waiters, request_id))
          {:noreply, socket}

        {:error, reason} ->
          Logger.warning(
            "bridge app failed to start response waiter request_id=#{request_id} reason=#{inspect(reason)}"
          )

          {:reply, {:error, %{reason: "internal_error"}}, socket}
      end
    end
  end

  defp await_http_response(channel_pid, socket_ref, request_id, server_pid, server_message) do
    topic = "tunnel:request:#{request_id}"
    Phoenix.PubSub.subscribe(Bridge.PubSub, topic)

    try do
      case safe_send(server_pid, server_message) do
        :ok ->
          monitor_ref = Process.monitor(channel_pid)
          await_http_response_loop(channel_pid, socket_ref, request_id, topic, monitor_ref)

        :error ->
          Phoenix.PubSub.unsubscribe(Bridge.PubSub, topic)

          send(channel_pid, {
            :http_response_reply,
            request_id,
            socket_ref,
            :error,
            %{reason: "server_not_found"}
          })
      end
    after
      send(channel_pid, {:http_response_waiter_done, request_id})
    end
  end

  defp await_http_response_loop(channel_pid, socket_ref, request_id, topic, monitor_ref) do
    receive do
      {:http_response, response} ->
        Phoenix.PubSub.unsubscribe(Bridge.PubSub, topic)
        Process.demonitor(monitor_ref, [:flush])
        send(channel_pid, {:http_response_reply, request_id, socket_ref, :ok, response})

      {:http_response_init, payload} ->
        send(channel_pid, {:http_response_push, request_id, "http_response_init", payload})
        await_http_response_loop(channel_pid, socket_ref, request_id, topic, monitor_ref)

      {:http_response_chunk, payload} ->
        send(channel_pid, {:http_response_push, request_id, "http_response_chunk", payload})
        await_http_response_loop(channel_pid, socket_ref, request_id, topic, monitor_ref)

      {:http_response_end, payload} ->
        Phoenix.PubSub.unsubscribe(Bridge.PubSub, topic)
        Process.demonitor(monitor_ref, [:flush])
        send(channel_pid, {:http_response_push, request_id, "http_response_end", payload})

        send(
          channel_pid,
          {:http_response_reply, request_id, socket_ref, :ok,
           %{type: "http_response_chunked", request_id: request_id}}
        )

      {:DOWN, ^monitor_ref, :process, ^channel_pid, _reason} ->
        Phoenix.PubSub.unsubscribe(Bridge.PubSub, topic)
    after
      http_timeout_ms() ->
        Phoenix.PubSub.unsubscribe(Bridge.PubSub, topic)
        Process.demonitor(monitor_ref, [:flush])

        Logger.warning(
          "bridge app request timed out while awaiting response request_id=#{request_id}"
        )

        send(channel_pid, {
          :http_response_reply,
          request_id,
          socket_ref,
          :error,
          %{reason: "timeout"}
        })
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
              session_id_result =
                Bridge.SessionManager.create_session(
                  pairing.server_id,
                  client_id,
                  server_info.node,
                  node()
                )

              case session_id_result do
                {:ok, session_id} ->
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
            start_http_response_waiter(
              socket,
              request_id,
              server_info.channel_pid,
              {:http_request, request}
            )

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
            start_http_response_waiter(
              socket,
              request_id,
              server_info.channel_pid,
              {:http_request_end, request}
            )

          {:error, :not_found} ->
            {:reply, {:error, %{reason: "server_not_found"}}, socket}
        end

      {:error, :not_found} ->
        {:reply, {:error, %{reason: "invalid_session"}}, socket}
    end
  end

  @impl true
  def handle_info({:http_response_push, _request_id, event, payload}, socket) do
    push(socket, event, payload)
    {:noreply, socket}
  end

  @impl true
  def handle_info({:http_response_reply, _request_id, socket_ref, status, payload}, socket) do
    reply(socket_ref, {status, payload})
    {:noreply, socket}
  end

  @impl true
  def handle_info({:http_response_waiter_done, request_id}, socket) do
    waiters = pending_http_waiters(socket)
    {:noreply, assign(socket, :pending_http_waiters, MapSet.delete(waiters, request_id))}
  end

  @impl true
  def terminate(_reason, _socket) do
    :ok
  end
end

defmodule Bridge.HttpTransfer do
  @moduledoc false

  use GenServer
  require Logger

  def start(options, supervisor \\ Bridge.HttpTransferSupervisor) do
    case DynamicSupervisor.start_child(supervisor, {__MODULE__, options}) do
      {:error, :max_children} -> {:error, :too_many_transfers}
      result -> result
    end
  end

  def child_spec(options) do
    %{
      id: {__MODULE__, options.request_id},
      start: {__MODULE__, :start_link, [options]},
      restart: :temporary
    }
  end

  def start_link(options), do: GenServer.start_link(__MODULE__, options)

  @impl true
  def init(options) do
    request_id = options.request_id
    topic = topic(request_id)
    :ok = Phoenix.PubSub.subscribe(Bridge.PubSub, topic)

    frontend_monitor = Process.monitor(options.frontend_pid)
    server_monitor = Process.monitor(options.server_pid)
    timeout_ref = Process.send_after(self(), :transfer_timeout, timeout_ms())

    {:ok,
     %{
       request_id: request_id,
       server_id: options.server_id,
       server_pid: options.server_pid,
       frontend_pid: options.frontend_pid,
       frontend_monitor: frontend_monitor,
       server_monitor: server_monitor,
       timeout_ref: timeout_ref,
       request_body_present: options.request_body_present,
       request_consumer: nil,
       request_consumer_monitor: nil,
       request_bytes: 0,
       request_waiting_ack: false,
       request_done: not options.request_body_present,
       response_uploader: nil,
       response_uploader_monitor: nil,
       response_bytes: 0,
       response_waiting_ack: false,
       response_init: nil,
       frontend_response_ready: false,
       completed: false
     }}
  end

  @impl true
  def handle_info(
        {:http_transfer_attach, "request_body", claims, peer, ref},
        state
      ) do
    cond do
      not valid_claims?(claims, state, "request_body") ->
        send(peer, {:http_transfer_rejected, ref, :invalid_transfer})
        {:noreply, state}

      state.request_done ->
        send(peer, {:http_transfer_rejected, ref, :already_consumed})
        {:noreply, state}

      not state.request_body_present ->
        send(peer, {:http_transfer_rejected, ref, :request_body_absent})
        {:noreply, state}

      state.request_consumer != nil ->
        send(peer, {:http_transfer_rejected, ref, :already_attached})
        {:noreply, state}

      true ->
        monitor_ref = Process.monitor(peer)
        send(peer, {:http_transfer_attached, ref})
        send(state.frontend_pid, {:http_transfer_request_demand, self()})

        {:noreply,
         %{
           state
           | request_consumer: peer,
             request_consumer_monitor: monitor_ref
         }}
    end
  end

  def handle_info(
        {:http_transfer_attach, "response_body", claims, peer, ref},
        state
      ) do
    cond do
      not valid_claims?(claims, state, "response_body") ->
        send(peer, {:http_transfer_rejected, ref, :invalid_transfer})
        {:noreply, state}

      state.response_uploader != nil ->
        send(peer, {:http_transfer_rejected, ref, :already_attached})
        {:noreply, state}

      true ->
        monitor_ref = Process.monitor(peer)
        send(peer, {:http_transfer_attached, ref})

        state = %{
          state
          | response_uploader: peer,
            response_uploader_monitor: monitor_ref
        }

        {:noreply, maybe_demand_response(state)}
    end
  end

  def handle_info(
        {:http_response_v2_init, server_id, %{"status" => status, "headers" => headers}},
        state
      )
      when is_integer(status) and is_map(headers) do
    if server_id == state.server_id and state.response_init == nil do
      send(
        state.frontend_pid,
        {:http_transfer_response_init, self(), status, headers}
      )

      {:noreply, %{state | response_init: {status, headers}}}
    else
      {:noreply, state}
    end
  end

  def handle_info({:frontend_request_chunk, frontend, data, final}, state)
      when frontend == state.frontend_pid and is_binary(data) and is_boolean(final) do
    next_bytes = state.request_bytes + byte_size(data)

    cond do
      state.request_consumer == nil or state.request_waiting_ack ->
        fail(state, 502, "invalid_request_stream_state")

      next_bytes > max_body_bytes() ->
        fail(state, 413, "request_body_too_large")

      true ->
        send(
          state.request_consumer,
          {:http_transfer_request_chunk, self(), data, final}
        )

        {:noreply,
         %{
           state
           | request_bytes: next_bytes,
             request_waiting_ack: true
         }}
    end
  end

  def handle_info({:request_chunk_ack, peer, final}, state)
      when peer == state.request_consumer and is_boolean(final) do
    cond do
      not state.request_waiting_ack ->
        fail(state, 502, "unexpected_request_ack")

      final ->
        send(peer, {:http_transfer_request_complete, self()})
        send(state.frontend_pid, {:http_transfer_request_complete, self()})

        {:noreply,
         %{
           state
           | request_waiting_ack: false,
             request_done: true
         }}

      true ->
        send(state.frontend_pid, {:http_transfer_request_demand, self()})
        {:noreply, %{state | request_waiting_ack: false}}
    end
  end

  def handle_info({:frontend_response_ready, frontend}, state)
      when frontend == state.frontend_pid do
    {:noreply, maybe_demand_response(%{state | frontend_response_ready: true})}
  end

  def handle_info({:response_upload_chunk, peer, data, final}, state)
      when peer == state.response_uploader and is_binary(data) and is_boolean(final) do
    next_bytes = state.response_bytes + byte_size(data)

    cond do
      not state.frontend_response_ready or state.response_init == nil ->
        fail(state, 502, "invalid_response_stream_state")

      state.response_waiting_ack ->
        fail(state, 502, "unexpected_response_chunk")

      next_bytes > max_body_bytes() ->
        fail(state, 502, "response_body_too_large")

      true ->
        send(
          state.frontend_pid,
          {:http_transfer_response_chunk, self(), data, final}
        )

        {:noreply,
         %{
           state
           | response_bytes: next_bytes,
             response_waiting_ack: true
         }}
    end
  end

  def handle_info({:frontend_response_ack, frontend, final}, state)
      when frontend == state.frontend_pid and is_boolean(final) do
    cond do
      not state.response_waiting_ack ->
        fail(state, 502, "unexpected_frontend_response_ack")

      final ->
        send(state.response_uploader, {:http_transfer_response_complete, self()})
        send(state.frontend_pid, {:http_transfer_complete, self()})
        cancel_timeout(state.timeout_ref)
        {:stop, :normal, %{state | response_waiting_ack: false, completed: true}}

      true ->
        send(state.response_uploader, {:http_transfer_response_demand, self()})
        {:noreply, %{state | response_waiting_ack: false}}
    end
  end

  def handle_info({:http_transfer_peer_error, peer, reason}, state) do
    if peer in [state.frontend_pid, state.request_consumer, state.response_uploader] do
      fail(state, 502, "transfer_peer_error:#{reason}")
    else
      {:noreply, state}
    end
  end

  def handle_info(:transfer_timeout, state), do: fail(state, 504, "transfer_timeout")

  def handle_info(
        {:DOWN, monitor_ref, :process, _pid, reason},
        %{frontend_monitor: monitor_ref} = state
      ) do
    cancel_server(state, "frontend_disconnected")
    {:stop, {:frontend_down, reason}, state}
  end

  def handle_info(
        {:DOWN, monitor_ref, :process, _pid, reason},
        %{server_monitor: monitor_ref} = state
      ) do
    fail(state, 503, "server_disconnected:#{inspect(reason)}")
  end

  def handle_info(
        {:DOWN, monitor_ref, :process, _pid, _reason},
        %{request_consumer_monitor: monitor_ref, request_done: true} = state
      ) do
    {:noreply, %{state | request_consumer: nil, request_consumer_monitor: nil}}
  end

  def handle_info(
        {:DOWN, monitor_ref, :process, _pid, reason},
        %{request_consumer_monitor: monitor_ref} = state
      ) do
    fail(state, 502, "request_consumer_disconnected:#{inspect(reason)}")
  end

  def handle_info(
        {:DOWN, monitor_ref, :process, _pid, reason},
        %{response_uploader_monitor: monitor_ref} = state
      ) do
    fail(state, 502, "response_uploader_disconnected:#{inspect(reason)}")
  end

  def handle_info(_message, state), do: {:noreply, state}

  @impl true
  def terminate(_reason, state) do
    cancel_timeout(state.timeout_ref)
    :ok
  end

  def topic(request_id), do: "http_transfer:#{request_id}"

  defp valid_claims?(claims, state, direction) do
    claims.request_id == state.request_id and
      claims.server_id == state.server_id and
      claims.direction == direction
  end

  defp maybe_demand_response(state) do
    if state.response_uploader != nil and state.response_init != nil and
         state.frontend_response_ready and not state.response_waiting_ack do
      send(
        state.response_uploader,
        {:http_transfer_response_demand, self()}
      )
    end

    state
  end

  defp fail(state, status, reason) do
    Logger.warning("bridge HTTP transfer failed request_id=#{state.request_id} reason=#{reason}")

    send(
      state.frontend_pid,
      {:http_transfer_error, self(), status, reason}
    )

    send_peer_error(state.request_consumer, reason)
    send_peer_error(state.response_uploader, reason)
    cancel_server(state, reason)
    cancel_timeout(state.timeout_ref)
    {:stop, :normal, state}
  end

  defp send_peer_error(nil, _reason), do: :ok

  defp send_peer_error(peer, reason) do
    send(peer, {:http_transfer_error, self(), reason})
  end

  defp cancel_server(%{completed: true}, _reason), do: :ok

  defp cancel_server(state, reason) do
    send(
      state.server_pid,
      {:http_request_v2_cancel, %{request_id: state.request_id, reason: reason}}
    )
  rescue
    ArgumentError -> :ok
  end

  defp cancel_timeout(nil), do: :ok
  defp cancel_timeout(ref), do: Process.cancel_timer(ref)

  defp timeout_ms, do: positive_env("BRIDGE_HTTP_TIMEOUT_MS", 120_000)
  defp max_body_bytes, do: positive_env("BRIDGE_HTTP_MAX_BODY_BYTES", 100 * 1024 * 1024)

  defp positive_env(name, default) do
    case System.get_env(name) do
      nil ->
        default

      "" ->
        default

      value ->
        case Integer.parse(value) do
          {parsed, ""} when parsed > 0 -> parsed
          _ -> default
        end
    end
  end
end

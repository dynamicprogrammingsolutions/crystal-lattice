defmodule Bridge.AppChannelHttpConcurrencyTest do
  use ExUnit.Case, async: false
  import Phoenix.ChannelTest

  @endpoint Bridge.Endpoint

  defp start_server_process(test_pid) do
    spawn(fn -> receive_loop(test_pid) end)
  end

  defp receive_loop(test_pid) do
    receive do
      :stop ->
        :ok

      msg ->
        send(test_pid, {:server_received, msg})
        receive_loop(test_pid)
    end
  end

  defp stop_server_process(pid), do: send(pid, :stop)

  defp setup_paired_app_channel(_context) do
    server_id = UUID.uuid4()
    client_id = UUID.uuid4()
    server_pid = start_server_process(self())

    Bridge.ServerRegistry.register_server(server_id, %{
      display_name: "Test Server",
      computer_name: "test.local",
      location: nil,
      channel_pid: server_pid
    })

    {:ok, session_id} = Bridge.SessionManager.create_session(server_id, client_id, node(), node())
    assert_receive {:server_received, {:paired, ^client_id, ^session_id}}, 1000

    {:ok, socket} = connect(Bridge.Socket, %{"type" => "app"})
    {:ok, _reply, socket} = subscribe_and_join(socket, "app:#{client_id}", %{})

    on_exit(fn ->
      Bridge.ServerRegistry.unregister_server(server_id, server_pid)
      stop_server_process(server_pid)
    end)

    %{socket: socket, session_id: session_id}
  end

  defp full_request_payload(request_id, session_id, path) do
    %{
      "request_id" => request_id,
      "session_id" => session_id,
      "method" => "GET",
      "path" => path,
      "headers" => %{},
      "body" => nil
    }
  end

  defp broadcast_full_response(request_id, status, body) do
    Phoenix.PubSub.broadcast(
      Bridge.PubSub,
      "tunnel:request:#{request_id}",
      {:http_response,
       %{
         type: "http_response",
         request_id: request_id,
         status: status,
         headers: %{"content-type" => "application/json"},
         body: body
       }}
    )
  end

  setup do
    :ets.delete_all_objects(:bridge_servers)
    :ets.delete_all_objects(:bridge_pairing_codes)
    :ets.delete_all_objects(:bridge_sessions)
    :ok
  end

  test "fast full request completes while earlier slow full request is pending", context do
    %{socket: socket, session_id: session_id} = setup_paired_app_channel(context)

    slow_id = UUID.uuid4()
    fast_id = UUID.uuid4()

    slow_ref = push(socket, "http_request", full_request_payload(slow_id, session_id, "/slow"))
    assert_receive {:server_received, {:http_request, %{request_id: ^slow_id}}}, 1000

    fast_ref = push(socket, "http_request", full_request_payload(fast_id, session_id, "/fast"))
    assert_receive {:server_received, {:http_request, %{request_id: ^fast_id}}}, 1000

    broadcast_full_response(fast_id, 200, ~s({"ok":"fast"}))

    assert_reply(fast_ref, :ok, %{request_id: ^fast_id, status: 200}, 1000)
    refute_receive %Phoenix.Socket.Reply{ref: ^slow_ref}, 50

    broadcast_full_response(slow_id, 200, ~s({"ok":"slow"}))
    assert_reply(slow_ref, :ok, %{request_id: ^slow_id, status: 200}, 1000)
  end

  test "chunked request completion does not block a later fast request", context do
    %{socket: socket, session_id: session_id} = setup_paired_app_channel(context)

    slow_id = UUID.uuid4()
    fast_id = UUID.uuid4()

    init_ref =
      push(socket, "http_request_init", %{
        "request_id" => slow_id,
        "session_id" => session_id,
        "method" => "PUT",
        "path" => "/slow",
        "headers" => %{}
      })

    assert_reply(init_ref, :ok, %{status: "accepted"}, 1000)
    assert_receive {:server_received, {:http_request_init, %{request_id: ^slow_id}}}, 1000

    chunk_ref =
      push(socket, "http_request_chunk", %{
        "request_id" => slow_id,
        "session_id" => session_id,
        "seq" => 0,
        "chunk" => "{}"
      })

    assert_reply(chunk_ref, :ok, %{status: "accepted"}, 1000)
    assert_receive {:server_received, {:http_request_chunk, %{request_id: ^slow_id}}}, 1000

    slow_end_ref =
      push(socket, "http_request_end", %{
        "request_id" => slow_id,
        "session_id" => session_id,
        "final_seq" => 0
      })

    assert_receive {:server_received, {:http_request_end, %{request_id: ^slow_id}}}, 1000

    fast_ref = push(socket, "http_request", full_request_payload(fast_id, session_id, "/fast"))
    assert_receive {:server_received, {:http_request, %{request_id: ^fast_id}}}, 1000

    broadcast_full_response(fast_id, 200, ~s({"ok":"fast"}))

    assert_reply(fast_ref, :ok, %{request_id: ^fast_id, status: 200}, 1000)
    refute_receive %Phoenix.Socket.Reply{ref: ^slow_end_ref}, 50

    broadcast_full_response(slow_id, 200, ~s({"ok":"slow"}))
    assert_reply(slow_end_ref, :ok, %{request_id: ^slow_id, status: 200}, 1000)
  end

  test "chunked response pushes remain ordered before final reply", context do
    %{socket: socket, session_id: session_id} = setup_paired_app_channel(context)

    request_id = UUID.uuid4()
    ref = push(socket, "http_request", full_request_payload(request_id, session_id, "/large"))
    assert_receive {:server_received, {:http_request, %{request_id: ^request_id}}}, 1000

    topic = "tunnel:request:#{request_id}"

    Phoenix.PubSub.broadcast(
      Bridge.PubSub,
      topic,
      {:http_response_init, %{request_id: request_id, status: 200, headers: %{}}}
    )

    Phoenix.PubSub.broadcast(
      Bridge.PubSub,
      topic,
      {:http_response_chunk, %{request_id: request_id, seq: 0, chunk: "abc"}}
    )

    Phoenix.PubSub.broadcast(
      Bridge.PubSub,
      topic,
      {:http_response_end, %{request_id: request_id, final_seq: 0}}
    )

    assert_push("http_response_init", %{request_id: ^request_id, status: 200}, 1000)
    assert_push("http_response_chunk", %{request_id: ^request_id, seq: 0, chunk: "abc"}, 1000)
    assert_push("http_response_end", %{request_id: ^request_id, final_seq: 0}, 1000)

    assert_reply(ref, :ok, %{type: "http_response_chunked", request_id: ^request_id}, 1000)
  end

  test "timeout replies cleanly and does not poison later requests", context do
    previous_timeout = System.get_env("BRIDGE_HTTP_TIMEOUT_MS")
    System.put_env("BRIDGE_HTTP_TIMEOUT_MS", "30")

    on_exit(fn ->
      case previous_timeout do
        nil -> System.delete_env("BRIDGE_HTTP_TIMEOUT_MS")
        value -> System.put_env("BRIDGE_HTTP_TIMEOUT_MS", value)
      end
    end)

    %{socket: socket, session_id: session_id} = setup_paired_app_channel(context)

    timed_out_id = UUID.uuid4()

    timeout_ref =
      push(socket, "http_request", full_request_payload(timed_out_id, session_id, "/timeout"))

    assert_receive {:server_received, {:http_request, %{request_id: ^timed_out_id}}}, 1000
    assert_reply(timeout_ref, :error, %{reason: "timeout"}, 1000)

    fast_id = UUID.uuid4()
    fast_ref = push(socket, "http_request", full_request_payload(fast_id, session_id, "/fast"))
    assert_receive {:server_received, {:http_request, %{request_id: ^fast_id}}}, 1000
    broadcast_full_response(fast_id, 200, ~s({"ok":"fast"}))

    assert_reply(fast_ref, :ok, %{request_id: ^fast_id, status: 200}, 1000)
  end
end

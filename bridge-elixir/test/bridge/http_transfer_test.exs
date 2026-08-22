defmodule Bridge.HttpTransferTest do
  use ExUnit.Case, async: false

  setup do
    previous_timeout = System.get_env("BRIDGE_HTTP_TIMEOUT_MS")
    previous_max_body = System.get_env("BRIDGE_HTTP_MAX_BODY_BYTES")

    on_exit(fn ->
      restore_env("BRIDGE_HTTP_TIMEOUT_MS", previous_timeout)
      restore_env("BRIDGE_HTTP_MAX_BODY_BYTES", previous_max_body)
    end)

    :ok
  end

  test "timeout cancels server work and removes the coordinator" do
    System.put_env("BRIDGE_HTTP_TIMEOUT_MS", "30")
    server_pid = relay_to(self())

    assert {:ok, transfer_pid} =
             Bridge.HttpTransfer.start(%{
               request_id: "timeout-request",
               server_id: "server-1",
               server_pid: server_pid,
               frontend_pid: self(),
               request_body_present: false
             })

    monitor_ref = Process.monitor(transfer_pid)

    assert_receive {:http_transfer_error, ^transfer_pid, 504, "transfer_timeout"},
                   1_000

    assert_receive {:relayed,
                    {:http_request_v2_cancel,
                     %{request_id: "timeout-request", reason: "transfer_timeout"}}},
                   1_000

    assert_receive {:DOWN, ^monitor_ref, :process, ^transfer_pid, _reason}, 1_000
  end

  test "response byte limits terminate the transfer before buffering more data" do
    System.put_env("BRIDGE_HTTP_MAX_BODY_BYTES", "4")
    server_pid = relay_to(self())

    assert {:ok, transfer_pid} =
             Bridge.HttpTransfer.start(%{
               request_id: "limited-request",
               server_id: "server-1",
               server_pid: server_pid,
               frontend_pid: self(),
               request_body_present: false
             })

    claims = %{
      request_id: "limited-request",
      server_id: "server-1",
      direction: "response_body"
    }

    attach_ref = make_ref()

    Phoenix.PubSub.broadcast(
      Bridge.PubSub,
      Bridge.HttpTransfer.topic("limited-request"),
      {:http_transfer_attach, "response_body", claims, self(), attach_ref}
    )

    assert_receive {:http_transfer_attached, ^attach_ref}, 1_000

    Phoenix.PubSub.broadcast(
      Bridge.PubSub,
      Bridge.HttpTransfer.topic("limited-request"),
      {:http_response_v2_init, "server-1", %{"status" => 200, "headers" => %{}}}
    )

    assert_receive {:http_transfer_response_init, ^transfer_pid, 200, %{}},
                   1_000

    send(transfer_pid, {:frontend_response_ready, self()})
    assert_receive {:http_transfer_response_demand, ^transfer_pid}, 1_000
    send(transfer_pid, {:response_upload_chunk, self(), "12345", true})

    assert_receive {:http_transfer_error, ^transfer_pid, 502, "response_body_too_large"},
                   1_000

    assert_receive {:http_transfer_error, ^transfer_pid, "response_body_too_large"},
                   1_000
  end

  test "request byte limits cancel the server and remove the coordinator" do
    System.put_env("BRIDGE_HTTP_MAX_BODY_BYTES", "4")
    server_pid = relay_to(self())

    assert {:ok, transfer_pid} =
             Bridge.HttpTransfer.start(%{
               request_id: "limited-request-body",
               server_id: "server-1",
               server_pid: server_pid,
               frontend_pid: self(),
               request_body_present: true
             })

    monitor_ref = Process.monitor(transfer_pid)
    claims = transfer_claims("limited-request-body", "request_body")
    attach_ref = attach("limited-request-body", "request_body", claims, self())

    assert_receive {:http_transfer_attached, ^attach_ref}, 1_000
    assert_receive {:http_transfer_request_demand, ^transfer_pid}, 1_000

    send(transfer_pid, {:frontend_request_chunk, self(), "12345", true})

    assert_receive {:http_transfer_error, ^transfer_pid, 413, "request_body_too_large"},
                   1_000

    assert_receive {:http_transfer_error, ^transfer_pid, "request_body_too_large"},
                   1_000

    assert_receive {:relayed,
                    {:http_request_v2_cancel,
                     %{request_id: "limited-request-body", reason: "request_body_too_large"}}},
                   1_000

    assert_coordinator_stopped(transfer_pid, monitor_ref)
  end

  test "active transfer admission is atomic at the supervisor child limit" do
    {:ok, supervisor} =
      DynamicSupervisor.start_link(
        strategy: :one_for_one,
        max_children: 1
      )

    on_exit(fn ->
      if Process.alive?(supervisor), do: Supervisor.stop(supervisor)
    end)

    server_pid = relay_to(self())

    assert {:ok, first_pid} =
             Bridge.HttpTransfer.start(
               transfer_options("first-limited-transfer", server_pid, self()),
               supervisor
             )

    assert {:error, :too_many_transfers} =
             Bridge.HttpTransfer.start(
               transfer_options("second-limited-transfer", server_pid, self()),
               supervisor
             )

    assert DynamicSupervisor.count_children(supervisor).active == 1
    Process.exit(first_pid, :kill)
  end

  test "invalid and duplicate transfer attachments are rejected" do
    server_pid = relay_to(self())

    assert {:ok, transfer_pid} =
             Bridge.HttpTransfer.start(transfer_options("attachment-request", server_pid, self()))

    for claims <- [
          transfer_claims("wrong-request", "response_body"),
          %{transfer_claims("attachment-request", "response_body") | server_id: "wrong-server"},
          transfer_claims("attachment-request", "request_body")
        ] do
      attach_ref =
        attach("attachment-request", "response_body", claims, self())

      assert_receive {:http_transfer_rejected, ^attach_ref, :invalid_transfer},
                     1_000
    end

    valid_claims = transfer_claims("attachment-request", "response_body")
    first_ref = attach("attachment-request", "response_body", valid_claims, self())
    assert_receive {:http_transfer_attached, ^first_ref}, 1_000

    duplicate_ref =
      attach("attachment-request", "response_body", valid_claims, self())

    assert_receive {:http_transfer_rejected, ^duplicate_ref, :already_attached},
                   1_000

    Process.exit(transfer_pid, :kill)
  end

  test "frontend loss cancels server work and removes the coordinator" do
    frontend_pid = relay_to(self(), :frontend)
    server_pid = relay_to(self())

    assert {:ok, transfer_pid} =
             Bridge.HttpTransfer.start(
               transfer_options("frontend-loss", server_pid, frontend_pid)
             )

    monitor_ref = Process.monitor(transfer_pid)
    Process.exit(frontend_pid, :kill)

    assert_receive {:relayed,
                    {:http_request_v2_cancel,
                     %{request_id: "frontend-loss", reason: "frontend_disconnected"}}},
                   1_000

    assert_coordinator_stopped(transfer_pid, monitor_ref)
  end

  test "server loss fails the frontend and removes the coordinator" do
    server_pid = relay_to(self())

    assert {:ok, transfer_pid} =
             Bridge.HttpTransfer.start(transfer_options("server-loss", server_pid, self()))

    monitor_ref = Process.monitor(transfer_pid)
    Process.exit(server_pid, :kill)

    assert_receive {:http_transfer_error, ^transfer_pid, 503, reason}, 1_000
    assert String.starts_with?(reason, "server_disconnected:")
    assert_coordinator_stopped(transfer_pid, monitor_ref)
  end

  test "request consumer loss cancels server work and removes the coordinator" do
    server_pid = relay_to(self())
    consumer_pid = relay_to(self(), :consumer)

    assert {:ok, transfer_pid} =
             Bridge.HttpTransfer.start(%{
               request_id: "request-consumer-loss",
               server_id: "server-1",
               server_pid: server_pid,
               frontend_pid: self(),
               request_body_present: true
             })

    monitor_ref = Process.monitor(transfer_pid)
    claims = transfer_claims("request-consumer-loss", "request_body")
    attach_ref = attach("request-consumer-loss", "request_body", claims, consumer_pid)

    assert_receive {:consumer, {:http_transfer_attached, ^attach_ref}}, 1_000
    assert_receive {:http_transfer_request_demand, ^transfer_pid}, 1_000
    Process.exit(consumer_pid, :kill)

    assert_receive {:http_transfer_error, ^transfer_pid, 502, reason}, 1_000
    assert String.starts_with?(reason, "request_consumer_disconnected:")

    assert_receive {:relayed, {:http_request_v2_cancel, %{request_id: "request-consumer-loss"}}},
                   1_000

    assert_coordinator_stopped(transfer_pid, monitor_ref)
  end

  test "response uploader loss cancels server work and removes the coordinator" do
    server_pid = relay_to(self())
    uploader_pid = relay_to(self(), :uploader)

    assert {:ok, transfer_pid} =
             Bridge.HttpTransfer.start(
               transfer_options("response-uploader-loss", server_pid, self())
             )

    monitor_ref = Process.monitor(transfer_pid)
    claims = transfer_claims("response-uploader-loss", "response_body")
    attach_ref = attach("response-uploader-loss", "response_body", claims, uploader_pid)

    assert_receive {:uploader, {:http_transfer_attached, ^attach_ref}}, 1_000
    Process.exit(uploader_pid, :kill)

    assert_receive {:http_transfer_error, ^transfer_pid, 502, reason}, 1_000
    assert String.starts_with?(reason, "response_uploader_disconnected:")

    assert_receive {:relayed, {:http_request_v2_cancel, %{request_id: "response-uploader-loss"}}},
                   1_000

    assert_coordinator_stopped(transfer_pid, monitor_ref)
  end

  defp transfer_options(request_id, server_pid, frontend_pid) do
    %{
      request_id: request_id,
      server_id: "server-1",
      server_pid: server_pid,
      frontend_pid: frontend_pid,
      request_body_present: false
    }
  end

  defp transfer_claims(request_id, direction) do
    %{
      request_id: request_id,
      server_id: "server-1",
      direction: direction
    }
  end

  defp attach(request_id, direction, claims, peer) do
    attach_ref = make_ref()

    Phoenix.PubSub.broadcast(
      Bridge.PubSub,
      Bridge.HttpTransfer.topic(request_id),
      {:http_transfer_attach, direction, claims, peer, attach_ref}
    )

    attach_ref
  end

  defp assert_coordinator_stopped(transfer_pid, monitor_ref) do
    assert_receive {:DOWN, ^monitor_ref, :process, ^transfer_pid, _reason}, 1_000

    refute Enum.any?(
             DynamicSupervisor.which_children(Bridge.HttpTransferSupervisor),
             fn {_id, child_pid, _type, _modules} -> child_pid == transfer_pid end
           )
  end

  defp relay_to(test_pid, tag \\ :relayed) do
    pid = spawn(fn -> relay_loop(test_pid, tag) end)

    on_exit(fn ->
      if Process.alive?(pid), do: Process.exit(pid, :kill)
    end)

    pid
  end

  defp relay_loop(test_pid, tag) do
    receive do
      message ->
        send(test_pid, {tag, message})
        relay_loop(test_pid, tag)
    end
  end

  defp restore_env(name, nil), do: System.delete_env(name)
  defp restore_env(name, value), do: System.put_env(name, value)
end

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

  defp relay_to(test_pid) do
    spawn(fn -> relay_loop(test_pid) end)
  end

  defp relay_loop(test_pid) do
    receive do
      message ->
        send(test_pid, {:relayed, message})
        relay_loop(test_pid)
    end
  end

  defp restore_env(name, nil), do: System.delete_env(name)
  defp restore_env(name, value), do: System.put_env(name, value)
end

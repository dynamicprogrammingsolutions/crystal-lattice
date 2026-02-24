defmodule Bridge.ServerChannelChunkedHttpTest do
  use ExUnit.Case, async: false

  setup do
    :ets.delete_all_objects(:bridge_servers)
    :ets.delete_all_objects(:bridge_pairing_codes)
    :ets.delete_all_objects(:bridge_sessions)
    :ok
  end

  test "http_response_init/chunk/end broadcast to request topic" do
    request_id = UUID.uuid4()
    topic = "tunnel:request:#{request_id}"
    Phoenix.PubSub.subscribe(Bridge.PubSub, topic)

    socket = %Phoenix.Socket{}

    assert {:noreply, _} = Bridge.ServerChannel.handle_in("http_response_init", %{"request_id" => request_id, "status" => 200}, socket)
    assert_receive {:http_response_init, %{"request_id" => ^request_id, "status" => 200}}, 1000

    assert {:noreply, _} = Bridge.ServerChannel.handle_in("http_response_chunk", %{"request_id" => request_id, "seq" => 0, "chunk" => "abc"}, socket)
    assert_receive {:http_response_chunk, %{"request_id" => ^request_id, "seq" => 0, "chunk" => "abc"}}, 1000

    assert {:noreply, _} = Bridge.ServerChannel.handle_in("http_response_end", %{"request_id" => request_id, "final_seq" => 0}, socket)
    assert_receive {:http_response_end, %{"request_id" => ^request_id, "final_seq" => 0}}, 1000
  end
end

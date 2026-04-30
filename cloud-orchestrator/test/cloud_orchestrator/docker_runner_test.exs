defmodule CloudOrchestrator.Runner.DockerTest do
  use ExUnit.Case

  alias CloudOrchestrator.Runner.Docker

  test "runtime container args mount instance storage and pass canonical env" do
    previous_host_data_dir = Application.get_env(:cloud_orchestrator, :host_data_dir)
    Application.put_env(:cloud_orchestrator, :host_data_dir, "/host/cloud-orchestrator")

    try do
      args =
        Docker.runtime_container_args(
          %{
            "instance_id" => "inst_test",
            "session_id" => "session-1",
            "transfer" => %{"slot_host_path" => "/host/cloud-orchestrator/transfers/tr_test"}
          },
          %{},
          30123,
          "cloud-agent-runtime:test"
        )

      assert ["run", "-d" | _] = args

      assert Enum.chunk_every(args, 2, 1, :discard)
             |> Enum.any?(&(&1 == ["-e", "CLOUD_AGENT_INSTANCE_DIR=/cloud-agent/instance"]))

      assert Enum.chunk_every(args, 2, 1, :discard)
             |> Enum.any?(
               &(&1 == ["-e", "CLOUD_AGENT_WORKSPACE_DIR=/cloud-agent/instance/workspace"])
             )

      assert Enum.chunk_every(args, 2, 1, :discard)
             |> Enum.any?(
               &(&1 == ["-e", "CLOUD_AGENT_CONFIG_PATH=/cloud-agent/instance/config/config.json"])
             )

      assert Enum.chunk_every(args, 2, 1, :discard)
             |> Enum.any?(&(&1 == ["-e", "CONFIG_DIR=/cloud-agent/instance/config/assets"]))

      assert Enum.chunk_every(args, 2, 1, :discard)
             |> Enum.any?(&(&1 == ["-e", "WORKING_DIR=/cloud-agent/instance/workspace"]))

      assert Enum.chunk_every(args, 2, 1, :discard)
             |> Enum.any?(
               &(&1 == [
                   "-v",
                   "/host/cloud-orchestrator/instances/inst_test:/cloud-agent/instance"
                 ])
             )

      assert Enum.chunk_every(args, 2, 1, :discard)
             |> Enum.any?(
               &(&1 == ["-v", "/host/cloud-orchestrator/transfers/tr_test:/transfer:ro"])
             )
    after
      Application.put_env(:cloud_orchestrator, :host_data_dir, previous_host_data_dir)
    end
  end
end

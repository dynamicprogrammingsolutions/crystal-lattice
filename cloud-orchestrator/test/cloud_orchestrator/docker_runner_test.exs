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
             |> Enum.any?(&(&1 == ["-e", "CLOUD_AGENT_CACHE_DIR=/cloud-agent/cache"]))

      assert Enum.chunk_every(args, 2, 1, :discard)
             |> Enum.any?(&(&1 == ["-e", "PIP_CACHE_DIR=/cloud-agent/cache/pip"]))

      assert Enum.chunk_every(args, 2, 1, :discard)
             |> Enum.any?(&(&1 == ["-e", "XDG_CACHE_HOME=/cloud-agent/cache/xdg"]))

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

      assert Enum.chunk_every(args, 2, 1, :discard)
             |> Enum.any?(
               &(&1 == ["-v", "/host/cloud-orchestrator/runtime-cache:/cloud-agent/cache"])
             )
    after
      Application.put_env(:cloud_orchestrator, :host_data_dir, previous_host_data_dir)
    end
  end

  test "runtime container args include configured shared profile mounts" do
    previous_host_data_dir = Application.get_env(:cloud_orchestrator, :host_data_dir)
    previous_data_dir = Application.get_env(:cloud_orchestrator, :data_dir)

    tmp_dir =
      System.tmp_dir!()
      |> Path.join("cloud-orchestrator-docker-test-#{System.unique_integer([:positive])}")

    Application.put_env(:cloud_orchestrator, :data_dir, tmp_dir)
    Application.put_env(:cloud_orchestrator, :host_data_dir, "/host/cloud-orchestrator")

    try do
      args =
        Docker.runtime_container_args(
          %{
            "instance_id" => "inst_test",
            "connection_id" => "conn_test",
            "session_id" => "session-1",
            "transfer" => %{"slot_host_path" => "/host/cloud-orchestrator/transfers/tr_test"}
          },
          %{
            "container" => %{
              "profile_id" => "iocharts",
              "cache_mounts" => [
                %{
                  "id" => "frontend-node-modules",
                  "target" => "/cloud-agent/instance/workspace/frontend/node_modules",
                  "scope" => "connection"
                }
              ],
              "mounts" => [
                %{
                  "id" => "ollama-models",
                  "target" => "/cloud-agent/cache/ollama",
                  "scope" => "profile"
                }
              ]
            }
          },
          30123,
          "cloud-agent-runtime:test"
        )

      assert Enum.chunk_every(args, 2, 1, :discard)
             |> Enum.any?(
               &(&1 == [
                   "-v",
                   "/host/cloud-orchestrator/shared-mounts/connections/conn_test/frontend-node-modules:/cloud-agent/instance/workspace/frontend/node_modules"
                 ])
             )

      assert Enum.chunk_every(args, 2, 1, :discard)
             |> Enum.any?(
               &(&1 == [
                   "-v",
                   "/host/cloud-orchestrator/shared-mounts/profiles/iocharts/ollama-models:/cloud-agent/cache/ollama"
                 ])
             )
    after
      File.rm_rf!(tmp_dir)
      Application.put_env(:cloud_orchestrator, :data_dir, previous_data_dir)
      Application.put_env(:cloud_orchestrator, :host_data_dir, previous_host_data_dir)
    end
  end

  test "docker build args use digest context metadata" do
    previous_host_data_dir = Application.get_env(:cloud_orchestrator, :host_data_dir)
    Application.put_env(:cloud_orchestrator, :host_data_dir, "/host/cloud-orchestrator")

    try do
      args =
        Docker.docker_build_args(%{
          "mode" => "dockerfile",
          "image" => "runtime:test",
          "build_context_digest" => "sha256:abc",
          "dockerfile" => "Dockerfile",
          "target" => "cloud-agent",
          "build_args" => %{"PYTHON_VERSION" => "3.12"}
        })

      assert args == [
               "build",
               "-t",
               "runtime:test",
               "--label",
               "org.crystal-lattice.cloud-runtime.digest=sha256:abc",
               "--target",
               "cloud-agent",
               "--build-arg",
               "PYTHON_VERSION=3.12",
               "-f",
               "/host/cloud-orchestrator/build-contexts/sha256:abc/context/Dockerfile",
               "/host/cloud-orchestrator/build-contexts/sha256:abc/context"
             ]
    after
      Application.put_env(:cloud_orchestrator, :host_data_dir, previous_host_data_dir)
    end
  end
end

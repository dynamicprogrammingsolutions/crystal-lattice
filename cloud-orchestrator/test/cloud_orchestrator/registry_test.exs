defmodule CloudOrchestrator.RegistryTest do
  use ExUnit.Case

  alias CloudOrchestrator.{InstanceRegistry, TransferRegistry}

  setup do
    System.put_env("CLOUD_ORCHESTRATOR_FAKE_MANAGED_SSH", "1")
    TransferRegistry.reset()
    InstanceRegistry.reset()

    on_exit(fn ->
      TransferRegistry.reset()
      System.delete_env("CLOUD_ORCHESTRATOR_FAKE_MANAGED_SSH")
    end)

    :ok
  end

  test "creates opaque transfer slots and starts instances from ready transfer refs" do
    assert {:ok, transfer} =
             TransferRegistry.create(%{
               "direction" => "upload",
               "method" => "managed_ssh",
               "public_host" => "cloud.example.test",
               "port" => 22001,
               "public_key" => "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKey test"
             })

    assert transfer["transfer_id"] =~ "tr_"
    assert transfer["endpoint"]["host"] == "cloud.example.test"
    assert transfer["endpoint"]["port"] == 22001
    refute Map.has_key?(transfer, "artifact_name")
    refute Map.has_key?(transfer, "archive")

    assert {:ok, ready} = TransferRegistry.mark_ready(transfer["transfer_id"])
    assert ready["state"] == "ready"

    assert {:ok, instance} =
             InstanceRegistry.start_instance(%{
               "session_id" => "session-1",
               "transfer_ref" => %{"transfer_id" => transfer["transfer_id"]}
             })

    assert instance["instance_id"] =~ "inst_"
    assert instance["state"] == "running"
    assert instance["session_id"] == "session-1"
    assert is_binary(instance["token"])
    refute Map.has_key?(instance, "proxy_base_url")
  end

  test "refuses to start from a transfer that is not ready" do
    assert {:ok, transfer} =
             TransferRegistry.create(%{
               "direction" => "upload",
               "public_key" => "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKey test"
             })

    assert {:error, 409, %{error: "transfer_not_ready"}} =
             InstanceRegistry.start_instance(%{
               "session_id" => "session-1",
               "transfer_ref" => %{"transfer_id" => transfer["transfer_id"]}
             })
  end
end

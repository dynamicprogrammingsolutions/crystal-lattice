defmodule CloudOrchestrator.TestAsyncRunner do
  @behaviour CloudOrchestrator.Runner

  import Plug.Conn

  @impl true
  def start_instance(instance, _params) do
    {:ok,
     instance
     |> Map.put("state", "starting")
     |> Map.put("startup_stage", "container_started")
     |> Map.put("proxy_base_url", "http://127.0.0.1:9")
     |> Map.put("runner", "test_async")}
  end

  @impl true
  def runtime_status(_instance) do
    Application.get_env(:cloud_orchestrator, :test_async_runtime_status, {:starting, %{}})
  end

  @impl true
  def recent_logs(_instance), do: "test runtime log"

  @impl true
  def export_instance(instance, params) do
    {:ok, %{"instance_id" => instance["instance_id"], "transfer_ref" => params["transfer_ref"]}}
  end

  @impl true
  def close_instance(instance, _params) do
    {:ok, %{"instance_id" => instance["instance_id"], "state" => "closed"}}
  end

  @impl true
  def handle_proxy_request(_instance, conn, _path) do
    conn
    |> put_resp_content_type("application/json")
    |> send_resp(200, Jason.encode!(%{ok: true}))
  end

  @impl true
  def handle_proxy_request_result(_instance, _conn, _path) do
    {:ok,
     %{
       status: 200,
       headers: [{"content-type", "application/json"}],
       body: Jason.encode!(%{ok: true})
     }}
  end
end

defmodule CloudOrchestrator.RegistryTest do
  use ExUnit.Case

  alias CloudOrchestrator.{ConnectionRegistry, InstanceRegistry, Token, TransferRegistry}

  setup do
    System.put_env("CLOUD_ORCHESTRATOR_FAKE_MANAGED_SSH", "1")
    previous_runner = Application.get_env(:cloud_orchestrator, :runner)
    previous_async_status = Application.get_env(:cloud_orchestrator, :test_async_runtime_status)

    previous_transfer_public_host =
      Application.get_env(:cloud_orchestrator, :transfer_public_host)

    TransferRegistry.reset()
    InstanceRegistry.reset()
    ConnectionRegistry.reset()

    on_exit(fn ->
      restore_env(:runner, previous_runner)
      restore_env(:test_async_runtime_status, previous_async_status)
      restore_env(:transfer_public_host, previous_transfer_public_host)
      TransferRegistry.reset()
      InstanceRegistry.reset()
      ConnectionRegistry.reset()
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

  test "managed SSH transfer endpoints use configured transfer public host by default" do
    Application.put_env(:cloud_orchestrator, :transfer_public_host, "origin.example.test")

    assert {:ok, transfer} =
             TransferRegistry.create(%{
               "direction" => "upload",
               "method" => "managed_ssh",
               "port" => 22002,
               "public_key" => "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKey test"
             })

    assert transfer["endpoint"]["host"] == "origin.example.test"
    assert transfer["endpoint"]["port"] == 22002
  end

  test "managed SSH request public_host overrides configured transfer public host" do
    Application.put_env(:cloud_orchestrator, :transfer_public_host, "origin.example.test")

    assert {:ok, transfer} =
             TransferRegistry.create(%{
               "direction" => "upload",
               "method" => "managed_ssh",
               "public_host" => "override.example.test",
               "port" => 22003,
               "public_key" => "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKey test"
             })

    assert transfer["endpoint"]["host"] == "override.example.test"
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

  test "reuses connection keys and routes sessions to separate instances" do
    assert {:ok, transfer_1} = ready_transfer()
    assert {:ok, transfer_2} = ready_transfer()

    assert {:ok, instance_1} =
             ConnectionRegistry.start_instance(%{
               "connection_ref" => %{
                 "connection_key" => "local-server-test",
                 "reuse" => true,
                 "metadata" => %{"label" => "Local Test"}
               },
               "session_id" => "session-1",
               "transfer_ref" => %{"transfer_id" => transfer_1["transfer_id"]}
             })

    assert {:ok, instance_2} =
             ConnectionRegistry.start_instance(%{
               "connection_ref" => %{
                 "connection_key" => "local-server-test",
                 "reuse" => true
               },
               "session_id" => "session-2",
               "transfer_ref" => %{"transfer_id" => transfer_2["transfer_id"]}
             })

    assert instance_1["connection_id"] == instance_2["connection_id"]
    assert instance_1["instance_id"] != instance_2["instance_id"]

    assert {:ok, connection} = ConnectionRegistry.get(instance_1["connection_id"])
    assert connection["default_instance_id"] == instance_1["instance_id"]
    assert connection["instance_ids"] == [instance_1["instance_id"], instance_2["instance_id"]]
    refute Map.has_key?(connection, "connection_key")

    assert {:ok, routed_1} =
             ConnectionRegistry.resolve_route(instance_1["connection_id"], "session-1")

    assert {:ok, routed_2} =
             ConnectionRegistry.resolve_route(instance_1["connection_id"], "session-2")

    assert routed_1["instance_id"] == instance_1["instance_id"]
    assert routed_2["instance_id"] == instance_2["instance_id"]

    assert {:ok, claims} = Token.verify(instance_1["token"])
    assert claims["connection_id"] == instance_1["connection_id"]
    assert claims["instance_id"] == instance_1["instance_id"]
  end

  test "registers routes for sessions created through an existing connection instance" do
    assert {:ok, transfer} = ready_transfer()

    assert {:ok, instance} =
             ConnectionRegistry.start_instance(%{
               "connection_ref" => %{"connection_key" => "route-created-session", "reuse" => true},
               "session_id" => "session-original",
               "transfer_ref" => %{"transfer_id" => transfer["transfer_id"]}
             })

    connection_id = instance["connection_id"]
    instance_id = instance["instance_id"]

    assert :ok =
             ConnectionRegistry.register_route(
               connection_id,
               "session-cloud-created",
               instance_id
             )

    assert {:ok, routed} =
             ConnectionRegistry.resolve_route(connection_id, "session-cloud-created")

    assert routed["instance_id"] == instance_id

    assert {:error, :not_found} =
             ConnectionRegistry.register_route(
               "missing-connection",
               "session-cloud-created",
               instance_id
             )

    assert {:error, :invalid_session_id} =
             ConnectionRegistry.register_route(connection_id, "", instance_id)

    assert {:error, :instance_not_in_connection} =
             ConnectionRegistry.register_route(connection_id, "session-other", "missing-instance")
  end

  test "async runners return starting instances and later transition to running" do
    Application.put_env(:cloud_orchestrator, :runner, CloudOrchestrator.TestAsyncRunner)

    Application.put_env(
      :cloud_orchestrator,
      :test_async_runtime_status,
      {:starting, %{"startup_stage" => "agent_application_initializing"}}
    )

    assert {:ok, transfer} =
             TransferRegistry.create(%{
               "direction" => "upload",
               "public_key" => "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKey test"
             })

    assert {:ok, _ready} = TransferRegistry.mark_ready(transfer["transfer_id"])

    assert {:ok, instance} =
             InstanceRegistry.start_instance(%{
               "session_id" => "session-async",
               "transfer_ref" => %{"transfer_id" => transfer["transfer_id"]}
             })

    assert instance["state"] == "starting"
    assert instance["startup_stage"] == "container_started"
    assert is_binary(instance["token"])

    assert {:ok, stored} = InstanceRegistry.get(instance["instance_id"])
    assert stored["state"] == "starting"

    Application.put_env(
      :cloud_orchestrator,
      :test_async_runtime_status,
      {:ready, %{"startup_stage" => "ready"}}
    )

    assert eventually(fn ->
             {:ok, updated} = InstanceRegistry.get(instance["instance_id"])
             updated["state"] == "running"
           end)
  end

  test "export refuses instances that are not ready" do
    Application.put_env(:cloud_orchestrator, :runner, CloudOrchestrator.TestAsyncRunner)

    Application.put_env(
      :cloud_orchestrator,
      :test_async_runtime_status,
      {:starting, %{"startup_stage" => "agent_application_initializing"}}
    )

    assert {:ok, transfer} =
             TransferRegistry.create(%{
               "direction" => "upload",
               "public_key" => "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKey test"
             })

    assert {:ok, _ready} = TransferRegistry.mark_ready(transfer["transfer_id"])

    assert {:ok, instance} =
             InstanceRegistry.start_instance(%{
               "session_id" => "session-async",
               "transfer_ref" => %{"transfer_id" => transfer["transfer_id"]}
             })

    assert {:error, 503, %{error: "runtime_not_ready", instance: public}} =
             InstanceRegistry.export_instance(instance["instance_id"], %{})

    assert public["state"] == "starting"
  end

  defp eventually(predicate) do
    deadline = System.monotonic_time(:millisecond) + 2_000
    eventually(predicate, deadline)
  end

  defp eventually(predicate, deadline) do
    if predicate.() do
      true
    else
      if System.monotonic_time(:millisecond) < deadline do
        Process.sleep(25)
        eventually(predicate, deadline)
      else
        false
      end
    end
  end

  defp restore_env(key, nil), do: Application.delete_env(:cloud_orchestrator, key)
  defp restore_env(key, value), do: Application.put_env(:cloud_orchestrator, key, value)

  defp ready_transfer do
    with {:ok, transfer} <-
           TransferRegistry.create(%{
             "direction" => "upload",
             "public_key" => "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKey test"
           }) do
      TransferRegistry.mark_ready(transfer["transfer_id"])
    end
  end
end

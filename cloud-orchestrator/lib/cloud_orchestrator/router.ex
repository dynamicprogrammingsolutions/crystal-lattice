defmodule CloudOrchestrator.Router do
  use Plug.Router

  alias CloudOrchestrator.{InstanceRegistry, Proxy, Token, TransferRegistry}

  plug(:match)
  plug(:dispatch)

  get "/health" do
    send_json(conn, 200, %{
      status: "healthy",
      service: "cloud-orchestrator",
      transfers: TransferRegistry.count(),
      instances: InstanceRegistry.count()
    })
  end

  post "/transfers" do
    with :ok <- authorize_control(conn),
         {:ok, params} <- read_json_params(conn),
         {:ok, transfer} <- TransferRegistry.create(params) do
      send_json(conn, 201, transfer)
    else
      {:error, :unauthorized} -> send_json(conn, 401, %{error: "unauthorized"})
      {:error, status, payload} -> send_json(conn, status, payload)
      {:error, reason} -> send_json(conn, 400, %{error: to_string(reason)})
    end
  end

  post "/transfers/:transfer_id/ready" do
    with :ok <- authorize_control(conn) do
      case TransferRegistry.mark_ready(transfer_id) do
        {:ok, transfer} -> send_json(conn, 200, transfer)
        {:error, :not_found} -> send_json(conn, 404, %{error: "transfer_not_found"})
      end
    else
      {:error, :unauthorized} -> send_json(conn, 401, %{error: "unauthorized"})
    end
  end

  put "/transfers/:transfer_id/upload" do
    with :ok <- authorize_control(conn),
         {:ok, body, _conn} <-
           Plug.Conn.read_body(conn, length: 200_000_000, read_length: 1_000_000),
         {:ok, transfer} <- TransferRegistry.upload_bundle(transfer_id, body) do
      send_json(conn, 200, transfer)
    else
      {:error, :unauthorized} -> send_json(conn, 401, %{error: "unauthorized"})
      {:error, :not_found} -> send_json(conn, 404, %{error: "transfer_not_found"})
      {:more, _body, _conn} -> send_json(conn, 413, %{error: "upload_too_large"})
      {:error, reason} -> send_json(conn, 400, %{error: to_string(reason)})
    end
  end

  get "/transfers/:transfer_id/download" do
    with :ok <- authorize_control(conn),
         {:ok, body} <- TransferRegistry.read_bundle(transfer_id) do
      conn
      |> put_resp_content_type("application/gzip")
      |> send_resp(200, body)
    else
      {:error, :unauthorized} -> send_json(conn, 401, %{error: "unauthorized"})
      {:error, :not_found} -> send_json(conn, 404, %{error: "transfer_not_found"})
    end
  end

  delete "/transfers/:transfer_id" do
    with :ok <- authorize_control(conn) do
      case TransferRegistry.delete(transfer_id) do
        :ok -> send_json(conn, 200, %{status: "deleted", transfer_id: transfer_id})
        {:error, :not_found} -> send_json(conn, 404, %{error: "transfer_not_found"})
      end
    else
      {:error, :unauthorized} -> send_json(conn, 401, %{error: "unauthorized"})
    end
  end

  post "/instances" do
    with :ok <- authorize_control(conn),
         {:ok, params} <- read_json_params(conn),
         {:ok, instance} <- InstanceRegistry.start_instance(params) do
      send_json(conn, 201, instance)
    else
      {:error, :unauthorized} -> send_json(conn, 401, %{error: "unauthorized"})
      {:error, status, payload} -> send_json(conn, status, payload)
      {:error, reason} -> send_json(conn, 400, %{error: to_string(reason)})
    end
  end

  get "/instances/:instance_id" do
    case InstanceRegistry.get(instance_id) do
      {:ok, instance} -> send_json(conn, 200, instance)
      {:error, :not_found} -> send_json(conn, 404, %{error: "instance_not_found"})
    end
  end

  post "/instances/:instance_id/export" do
    with :ok <- authorize_control(conn),
         {:ok, params} <- read_json_params(conn),
         {:ok, result} <- InstanceRegistry.export_instance(instance_id, params) do
      send_json(conn, 200, result)
    else
      {:error, :unauthorized} -> send_json(conn, 401, %{error: "unauthorized"})
      {:error, :not_found} -> send_json(conn, 404, %{error: "instance_not_found"})
      {:error, status, payload} -> send_json(conn, status, payload)
    end
  end

  post "/instances/:instance_id/close" do
    with :ok <- authorize_control(conn),
         {:ok, params} <- read_json_params(conn),
         {:ok, result} <- InstanceRegistry.close_instance(instance_id, params) do
      send_json(conn, 200, result)
    else
      {:error, :unauthorized} -> send_json(conn, 401, %{error: "unauthorized"})
      {:error, :not_found} -> send_json(conn, 404, %{error: "instance_not_found"})
      {:error, status, payload} -> send_json(conn, status, payload)
    end
  end

  defp authorize_control(conn) do
    case Application.get_env(:cloud_orchestrator, :control_token) do
      nil ->
        :ok

      "" ->
        :ok

      expected ->
        case get_req_header(conn, "authorization") do
          ["Bearer " <> token] ->
            if Plug.Crypto.secure_compare(token, expected), do: :ok, else: {:error, :unauthorized}

          _ ->
            {:error, :unauthorized}
        end
    end
  end

  match "/instances/:instance_id/proxy/*path" do
    with :ok <- authorize_proxy(conn, instance_id),
         {:ok, instance} <- InstanceRegistry.get_internal(instance_id) do
      Proxy.forward(conn, instance, "/" <> Enum.join(path, "/"))
    else
      {:error, :unauthorized} -> send_json(conn, 401, %{error: "unauthorized"})
      {:error, :not_found} -> send_json(conn, 404, %{error: "instance_not_found"})
    end
  end

  match _ do
    send_json(conn, 404, %{error: "not_found"})
  end

  defp authorize_proxy(conn, instance_id) do
    with ["Bearer " <> token] <- get_req_header(conn, "authorization"),
         {:ok, claims} <- Token.verify(token),
         true <- Map.get(claims, "instance_id") == instance_id do
      :ok
    else
      _ -> {:error, :unauthorized}
    end
  end

  defp read_json_params(conn) do
    case conn.body_params do
      %Plug.Conn.Unfetched{} -> {:ok, %{}}
      params when is_map(params) -> {:ok, params}
      _ -> {:error, 400, %{error: "invalid_json"}}
    end
  end

  defp send_json(conn, status, data) do
    conn
    |> put_resp_content_type("application/json")
    |> send_resp(status, Jason.encode!(data))
  end
end

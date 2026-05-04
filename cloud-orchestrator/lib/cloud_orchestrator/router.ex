defmodule CloudOrchestrator.Router do
  use Plug.Router

  alias CloudOrchestrator.{ConnectionRegistry, InstanceRegistry, Proxy, Token, TransferRegistry}

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
         {:ok, instance} <- ConnectionRegistry.start_instance(params) do
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
         {:ok, result} <- ConnectionRegistry.close_instance(instance_id, params) do
      send_json(conn, 200, result)
    else
      {:error, :unauthorized} -> send_json(conn, 401, %{error: "unauthorized"})
      {:error, :not_found} -> send_json(conn, 404, %{error: "instance_not_found"})
      {:error, status, payload} -> send_json(conn, status, payload)
    end
  end

  post "/connections" do
    with :ok <- authorize_control(conn),
         {:ok, params} <- read_json_params(conn),
         {:ok, connection} <- ConnectionRegistry.create_connection(params) do
      send_json(conn, 201, connection)
    else
      {:error, :unauthorized} -> send_json(conn, 401, %{error: "unauthorized"})
      {:error, :connection_not_found} -> send_json(conn, 404, %{error: "connection_not_found"})
      {:error, :connection_key_exists} -> send_json(conn, 409, %{error: "connection_key_exists"})
      {:error, status, payload} -> send_json(conn, status, payload)
      {:error, reason} -> send_json(conn, 400, %{error: to_string(reason)})
    end
  end

  get "/connections/:connection_id" do
    case ConnectionRegistry.get(connection_id) do
      {:ok, connection} -> send_json(conn, 200, connection)
      {:error, :not_found} -> send_json(conn, 404, %{error: "connection_not_found"})
    end
  end

  get "/connections/:connection_id/sessions" do
    with :ok <- authorize_connection_proxy(conn, connection_id),
         {:ok, result} <- ConnectionRegistry.list_sessions(connection_id) do
      send_json(conn, 200, result)
    else
      {:error, :unauthorized} -> send_json(conn, 401, %{error: "unauthorized"})
      {:error, :not_found} -> send_json(conn, 404, %{error: "connection_not_found"})
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
      InstanceRegistry.handle_proxy_request(instance, conn, "/" <> Enum.join(path, "/"))
    else
      {:error, :unauthorized} -> send_json(conn, 401, %{error: "unauthorized"})
      {:error, :not_found} -> send_json(conn, 404, %{error: "instance_not_found"})
    end
  end

  match "/connections/:connection_id/proxy/*path" do
    with :ok <- authorize_connection_proxy(conn, connection_id) do
      case resolve_connection_proxy_instance(conn, connection_id, path) do
        {:ok, instance} ->
          handle_connection_proxy_request(conn, connection_id, instance, path)

        {:sessions, result} ->
          send_json(conn, 200, result)

        {:error, :not_found} ->
          send_json(conn, 404, %{error: "route_not_found"})

        {:error, status, payload} ->
          send_json(conn, status, payload)
      end
    else
      {:error, :unauthorized} -> send_json(conn, 401, %{error: "unauthorized"})
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

  defp authorize_connection_proxy(conn, connection_id) do
    with ["Bearer " <> token] <- get_req_header(conn, "authorization"),
         {:ok, claims} <- Token.verify(token),
         true <- Map.get(claims, "connection_id") == connection_id do
      :ok
    else
      _ -> {:error, :unauthorized}
    end
  end

  defp resolve_connection_proxy_instance(%{method: "GET"}, connection_id, ["sessions"]) do
    case ConnectionRegistry.list_sessions(connection_id) do
      {:ok, result} -> {:sessions, result}
      error -> error
    end
  end

  defp resolve_connection_proxy_instance(conn, connection_id, path) do
    case session_id_from_proxy(conn, path) do
      nil ->
        ConnectionRegistry.default_instance(connection_id)

      session_id ->
        case ConnectionRegistry.resolve_route(connection_id, session_id) do
          {:error, :not_found} -> ConnectionRegistry.default_instance(connection_id)
          other -> other
        end
    end
  end

  defp handle_connection_proxy_request(%{method: "POST"} = conn, connection_id, instance, [
         "sessions"
       ]) do
    case InstanceRegistry.handle_proxy_request_result(instance, conn, "/sessions") do
      {:ok, response} ->
        maybe_register_created_session(connection_id, instance["instance_id"], response)
        Proxy.send_proxy_response(conn, response)

      {:error, reason} ->
        send_json(conn, 502, %{error: "proxy_failed", detail: inspect(reason)})
    end
  end

  defp handle_connection_proxy_request(conn, _connection_id, instance, path) do
    InstanceRegistry.handle_proxy_request(instance, conn, "/" <> Enum.join(path, "/"))
  end

  defp maybe_register_created_session(connection_id, instance_id, %{status: status, body: body})
       when status in 200..299 do
    case created_session_id(body) do
      nil -> :ok
      session_id -> ConnectionRegistry.register_route(connection_id, session_id, instance_id)
    end
  end

  defp maybe_register_created_session(_connection_id, _instance_id, _response), do: :ok

  defp created_session_id(body) when is_binary(body) do
    with {:ok, payload} <- Jason.decode(body) do
      case payload do
        %{"session" => %{"session_id" => session_id}}
        when is_binary(session_id) and session_id != "" ->
          session_id

        %{"session_id" => session_id} when is_binary(session_id) and session_id != "" ->
          session_id

        _ ->
          nil
      end
    else
      _ -> nil
    end
  end

  defp created_session_id(_body), do: nil

  defp session_id_from_proxy(_conn, ["sessions", session_id | _rest])
       when is_binary(session_id) do
    URI.decode(session_id)
  end

  defp session_id_from_proxy(conn, ["events"]) do
    conn = fetch_query_params(conn)

    case conn.query_params do
      %{"session_id" => session_id} when is_binary(session_id) and session_id != "" -> session_id
      _ -> nil
    end
  end

  defp session_id_from_proxy(_conn, _path), do: nil

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

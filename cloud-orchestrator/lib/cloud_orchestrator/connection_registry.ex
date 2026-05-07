defmodule CloudOrchestrator.ConnectionRegistry do
  use GenServer

  alias CloudOrchestrator.{Id, InstanceRegistry, Token}

  def start_link(_opts) do
    GenServer.start_link(__MODULE__, initial_state(), name: __MODULE__)
  end

  def create_connection(params), do: GenServer.call(__MODULE__, {:create_connection, params})
  def get(id), do: GenServer.call(__MODULE__, {:get, id})
  def start_instance(params), do: GenServer.call(__MODULE__, {:start_instance, params}, 60_000)

  def close_instance(id, params),
    do: GenServer.call(__MODULE__, {:close_instance, id, params}, 60_000)

  def resolve_route(connection_id, session_id),
    do: GenServer.call(__MODULE__, {:resolve_route, connection_id, session_id})

  def register_route(connection_id, session_id, instance_id),
    do: GenServer.call(__MODULE__, {:register_route, connection_id, session_id, instance_id})

  def default_instance(connection_id),
    do: GenServer.call(__MODULE__, {:default_instance, connection_id})

  def list_sessions(connection_id),
    do: GenServer.call(__MODULE__, {:list_sessions, connection_id}, 60_000)

  def reset, do: GenServer.call(__MODULE__, :reset)

  @impl true
  def init(_opts), do: {:ok, initial_state()}

  @impl true
  def handle_call({:create_connection, params}, _from, state) do
    case resolve_or_create_connection(connection_ref(params), state) do
      {:ok, connection, next_state} ->
        {:reply, {:ok, add_token(public_connection(connection))}, next_state}

      {:error, reason} ->
        {:reply, {:error, reason}, state}
    end
  end

  def handle_call({:get, id}, _from, state) do
    {:reply, fetch_connection(state, id) |> map_ok(&public_connection/1), state}
  end

  def handle_call({:start_instance, params}, _from, state) do
    with {:ok, connection, state} <- resolve_or_create_connection(connection_ref(params), state),
         params <- Map.put(params, "connection_id", connection["connection_id"]),
         {:ok, instance} <- InstanceRegistry.start_instance(params) do
      instance_id = instance["instance_id"]
      session_id = instance["session_id"]
      connection = register_instance(connection, instance_id)

      state =
        state
        |> put_connection(connection)
        |> put_route(connection["connection_id"], session_id, instance_id)

      {:reply, {:ok, instance}, state}
    else
      {:error, reason} when is_atom(reason) ->
        {:reply, {:error, connection_error_status(reason), %{error: to_string(reason)}}, state}

      {:error, _status, _payload} = error ->
        {:reply, error, state}
    end
  end

  def handle_call({:close_instance, id, params}, _from, state) do
    case InstanceRegistry.close_instance(id, params) do
      {:ok, result} ->
        {:reply, {:ok, result}, remove_instance_routes(state, id)}

      error ->
        {:reply, error, state}
    end
  end

  def handle_call({:resolve_route, connection_id, session_id}, _from, state) do
    reply =
      with {:ok, _connection} <- fetch_connection(state, connection_id),
           {:ok, instance_id} <- fetch_route(state, connection_id, session_id),
           {:ok, instance} <- InstanceRegistry.get_internal(instance_id) do
        {:ok, instance}
      end

    {:reply, reply, state}
  end

  def handle_call({:register_route, connection_id, session_id, instance_id}, _from, state) do
    with {:ok, connection} <- fetch_connection(state, connection_id),
         :ok <- validate_session_id(session_id),
         true <- instance_id in (connection["instance_ids"] || []),
         {:ok, _instance} <- InstanceRegistry.get_internal(instance_id) do
      {:reply, :ok, put_route(state, connection_id, session_id, instance_id)}
    else
      false -> {:reply, {:error, :instance_not_in_connection}, state}
      error -> {:reply, error, state}
    end
  end

  def handle_call({:default_instance, connection_id}, _from, state) do
    reply =
      with {:ok, connection} <- fetch_connection(state, connection_id),
           {:ok, instance_id} <- default_instance_id(connection),
           {:ok, instance} <- InstanceRegistry.get_internal(instance_id) do
        {:ok, instance}
      end

    {:reply, reply, state}
  end

  def handle_call({:list_sessions, connection_id}, _from, state) do
    reply =
      with {:ok, connection} <- fetch_connection(state, connection_id) do
        aggregate_sessions(connection, state)
      end

    {:reply, reply, state}
  end

  def handle_call(:reset, _from, _state), do: {:reply, :ok, initial_state()}

  defp initial_state do
    %{
      connections: %{},
      keys: %{},
      routes: %{}
    }
  end

  defp connection_ref(%{"connection_ref" => ref}) when is_map(ref), do: ref
  defp connection_ref(params) when is_map(params), do: params

  defp resolve_or_create_connection(ref, state) do
    cond do
      is_binary(ref["connection_id"]) and ref["connection_id"] != "" ->
        case fetch_connection(state, ref["connection_id"]) do
          {:ok, connection} -> {:ok, connection, state}
          {:error, :not_found} -> {:error, :connection_not_found}
        end

      is_binary(ref["connection_key"]) and ref["connection_key"] != "" and ref["reuse"] != false ->
        case Map.fetch(state.keys, ref["connection_key"]) do
          {:ok, connection_id} ->
            {:ok, Map.fetch!(state.connections, connection_id), state}

          :error ->
            create_new_connection(ref, state)
        end

      is_binary(ref["connection_key"]) and ref["connection_key"] != "" and
          Map.has_key?(state.keys, ref["connection_key"]) ->
        {:error, :connection_key_exists}

      true ->
        create_new_connection(ref, state)
    end
  end

  defp create_new_connection(ref, state) do
    connection_id = Id.new("conn")
    connection_key = normalized_optional(ref["connection_key"])

    connection = %{
      "connection_id" => connection_id,
      "connection_key" => connection_key,
      "metadata" => metadata(ref),
      "state" => "active",
      "default_instance_id" => nil,
      "instance_ids" => [],
      "created_at" => now(),
      "updated_at" => now()
    }

    {:ok, connection, put_connection(state, connection)}
  end

  defp metadata(%{"metadata" => metadata}) when is_map(metadata), do: metadata
  defp metadata(_ref), do: %{}

  defp normalized_optional(value) when is_binary(value) and value != "", do: value
  defp normalized_optional(_value), do: nil

  defp put_connection(state, connection) do
    state =
      put_in(state.connections[connection["connection_id"]], connection)

    if connection["connection_key"] do
      put_in(state.keys[connection["connection_key"]], connection["connection_id"])
    else
      state
    end
  end

  defp put_route(state, _connection_id, nil, _instance_id), do: state

  defp put_route(state, connection_id, session_id, instance_id) do
    put_in(state.routes[{connection_id, session_id}], instance_id)
  end

  defp register_instance(connection, instance_id) do
    instance_ids = connection["instance_ids"] || []

    connection
    |> Map.put("default_instance_id", connection["default_instance_id"] || instance_id)
    |> Map.put("instance_ids", Enum.uniq(instance_ids ++ [instance_id]))
    |> Map.put("updated_at", now())
  end

  defp remove_instance_routes(state, instance_id) do
    routes =
      state.routes
      |> Enum.reject(fn {_route, routed_instance_id} -> routed_instance_id == instance_id end)
      |> Map.new()

    connections =
      state.connections
      |> Enum.map(fn {connection_id, connection} ->
        instance_ids = Enum.reject(connection["instance_ids"] || [], &(&1 == instance_id))

        default_instance_id =
          if connection["default_instance_id"] == instance_id,
            do: List.first(instance_ids),
            else: connection["default_instance_id"]

        {connection_id,
         connection
         |> Map.put("instance_ids", instance_ids)
         |> Map.put("default_instance_id", default_instance_id)
         |> Map.put("updated_at", now())}
      end)
      |> Map.new()

    %{state | connections: connections, routes: routes}
  end

  defp fetch_connection(state, id) do
    case Map.fetch(state.connections, id) do
      {:ok, connection} -> {:ok, connection}
      :error -> {:error, :not_found}
    end
  end

  defp fetch_route(state, connection_id, session_id) do
    case Map.fetch(state.routes, {connection_id, session_id}) do
      {:ok, instance_id} -> {:ok, instance_id}
      :error -> {:error, :not_found}
    end
  end

  defp default_instance_id(%{"default_instance_id" => id}) when is_binary(id), do: {:ok, id}
  defp default_instance_id(%{"instance_ids" => [id | _]}) when is_binary(id), do: {:ok, id}
  defp default_instance_id(_connection), do: {:error, :not_found}

  defp validate_session_id(session_id) when is_binary(session_id) and session_id != "", do: :ok
  defp validate_session_id(_session_id), do: {:error, :invalid_session_id}

  defp aggregate_sessions(connection, state) do
    allowed_session_ids =
      state.routes
      |> Enum.filter(fn {{connection_id, _session_id}, instance_id} ->
        connection_id == connection["connection_id"] and
          instance_id in (connection["instance_ids"] || [])
      end)
      |> Enum.map(fn {{_connection_id, session_id}, _instance_id} -> session_id end)
      |> MapSet.new()

    connection["instance_ids"]
    |> Enum.reduce_while({:ok, []}, fn instance_id, {:ok, acc} ->
      with {:ok, instance} <- InstanceRegistry.get_internal(instance_id),
           true <- instance["state"] == "running",
           {:ok, sessions} <- fetch_instance_sessions(instance) do
        filtered =
          Enum.filter(sessions, fn session ->
            is_map(session) and MapSet.member?(allowed_session_ids, session["session_id"])
          end)

        {:cont, {:ok, acc ++ filtered}}
      else
        {:error, reason} ->
          {:halt, {:error, 502, %{error: "session_aggregation_failed", detail: inspect(reason)}}}

        false ->
          {:cont, {:ok, acc}}
      end
    end)
    |> case do
      {:ok, sessions} -> {:ok, %{"sessions" => dedupe_sessions(sessions)}}
      error -> error
    end
  end

  defp fetch_instance_sessions(%{"proxy_base_url" => base_url}) when is_binary(base_url) do
    request = Finch.build(:get, "#{base_url}/sessions")

    case Finch.request(request, CloudOrchestrator.Finch, receive_timeout: 30_000) do
      {:ok, %{status: status, body: body}} when status in 200..299 ->
        case Jason.decode(body) do
          {:ok, %{"sessions" => sessions}} when is_list(sessions) -> {:ok, sessions}
          {:ok, sessions} when is_list(sessions) -> {:ok, sessions}
          _ -> {:error, :invalid_sessions_response}
        end

      {:ok, %{status: status, body: body}} ->
        {:error, "HTTP #{status}: #{bounded(body)}"}

      {:error, reason} ->
        {:error, reason}
    end
  end

  defp fetch_instance_sessions(_instance), do: {:error, :instance_not_proxyable}

  defp dedupe_sessions(sessions) do
    sessions
    |> Enum.reverse()
    |> Enum.uniq_by(& &1["session_id"])
    |> Enum.reverse()
  end

  defp public_connection(connection) do
    connection
    |> Map.drop(["connection_key"])
  end

  defp add_token(connection) do
    Map.put(connection, "token", Token.sign(%{"connection_id" => connection["connection_id"]}))
  end

  defp connection_error_status(:connection_not_found), do: 404
  defp connection_error_status(:connection_key_exists), do: 409
  defp connection_error_status(_reason), do: 400

  defp map_ok({:ok, value}, mapper), do: {:ok, mapper.(value)}
  defp map_ok(other, _mapper), do: other

  defp bounded(body) when is_binary(body) and byte_size(body) > 1_000,
    do: binary_part(body, 0, 1_000)

  defp bounded(body) when is_binary(body), do: body
  defp bounded(body), do: inspect(body)

  defp now do
    System.system_time(:second) |> DateTime.from_unix!() |> DateTime.to_iso8601()
  end
end

defmodule Bridge.Router do
  use Plug.Router

  plug :match
  plug :dispatch

  get "/health" do
    cluster_size = length(Node.list()) + 1
    active_servers = Bridge.ServerRegistry.count_servers()
    active_sessions = Bridge.SessionManager.count_sessions()

    health = %{
      status: "healthy",
      node: Node.self(),
      cluster_size: cluster_size,
      active_servers: active_servers,
      active_sessions: active_sessions
    }

    send_json(conn, 200, health)
  end

  match _ do
    send_resp(conn, 404, "Not found")
  end

  defp send_json(conn, status, data) do
    conn
    |> put_resp_content_type("application/json")
    |> send_resp(status, Jason.encode!(data))
  end
end

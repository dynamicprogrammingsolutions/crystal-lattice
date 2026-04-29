defmodule CloudOrchestrator.Proxy do
  import Plug.Conn

  def forward(conn, %{"proxy_base_url" => base_url}, path) do
    target_path =
      case conn.query_string do
        "" -> String.trim_leading(path, "/")
        query -> String.trim_leading(path, "/") <> "?" <> query
      end

    target = URI.merge(base_url <> "/", target_path) |> URI.to_string()

    headers =
      conn.req_headers
      |> Enum.reject(fn {name, _} -> name in ["host", "authorization", "content-length"] end)

    body = read_body!(conn)

    request = Finch.build(proxy_method(conn.method), target, headers, body)

    case Finch.request(request, CloudOrchestrator.Finch) do
      {:ok, response} ->
        conn =
          Enum.reduce(response.headers, conn, fn {name, value}, acc ->
            put_resp_header(acc, String.downcase(name), value)
          end)

        send_resp(conn, response.status, response.body)

      {:error, reason} ->
        conn
        |> put_resp_content_type("application/json")
        |> send_resp(502, Jason.encode!(%{error: "proxy_failed", detail: inspect(reason)}))
    end
  end

  def forward(conn, _instance, _path) do
    conn
    |> put_resp_content_type("application/json")
    |> send_resp(409, Jason.encode!(%{error: "instance_not_proxyable"}))
  end

  defp read_body!(conn) do
    case Plug.Conn.read_body(conn, length: 100_000_000, read_length: 1_000_000) do
      {:ok, "", _conn} -> encoded_body_params(conn)
      {:ok, body, _conn} -> body
      {:more, body, _conn} -> body
      {:error, _reason} -> encoded_body_params(conn)
    end
  end

  defp encoded_body_params(%{body_params: %Plug.Conn.Unfetched{}}), do: ""
  defp encoded_body_params(%{body_params: params}) when is_map(params), do: Jason.encode!(params)
  defp encoded_body_params(_conn), do: ""

  defp proxy_method(method) do
    method
    |> String.downcase()
    |> String.to_existing_atom()
  rescue
    _ -> :get
  end
end

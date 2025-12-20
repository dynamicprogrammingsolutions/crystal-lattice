defmodule Bridge.Socket do
  use Phoenix.Socket

  channel "server:*", Bridge.ServerChannel
  channel "app:*", Bridge.AppChannel

  @impl true
  def connect(%{"type" => "server"}, socket, _connect_info) do
    {:ok, assign(socket, :type, :server)}
  end

  def connect(%{"type" => "app"}, socket, _connect_info) do
    {:ok, assign(socket, :type, :app)}
  end

  def connect(_params, _socket, _connect_info) do
    :error
  end

  @impl true
  def id(socket), do: "#{socket.assigns.type}:#{socket.assigns[:client_id]}"
end

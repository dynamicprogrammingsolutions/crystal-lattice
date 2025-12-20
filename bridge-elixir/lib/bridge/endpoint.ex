defmodule Bridge.Endpoint do
  use Phoenix.Endpoint, otp_app: :bridge

  socket("/ws", Bridge.Socket,
    websocket: [
      timeout: 45_000,
      check_origin: false
    ],
    longpoll: false
  )

  plug(Plug.Logger)

  plug(Plug.Parsers,
    parsers: [:json],
    pass: ["*/*"],
    json_decoder: Jason
  )

  plug(Bridge.Router)
end

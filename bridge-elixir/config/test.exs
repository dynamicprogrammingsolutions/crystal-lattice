import Config

config :logger, level: :warning

config :bridge, Bridge.Endpoint,
  http: [port: 4002],
  server: true

config :libcluster,
  topologies: []

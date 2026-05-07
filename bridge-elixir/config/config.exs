import Config

config :bridge, Bridge.Endpoint,
  http: [port: String.to_integer(System.get_env("PORT") || "4000")],
  server: true,
  pubsub_server: Bridge.PubSub

config :phoenix, :json_library, Jason

config :logger, :console,
  format: "$time $metadata[$level] $message\n",
  metadata: [:node, :request_id]

cluster_strategy = System.get_env("BRIDGE_CLUSTER_STRATEGY") || "gossip"

cluster_topologies =
  case cluster_strategy do
    "none" ->
      []

    "dns_poll" ->
      [
        bridge: [
          strategy: Cluster.Strategy.DNSPoll,
          config: [
            polling_interval: String.to_integer(System.get_env("BRIDGE_CLUSTER_POLL_MS") || "5000"),
            query: System.get_env("BRIDGE_CLUSTER_DNS_NAME") || "bridge.local",
            node_basename: System.get_env("BRIDGE_CLUSTER_NODE_BASENAME") || "bridge"
          ]
        ]
      ]

    _ ->
      [
        bridge: [
          strategy: Cluster.Strategy.Gossip,
          config: [
            port: String.to_integer(System.get_env("GOSSIP_PORT") || "45892"),
            if_addr: {0, 0, 0, 0},
            multicast_addr: System.get_env("GOSSIP_MULTICAST_ADDR") || "230.1.1.251",
            multicast_ttl: 1
          ]
        ]
      ]
  end

config :libcluster,
  topologies: cluster_topologies

config :bridge,
  pairing_code_ttl: String.to_integer(System.get_env("PAIRING_CODE_TTL") || "300"),
  max_pairing_attempts: String.to_integer(System.get_env("MAX_PAIRING_ATTEMPTS") || "3"),
  session_timeout: String.to_integer(System.get_env("SESSION_TIMEOUT") || "3600"),
  pairing_token_secret:
    System.get_env("BRIDGE_TOKEN_SECRET") ||
      "crystal-lattice-local-dev-pairing-token-secret",
  pairing_token_salt: System.get_env("BRIDGE_TOKEN_SALT") || "pairing-token-v1",
  pairing_token_ttl_seconds:
    String.to_integer(System.get_env("BRIDGE_PAIRING_TOKEN_TTL_SECONDS") || "2592000")

import_config "#{config_env()}.exs"

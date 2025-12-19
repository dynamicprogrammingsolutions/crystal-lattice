import Config

if System.get_env("NODE_NAME") do
  config :kernel,
    inet_dist_listen_min: 9100,
    inet_dist_listen_max: 9155
end

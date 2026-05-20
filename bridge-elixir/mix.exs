defmodule Bridge.MixProject do
  use Mix.Project

  def project do
    [
      app: :bridge,
      version: "0.1.0",
      elixir: "~> 1.14",
      licenses: ["AGPL-3.0"],
      start_permanent: Mix.env() == :prod,
      deps: deps()
    ]
  end

  def application do
    [
      extra_applications: [:logger, :runtime_tools],
      mod: {Bridge.Application, []}
    ]
  end

  defp deps do
    [
      {:phoenix, "~> 1.7.0"},
      {:phoenix_pubsub, "~> 2.1"},
      {:plug_cowboy, "~> 2.6"},
      {:jason, "~> 1.4"},
      {:libcluster, "~> 3.3"},
      {:uuid, "~> 1.1"},
      {:websockex, "~> 0.4.3", only: :test}
    ]
  end
end

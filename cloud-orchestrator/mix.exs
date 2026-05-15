defmodule CloudOrchestrator.MixProject do
  use Mix.Project

  def project do
    [
      app: :cloud_orchestrator,
      version: "0.1.0",
      elixir: "~> 1.14",
      licenses: ["AGPL-3.0-only"],
      start_permanent: Mix.env() == :prod,
      deps: deps()
    ]
  end

  def application do
    [
      extra_applications: [:logger, :runtime_tools],
      mod: {CloudOrchestrator.Application, []}
    ]
  end

  defp deps do
    [
      {:phoenix, "~> 1.7.0"},
      {:plug_cowboy, "~> 2.6"},
      {:jason, "~> 1.4"},
      {:finch, "~> 0.19"},
      {:mint, "~> 1.6"},
      {:castore, "~> 1.0"}
    ]
  end
end

defmodule CloudOrchestrator.Token do
  @max_age_seconds 24 * 60 * 60

  def sign(claims) when is_map(claims) do
    payload =
      claims
      |> Map.put_new("iat", System.system_time(:second))
      |> Jason.encode!()
      |> Base.url_encode64(padding: false)

    signature = sign_payload(payload)
    payload <> "." <> signature
  end

  def verify(token) when is_binary(token) do
    with [payload, signature] <- String.split(token, ".", parts: 2),
         true <- Plug.Crypto.secure_compare(signature, sign_payload(payload)),
         {:ok, json} <- Base.url_decode64(payload, padding: false),
         {:ok, claims} <- Jason.decode(json),
         :ok <- verify_age(claims) do
      {:ok, claims}
    else
      _ -> {:error, :invalid_token}
    end
  end

  def verify(_), do: {:error, :invalid_token}

  defp verify_age(%{"iat" => iat}) when is_integer(iat) do
    if System.system_time(:second) - iat <= @max_age_seconds do
      :ok
    else
      {:error, :expired}
    end
  end

  defp verify_age(_claims), do: {:error, :invalid_token}

  defp sign_payload(payload) do
    :crypto.mac(:hmac, :sha256, secret(), payload)
    |> Base.url_encode64(padding: false)
  end

  defp secret do
    Application.fetch_env!(:cloud_orchestrator, :token_secret)
  end
end

# Application Config App

Provides application-level actions to request a complete application reload and
to update explicitly allowlisted provider keys in a configured dotenv file.

Stage 1 configuration:

```json
{
  "application": {
    "application_config": {
      "env_file": "${env:CONFIG_DIR}/.env",
      "editable_env_keys": ["OPENROUTER_API_KEY"],
      "provider_env_keys": {
        "openrouter": "OPENROUTER_API_KEY"
      }
    }
  }
}
```

Values already supplied through the process environment are externally managed
and cannot be changed by this plugin.
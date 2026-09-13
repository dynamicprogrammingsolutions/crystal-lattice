function usageText() {
  return [
    "Usage: node proxy.js <endpoint> <port> [base-path] [--hide-headers] [--require-api-key-env NAME] [--delay-ms N]",
    "Example (OpenAI-compatible): node proxy.js https://openrouter.ai/api/v1 3000 /api/v1 --hide-headers",
    "Example (Anthropic):         node proxy.js https://api.anthropic.com 3000 /v1 --hide-headers",
    "Example (Ollama reviewer):    CRYSTAL_PROXY_API_KEY=... node proxy.js http://127.0.0.1:11434/v1 3000 /v1 --hide-headers --require-api-key-env CRYSTAL_PROXY_API_KEY",
  ].join("\n");
}

function parseProxyArgs(argv) {
  const args = Array.isArray(argv) ? argv : [];
  const flags = new Set();
  const positional = [];
  let requireApiKeyEnv = null;
  let delayMs = 0;

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--help" || arg === "-h") {
      flags.add("help");
      continue;
    }
    if (arg === "--hide-headers") {
      flags.add("hide_headers");
      continue;
    }
    if (arg === "--require-api-key-env") {
      const value = args[index + 1];
      if (
        typeof value !== "string" ||
        !value.trim() ||
        value.startsWith("--")
      ) {
        throw new Error("--require-api-key-env requires an environment name");
      }
      requireApiKeyEnv = value.trim();
      index += 1;
      continue;
    }
    if (arg === "--delay-ms") {
      const value = args[index + 1];
      const parsed = Number.parseInt(String(value ?? ""), 10);
      if (!Number.isInteger(parsed) || parsed < 0 || parsed > 300000) {
        throw new Error("--delay-ms must be between 0 and 300000");
      }
      delayMs = parsed;
      index += 1;
      continue;
    }
    if (typeof arg === "string" && arg.startsWith("--")) {
      throw new Error(`Unknown flag: ${arg}`);
    }
    positional.push(arg);
  }

  if (flags.has("help")) {
    return { help: true };
  }
  if (positional.length < 2 || positional.length > 3) {
    throw new Error(usageText());
  }

  const endpoint = String(positional[0] || "");
  const port = Number.parseInt(String(positional[1] || ""), 10);
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    throw new Error("Port must be a valid number between 1 and 65535");
  }

  const basePath = String(positional[2] || "/api/v1").replace(/\/$/, "");
  if (!basePath.startsWith("/")) {
    throw new Error("Base path must start with '/'");
  }

  return {
    help: false,
    endpoint,
    port,
    basePath,
    hideHeaders: flags.has("hide_headers"),
    requireApiKeyEnv,
    delayMs,
  };
}

module.exports = {
  parseProxyArgs,
  usageText,
};

function usageText() {
  return [
    "Usage: node proxy.js <endpoint> <port> [base-path] [--hide-headers]",
    "Example (OpenAI-compatible): node proxy.js https://openrouter.ai/api/v1 3000 /api/v1 --hide-headers",
    "Example (Anthropic):         node proxy.js https://api.anthropic.com 3000 /v1 --hide-headers",
  ].join("\n");
}

function parseProxyArgs(argv) {
  const args = Array.isArray(argv) ? argv : [];
  const flags = new Set();
  const positional = [];

  for (const arg of args) {
    if (arg === "--help" || arg === "-h") {
      flags.add("help");
      continue;
    }
    if (arg === "--hide-headers") {
      flags.add("hide_headers");
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
  };
}

module.exports = {
  parseProxyArgs,
  usageText,
};
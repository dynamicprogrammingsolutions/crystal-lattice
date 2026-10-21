export function normalizeBridgeAddress(address: string): string {
  const value = address.trim();
  if (!value) throw new Error("Please enter a bridge address");
  const normalized = /^[a-z][a-z\d+.-]*:\/\//i.test(value)
    ? value
    : `https://${value}`;
  let parsed: URL;
  try {
    parsed = new URL(normalized);
  } catch {
    throw new Error(
      "Enter a domain or a valid HTTP, HTTPS, WS, or WSS bridge address"
    );
  }
  const bridgeUrl = parsed as unknown as {
    protocol: string;
    hostname: string;
  };
  if (!["http:", "https:", "ws:", "wss:"].includes(bridgeUrl.protocol)) {
    throw new Error("Bridge addresses support HTTP, HTTPS, WS, and WSS");
  }
  if (!bridgeUrl.hostname)
    throw new Error("Bridge address must include a host");
  return normalized;
}

export function deriveBridgeWebSocketUrl(address: string): string {
  const normalized = normalizeBridgeAddress(address);
  const parsed = new URL(normalized) as unknown as {
    protocol: string;
    pathname: string;
    hash: string;
    toString(): string;
  };
  if (parsed.protocol === "ws:" || parsed.protocol === "wss:") {
    if (parsed.pathname !== "/" && parsed.pathname !== "") return normalized;
  }
  parsed.protocol =
    parsed.protocol === "https:" || parsed.protocol === "wss:" ? "wss:" : "ws:";
  const path = parsed.pathname.replace(/\/+$/, "");
  if (path.endsWith("/ws")) {
    parsed.pathname = `${path}/websocket`;
  } else if (!path.endsWith("/ws/websocket")) {
    parsed.pathname = `${path}/ws/websocket`;
  }
  parsed.hash = "";
  return parsed.toString();
}

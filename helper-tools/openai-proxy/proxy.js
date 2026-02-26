const express = require("express");
const axios = require("axios");
const crypto = require("crypto");

// Parse command line arguments
const args = process.argv.slice(2);
if (args.length < 2) {
  console.log("Usage: node proxy.js <endpoint> <port> [base-path]");
  console.log("Example (OpenAI-compatible): node proxy.js https://openrouter.ai/api/v1 3000");
  console.log("Example (Anthropic):         node proxy.js https://api.anthropic.com 3000 /v1");
  process.exit(1);
}

const TARGET_ENDPOINT = args[0];
const PORT = parseInt(args[1]);
// Optional base path: defaults to /api/v1 (OpenAI-compatible style).
// For Anthropic pass /v1 so that Claude Code's requests to /v1/messages are forwarded correctly.
const BASE_PATH = (args[2] || "/api/v1").replace(/\/$/, "");

// Validate arguments
if (isNaN(PORT) || PORT < 1 || PORT > 65535) {
  console.error("Error: Port must be a valid number between 1 and 65535");
  process.exit(1);
}

// Remove trailing slash from endpoint if present
const cleanEndpoint = TARGET_ENDPOINT.replace(/\/$/, "");


// Global long-text registry persisted across all requests.
// Maps sha256 hash -> { number, path (first seen), length }
const longTextRegistry = new Map();
let longTextCounter = 0;

function hashText(str) {
  return crypto.createHash("sha256").update(str).digest("hex");
}

// Returns the zero-padded placeholder number for the given text,
// registering it in the global registry if it hasn't been seen before.
// Also pushes to `newTexts` when the text is genuinely new.
function getOrRegisterLongText(str, path, newTexts) {
  const hash = hashText(str);
  if (longTextRegistry.has(hash)) {
    return longTextRegistry.get(hash).number;
  }
  longTextCounter++;
  const num = String(longTextCounter).padStart(3, "0");
  longTextRegistry.set(hash, { number: num, path, length: str.length });
  newTexts.push({ number: num, path, content: str, length: str.length });
  return num;
}

const app = express();

// Middleware to parse JSON and handle raw data
app.use(express.json({ limit: "10mb" }));
app.use(express.text({ limit: "10mb" }));
app.use(express.urlencoded({ extended: true, limit: "10mb" }));

// Function to find and extract long text fields with numbering
function extractLongTexts(
  obj,
  path = "",
  newTexts = []
) {
  if (typeof obj === "string" && obj.length > 1000) {
    const num = getOrRegisterLongText(obj, path, newTexts);
    return `[LONG_TEXT_${num}]`;
  } else if (Array.isArray(obj)) {
    return obj.map((item, index) =>
      extractLongTexts(item, `${path}[${index}]`, newTexts)
    );
  } else if (obj && typeof obj === "object") {
    const result = {};
    for (const [key, value] of Object.entries(obj)) {
      const newPath = path ? `${path}.${key}` : key;
      result[key] = extractLongTexts(value, newPath, newTexts);
    }
    return result;
  }
  return obj;
}

// Shared helper: pretty-print a body object, extracting long texts
function logBody(label, data) {
  const newTexts = [];
  const truncated = extractLongTexts(data, "", newTexts);
  console.log(`${label}:`, JSON.stringify(truncated, null, 2));
  if (newTexts.length > 0) {
    console.log("\n--- New Long Text Fields ---");
    newTexts.forEach(({ number, path, content, length }) => {
      console.log(`LONG_TEXT_${number} - ${path} (${length} chars):`);
      console.log("---");
      console.log(content);
      console.log("---\n");
    });
  }
}

// Function to log request with numbered long text extraction
function logRequest(req) {
  console.log("\n=== Incoming Request ===");
  console.log("Method:", req.method);
  console.log("Original URL:", req.originalUrl);
  console.log("Query:", req.query);
  console.log("Headers:", JSON.stringify(req.headers, null, 2));

  // Only log body for methods that typically have bodies
  if (["POST", "PUT", "PATCH"].includes(req.method) && req.body) {
    logBody("Body", req.body);
  }
  console.log("========================\n");
}

// Function to log response
function logResponse(status, data) {
  console.log("\n=== Response ===");
  console.log("Status:", status);
  if (data !== undefined && data !== null && data !== "") {
    logBody("Body", data);
  }
  console.log("================\n");
}

// Health check endpoint (before the wildcard)
app.get("/health", (req, res) => {
  res.json({
    status: "ok",
    target: cleanEndpoint,
    port: PORT,
    base_path: BASE_PATH,
    proxy_pattern: `${BASE_PATH}/*`,
  });
});

// Shared proxy handler — used for both OpenAI-compatible and Anthropic base paths
async function proxyHandler(req, res) {
  try {
    // Get the path after BASE_PATH
    const apiPath = req.path === "/" ? "" : req.path;

    // Log the incoming request
    logRequest(req);

    // Prepare headers for forwarding
    const forwardHeaders = { ...req.headers };
    delete forwardHeaders.host;
    delete forwardHeaders.connection;
    delete forwardHeaders["content-length"];

    // Build target URL: cleanEndpoint already contains the full base (e.g.
    // "https://api.anthropic.com" for Anthropic, or
    // "https://openrouter.ai/api/v1" for OpenAI-compatible).
    // We append BASE_PATH only when it isn't already part of cleanEndpoint.
    const targetUrl = cleanEndpoint.endsWith(BASE_PATH)
      ? `${cleanEndpoint}${apiPath}`
      : `${cleanEndpoint}${BASE_PATH}${apiPath}`;

    console.log(`Forwarding ${req.method} request to: ${targetUrl}`);

    const isStreaming =
      req.body?.stream === true || req.body?.stream === "true";

    // Prepare axios config
    const axiosConfig = {
      method: req.method.toLowerCase(),
      url: targetUrl,
      headers: forwardHeaders,
      params: req.query, // Forward query parameters
      validateStatus: () => true, // Don't throw on any status code
      // Use a stream response type so we can pipe SSE / chunked responses
      responseType: isStreaming ? "stream" : "json",
    };

    // Add body for methods that support it
    if (["post", "put", "patch"].includes(req.method.toLowerCase())) {
      axiosConfig.data = req.body;
    }

    const response = await axios(axiosConfig);

    // Forward response headers
    const responseHeaders = { ...response.headers };
    delete responseHeaders["transfer-encoding"];
    delete responseHeaders.connection;
    delete responseHeaders["content-encoding"];

    // Set response headers and status
    Object.keys(responseHeaders).forEach((key) => {
      res.set(key, responseHeaders[key]);
    });

    res.status(response.status);

    if (isStreaming) {
      // Pipe the SSE stream directly to the client, logging each chunk
      console.log("Streaming response — piping chunks:");
      response.data.on("data", (chunk) => {
        const text = chunk.toString();
        console.log("[chunk]", text);
        res.write(chunk);
      });
      response.data.on("end", () => {
        console.log("[stream end]");
        res.end();
      });
      response.data.on("error", (err) => {
        console.error("[stream error]", err.message);
        res.end();
      });
    } else {
      // Non-streaming: log full response then send
      logResponse(response.status, response.data);

      if (response.headers["content-type"]?.includes("application/json")) {
        res.json(response.data);
      } else {
        res.send(response.data);
      }
    }

    console.log(`Response status: ${response.status}`);
  } catch (error) {
    console.error("Proxy error:", error.message);

    if (error.code === "ECONNREFUSED") {
      res.status(502).json({
        error: "Bad Gateway",
        message: "Unable to connect to target endpoint",
      });
    } else if (error.code === "ENOTFOUND") {
      res.status(502).json({
        error: "Bad Gateway",
        message: "Target endpoint not found",
      });
    } else if (error.response) {
      // Forward the error response from the target
      res.status(error.response.status).json(error.response.data);
    } else {
      res.status(500).json({
        error: "Internal Server Error",
        message: "Proxy encountered an error",
        details: error.message,
      });
    }
  }
}

// Register the single handler under the configured base path
app.use(BASE_PATH, proxyHandler);

// Handle 404s for other routes
app.use((req, res) => {
  res.status(404).json({
    error: "Not Found",
    message: `This proxy only supports paths under ${BASE_PATH}/`,
    available_endpoints: [`ALL ${BASE_PATH}/*`, "GET /health"],
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`Proxy Server running on port ${PORT}`);
  console.log(`Target endpoint: ${cleanEndpoint}`);
  console.log(`Base path:       ${BASE_PATH}`);
  console.log(`Proxy pattern:   http://localhost:${PORT}${BASE_PATH}/*`);
  console.log(`Health check:    http://localhost:${PORT}/health`);
  console.log("\nExample endpoints:");
  if (BASE_PATH === "/v1") {
    console.log(`  - POST   ${BASE_PATH}/messages          (Anthropic)`);
    console.log(`  - GET    ${BASE_PATH}/models             (Anthropic)`);
  } else {
    console.log(`  - POST   ${BASE_PATH}/chat/completions   (OpenAI-compatible)`);
    console.log(`  - GET    ${BASE_PATH}/models              (OpenAI-compatible)`);
    console.log(`  - POST   ${BASE_PATH}/embeddings`);
    console.log(`  - POST   ${BASE_PATH}/completions`);
  }
  console.log(`  - And any other ${BASE_PATH}/* endpoint`);
  console.log(
    "\nLong text detection: Enabled (>1000 characters, numbered for easy search)"
  );
  console.log("Streaming support: Enabled (SSE chunks are piped and logged)");
  console.log("\nWaiting for requests...\n");
});

// Handle graceful shutdown
process.on("SIGINT", () => {
  console.log("\nShutting down proxy server...");
  process.exit(0);
});

process.on("uncaughtException", (error) => {
  console.error("Uncaught Exception:", error);
  process.exit(1);
});

process.on("unhandledRejection", (reason, promise) => {
  console.error("Unhandled Rejection at:", promise, "reason:", reason);
  process.exit(1);
});

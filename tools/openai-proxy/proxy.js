const express = require("express");
const axios = require("axios");
const crypto = require("crypto");
const { parseProxyArgs, usageText } = require("./proxy_args");
const { loadProxyConfiguration } = require("./proxy_config");
const {
  BudgetLedger,
  SseUsageCollector,
  usageFromPayload,
} = require("./rate_limit");

// Parse command line arguments
let parsedArgs;
try {
  parsedArgs = parseProxyArgs(process.argv.slice(2));
} catch (error) {
  if (error.message.startsWith("Usage:")) {
    console.error(error.message);
  } else {
    console.error(`Error: ${error.message}`);
    console.error(usageText());
  }
  process.exit(1);
}
if (parsedArgs.help) {
  console.log(usageText());
  process.exit(0);
}

let configuration;
try {
  configuration = loadProxyConfiguration(parsedArgs);
} catch (error) {
  console.error(`Error: ${error.message}`);
  process.exit(1);
}

const cleanEndpoint = configuration.endpoint;
const HOST = configuration.host;
const PORT = configuration.port;
const BASE_PATH = configuration.basePath;
const HIDE_HEADERS = configuration.hideHeaders;
const LOG_BODIES = configuration.logBodies;
const LONG_TEXT_THRESHOLD = configuration.longTextThreshold;
const REQUIRED_API_KEY_ENV = configuration.incomingApiKeyEnv;
const REQUIRED_API_KEY = configuration.incomingApiKey;
const UPSTREAM_API_KEY = configuration.upstreamApiKey;
const RESPONSE_DELAY_MS = configuration.delayMs;
const ALLOWED_MODELS = new Set(configuration.allowedModels);
const ALLOWED_SERVICE_TIERS = new Set(configuration.allowedServiceTiers);
const REQUEST_OVERRIDES = configuration.requestOverrides;
const budgetLedger = new BudgetLedger(configuration.budget);

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
function extractLongTexts(obj, path = "", newTexts = []) {
  if (typeof obj === "string" && obj.length > LONG_TEXT_THRESHOLD) {
    const num = getOrRegisterLongText(obj, path, newTexts);
    return `[LONG_TEXT_${num}]`;
  } else if (Array.isArray(obj)) {
    return obj.map((item, index) =>
      extractLongTexts(item, `${path}[${index}]`, newTexts),
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
  if (HIDE_HEADERS) {
    console.log("Headers: [hidden]");
  } else {
    const loggedHeaders = { ...req.headers };
    if (REQUIRED_API_KEY) {
      if (loggedHeaders.authorization) {
        loggedHeaders.authorization = "[redacted]";
      }
      if (loggedHeaders["x-api-key"]) {
        loggedHeaders["x-api-key"] = "[redacted]";
      }
    }
    console.log("Headers:", JSON.stringify(loggedHeaders, null, 2));
  }

  // Only log body for methods that typically have bodies
  if (
    LOG_BODIES &&
    ["POST", "PUT", "PATCH"].includes(req.method) &&
    req.body
  ) {
    logBody("Body", req.body);
  }
  console.log("========================\n");
}

// Function to log response
function logResponse(status, data) {
  console.log("\n=== Response ===");
  console.log("Status:", status);
  if (LOG_BODIES && data !== undefined && data !== null && data !== "") {
    logBody("Body", data);
  }
  console.log("================\n");
}

// Health check endpoint (before the wildcard)
app.get("/health", (req, res) => {
  const budget = budgetLedger.status();
  res.json({
    status: "ok",
    configured: Boolean(configuration.configPath),
    port: PORT,
    host: HOST,
    base_path: BASE_PATH,
    proxy_pattern: `${BASE_PATH}/*`,
    authentication: REQUIRED_API_KEY ? "bearer" : "none",
    response_delay_ms: RESPONSE_DELAY_MS,
    allowed_models: [...ALLOWED_MODELS],
    budget: configuration.budget
      ? {
          limit_usd: configuration.budget.limitUsd,
          spent_usd: budget.spentUsd,
          blocked: budget.blocked,
          blocked_until: budget.blockedUntil,
          retry_after_seconds: budget.retryAfterSeconds,
        }
      : null,
  });
});

function bearerToken(req) {
  const authorization = req.headers.authorization;
  if (typeof authorization !== "string") {
    return null;
  }
  const match = authorization.match(/^Bearer\s+(.+)$/i);
  return match ? match[1] : null;
}

function matchesRequiredApiKey(req) {
  if (!REQUIRED_API_KEY) {
    return true;
  }
  const supplied = bearerToken(req);
  if (typeof supplied !== "string") {
    return false;
  }
  const expectedBuffer = Buffer.from(REQUIRED_API_KEY);
  const suppliedBuffer = Buffer.from(supplied);
  return (
    expectedBuffer.length === suppliedBuffer.length &&
    crypto.timingSafeEqual(expectedBuffer, suppliedBuffer)
  );
}

async function delayResponse() {
  if (RESPONSE_DELAY_MS <= 0) {
    return;
  }
  await new Promise((resolve) => setTimeout(resolve, RESPONSE_DELAY_MS));
}

function modelRequestPath(pathname) {
  return pathname === "/responses" || pathname === "/chat/completions";
}

function budgetControlledPath(pathname) {
  return pathname === "/models" || modelRequestPath(pathname);
}

function applyRequestOverrides(pathname, body) {
  if (!body || typeof body !== "object" || Array.isArray(body)) {
    return body;
  }
  const endpoint = pathname.replace(/^\/+/, "").replaceAll("/", "_");
  const overrides = REQUEST_OVERRIDES[endpoint];
  return overrides ? { ...body, ...overrides } : body;
}

function validateRequestConfiguration(req, res) {
  if (modelRequestPath(req.path) && ALLOWED_MODELS.size > 0) {
    const model = req.body?.model;
    if (typeof model !== "string" || !ALLOWED_MODELS.has(model)) {
      res.status(configuration.invalidModelStatus).json({
        error: "Model not allowed",
        allowed_models: [...ALLOWED_MODELS],
      });
      return false;
    }
  }
  if (modelRequestPath(req.path) && ALLOWED_SERVICE_TIERS.size > 0) {
    const tier = req.body?.service_tier;
    if (
      typeof tier === "string" &&
      tier &&
      !ALLOWED_SERVICE_TIERS.has(tier)
    ) {
      res.status(configuration.invalidModelStatus).json({
        error: "Service tier not allowed",
        allowed_service_tiers: [...ALLOWED_SERVICE_TIERS],
      });
      return false;
    }
  }
  return true;
}

function filterModelResponse(pathname, data) {
  if (pathname !== "/models" || ALLOWED_MODELS.size === 0) {
    return data;
  }
  if (!data || typeof data !== "object") {
    return data;
  }
  if (Array.isArray(data.data)) {
    return {
      ...data,
      data: data.data.filter(
        (model) =>
          model &&
          typeof model === "object" &&
          ALLOWED_MODELS.has(model.id),
      ),
    };
  }
  if (Array.isArray(data.models)) {
    return {
      ...data,
      models: data.models.filter((model) => {
        const modelId =
          typeof model === "string"
            ? model
            : model && typeof model === "object"
              ? model.id ?? model.name
              : null;
        return typeof modelId === "string" && ALLOWED_MODELS.has(modelId);
      }),
    };
  }
  return data;
}

function blockedResponse(res) {
  const budget = budgetLedger.status();
  if (!budget.blocked) return false;
  res.set("Retry-After", String(budget.retryAfterSeconds));
  res.status(configuration.blockedStatus).json({
    error: "Budget cooldown active",
    blocked_until: budget.blockedUntil,
    retry_after_seconds: budget.retryAfterSeconds,
  });
  return true;
}

function chargeUsage(usage) {
  if (!usage || !configuration.budget) return;
  const cost = budgetLedger.charge(usage);
  console.log(
    `Recorded usage cost: $${cost.toFixed(8)}; total: $${budgetLedger
      .status()
      .spentUsd.toFixed(8)}`,
  );
}

// Shared proxy handler — used for both OpenAI-compatible and Anthropic base paths
async function proxyHandler(req, res) {
  let releaseBudget = () => {};
  try {
    if (!matchesRequiredApiKey(req)) {
      res.status(configuration.unauthorizedStatus).json({
        error: "Unauthorized",
        message: "A valid bearer API key is required",
      });
      return;
    }
    req.body = applyRequestOverrides(req.path, req.body);
    if (!validateRequestConfiguration(req, res)) {
      return;
    }
    if (budgetControlledPath(req.path)) {
      releaseBudget = await budgetLedger.acquire();
      if (blockedResponse(res)) {
        return;
      }
    }

    // Get the path after BASE_PATH
    const apiPath = req.path === "/" ? "" : req.path;

    // Log the incoming request
    logRequest(req);

    // Prepare headers for forwarding
    const forwardHeaders = { ...req.headers };
    delete forwardHeaders.host;
    delete forwardHeaders.connection;
    delete forwardHeaders["content-length"];
    if (REQUIRED_API_KEY) {
      delete forwardHeaders.authorization;
      delete forwardHeaders["x-api-key"];
    }
    if (UPSTREAM_API_KEY) {
      forwardHeaders.authorization = `Bearer ${UPSTREAM_API_KEY}`;
    }

    // Build target URL: cleanEndpoint already contains the full base (e.g.
    // "https://api.anthropic.com" for Anthropic, or
    // "https://openrouter.ai/api/v1" for OpenAI-compatible).
    // We append BASE_PATH only when it isn't already part of cleanEndpoint.
    const targetUrl = cleanEndpoint.endsWith(BASE_PATH)
      ? `${cleanEndpoint}${apiPath}`
      : `${cleanEndpoint}${BASE_PATH}${apiPath}`;

    console.log(`Forwarding ${req.method} request to: ${targetUrl}`);

    await delayResponse();

    const isStreaming =
      req.body?.stream === true || req.body?.stream === "true";
    if (
      isStreaming &&
      configuration.budget?.ensureStreamUsage &&
      req.path === "/chat/completions" &&
      req.body &&
      typeof req.body === "object"
    ) {
      req.body = {
        ...req.body,
        stream_options: {
          ...(req.body.stream_options ?? {}),
          include_usage: true,
        },
      };
    }

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
      const usageCollector = new SseUsageCollector();
      console.log("Streaming response — piping chunks:");
      await new Promise((resolve, reject) => {
        response.data.on("data", (chunk) => {
          usageCollector.push(chunk);
          if (LOG_BODIES) {
            console.log("[chunk]", chunk.toString());
          }
          res.write(chunk);
        });
        response.data.on("end", () => {
          console.log("[stream end]");
          res.end();
          resolve();
        });
        response.data.on("error", (error) => {
          console.error("[stream error]", error.message);
          res.end();
          reject(error);
        });
      });
      chargeUsage(usageCollector.finish());
    } else {
      const responseData = filterModelResponse(req.path, response.data);
      logResponse(response.status, responseData);
      if (response.status >= 200 && response.status < 300) {
        chargeUsage(usageFromPayload(responseData));
      }

      if (response.headers["content-type"]?.includes("application/json")) {
        res.json(responseData);
      } else {
        res.send(responseData);
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
  } finally {
    releaseBudget();
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
app.listen(PORT, HOST, () => {
  console.log(`Proxy Server running on ${HOST}:${PORT}`);
  console.log(`Target endpoint: ${cleanEndpoint}`);
  console.log(`Base path:       ${BASE_PATH}`);
  console.log(`Header logging:  ${HIDE_HEADERS ? "hidden" : "enabled"}`);
  console.log(
    `Authentication:  ${REQUIRED_API_KEY ? `bearer via ${REQUIRED_API_KEY_ENV}` : "none"}`,
  );
  console.log(
    `Upstream auth:   ${UPSTREAM_API_KEY ? `bearer via ${configuration.upstreamApiKeyEnv}` : "forwarded"}`,
  );
  console.log(
    `Allowed models:  ${ALLOWED_MODELS.size > 0 ? [...ALLOWED_MODELS].join(", ") : "unrestricted"}`,
  );
  console.log(
    `Budget:          ${configuration.budget ? `$${configuration.budget.limitUsd} / ${configuration.budget.cooldownSeconds}s` : "disabled"}`,
  );
  console.log(`Response delay:  ${RESPONSE_DELAY_MS} ms`);
  console.log(`Proxy pattern:   http://localhost:${PORT}${BASE_PATH}/*`);
  console.log(`Health check:    http://localhost:${PORT}/health`);
  console.log("\nExample endpoints:");
  if (BASE_PATH === "/v1") {
    console.log(`  - POST   ${BASE_PATH}/messages          (Anthropic)`);
    console.log(`  - GET    ${BASE_PATH}/models             (Anthropic)`);
  } else {
    console.log(
      `  - POST   ${BASE_PATH}/chat/completions   (OpenAI-compatible)`,
    );
    console.log(
      `  - GET    ${BASE_PATH}/models              (OpenAI-compatible)`,
    );
    console.log(`  - POST   ${BASE_PATH}/embeddings`);
    console.log(`  - POST   ${BASE_PATH}/completions`);
  }
  console.log(`  - And any other ${BASE_PATH}/* endpoint`);
  console.log(
    "\nLong text detection: Enabled (>1000 characters, numbered for easy search)",
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

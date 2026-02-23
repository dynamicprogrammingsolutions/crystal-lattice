const express = require("express");
const axios = require("axios");

// Parse command line arguments
const args = process.argv.slice(2);
if (args.length < 2) {
  console.log("Usage: node proxy.js <endpoint> <port>");
  console.log("Example: node proxy.js https://openrouter.ai/api/v1 3000");
  process.exit(1);
}

const TARGET_ENDPOINT = args[0];
const PORT = parseInt(args[1]);

// Validate arguments
if (isNaN(PORT) || PORT < 1 || PORT > 65535) {
  console.error("Error: Port must be a valid number between 1 and 65535");
  process.exit(1);
}

// Remove trailing slash from endpoint if present
const cleanEndpoint = TARGET_ENDPOINT.replace(/\/$/, "");

const app = express();

// Middleware to parse JSON and handle raw data
app.use(express.json({ limit: "10mb" }));
app.use(express.text({ limit: "10mb" }));
app.use(express.urlencoded({ extended: true, limit: "10mb" }));

// Function to find and extract long text fields with numbering
function extractLongTexts(
  obj,
  path = "",
  longTexts = [],
  counter = { value: 0 }
) {
  if (typeof obj === "string" && obj.length > 1000) {
    counter.value++;
    const textNumber = counter.value;
    longTexts.push({
      number: textNumber,
      path,
      content: obj,
      length: obj.length,
    });
    return `[LONG_TEXT_${textNumber}]`;
  } else if (Array.isArray(obj)) {
    return obj.map((item, index) =>
      extractLongTexts(item, `${path}[${index}]`, longTexts, counter)
    );
  } else if (obj && typeof obj === "object") {
    const result = {};
    for (const [key, value] of Object.entries(obj)) {
      const newPath = path ? `${path}.${key}` : key;
      result[key] = extractLongTexts(value, newPath, longTexts, counter);
    }
    return result;
  }
  return obj;
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
    const longTexts = [];
    const counter = { value: 0 };
    const truncatedBody = extractLongTexts(req.body, "", longTexts, counter);

    console.log("Body:", JSON.stringify(truncatedBody, null, 2));

    // Output long texts separately with numbers
    if (longTexts.length > 0) {
      console.log("\n--- Long Text Fields ---");
      longTexts.forEach(({ number, path, content, length }) => {
        console.log(`LONG_TEXT_${number} - ${path} (${length} chars):`);
        console.log("---");
        console.log(content);
        console.log("---\n");
      });
    }
  }
  console.log("========================\n");
}

// Health check endpoint (before the wildcard)
app.get("/health", (req, res) => {
  res.json({
    status: "ok",
    target: cleanEndpoint,
    port: PORT,
    proxy_pattern: "/api/v1/*",
  });
});

// Middleware to handle all /api/v1 routes
app.use("/api/v1", async (req, res) => {
  try {
    // Get the path after /api/v1
    const apiPath = req.path === "/" ? "" : req.path;

    // Log the incoming request with numbered long text extraction
    logRequest(req);

    // Prepare headers for forwarding
    const forwardHeaders = { ...req.headers };
    delete forwardHeaders.host;
    delete forwardHeaders.connection;
    delete forwardHeaders["content-length"];

    // Build target URL
    const targetUrl = `${cleanEndpoint}${apiPath}`;

    console.log(`Forwarding ${req.method} request to: ${targetUrl}`);

    // Prepare axios config
    const axiosConfig = {
      method: req.method.toLowerCase(),
      url: targetUrl,
      headers: forwardHeaders,
      params: req.query, // Forward query parameters
      validateStatus: () => true, // Don't throw on any status code
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

    // Send response based on content type
    if (response.headers["content-type"]?.includes("application/json")) {
      res.json(response.data);
    } else {
      res.send(response.data);
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
});

// Handle 404s for other routes
app.use((req, res) => {
  res.status(404).json({
    error: "Not Found",
    message: "This proxy only supports paths under /api/v1/",
    available_endpoints: ["ALL /api/v1/*", "GET /health"],
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`OpenAI Proxy Server running on port ${PORT}`);
  console.log(`Target endpoint: ${cleanEndpoint}`);
  console.log(`Proxy pattern: http://localhost:${PORT}/api/v1/*`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log("\nSupported endpoints:");
  console.log(`  - POST   /api/v1/chat/completions`);
  console.log(`  - GET    /api/v1/models`);
  console.log(`  - POST   /api/v1/embeddings`);
  console.log(`  - POST   /api/v1/completions`);
  console.log(`  - And any other /api/v1/* endpoint`);
  console.log(
    "\nLong text detection: Enabled (>1000 characters, numbered for easy search)"
  );
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

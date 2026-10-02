const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");

const { loadProxyConfiguration } = require("../proxy_config");

test("loads configured values and secrets from named environment variables", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "openai-proxy-config-"));
  const configPath = path.join(root, "reviewer.json");
  fs.writeFileSync(
    configPath,
    JSON.stringify({
      listen: { host: "127.0.0.2", port: 4321 },
      upstream: {
        base_url: "https://api.example.test/v1/",
        api_key_env: "UPSTREAM_TEST_KEY",
      },
      routing: {
        base_path: "/review/v1/",
        allowed_endpoints: ["models", "/responses"],
      },
      client_auth: { api_key_env: "CLIENT_TEST_KEY" },
      models: {
        allowed: ["model-a"],
        allowed_service_tiers: ["standard"],
      },
      forwarding: { delay_ms: 17 },
      logging: {
        headers: true,
        bodies: true,
        long_text_threshold: 321,
      },
      budget: {
        limit_usd: 2.5,
        cooldown_seconds: 123,
        state_path: "./state/ledger.json",
        serialize_requests: false,
        ensure_stream_usage: false,
        pricing_per_million: {
          input: 0.2,
          cached_input: 0.02,
          output: 1.2,
        },
        long_context: {
          input_token_threshold: 272000,
          input_multiplier: 2,
          cached_input_multiplier: 2,
          output_multiplier: 1.5,
        },
        ignored_charges: ["web_search"],
      },
      responses: {
        blocked_status: 430,
        unauthorized_status: 431,
        invalid_model_status: 432,
        unsupported_endpoint_status: 433,
      },
    }),
  );

  const config = loadProxyConfiguration(
    { help: false, configPath },
    {
      UPSTREAM_TEST_KEY: "upstream-secret",
      CLIENT_TEST_KEY: "client-secret",
    },
  );

  assert.equal(config.endpoint, "https://api.example.test/v1");
  assert.equal(config.host, "127.0.0.2");
  assert.equal(config.port, 4321);
  assert.equal(config.basePath, "/review/v1");
  assert.deepEqual(config.allowedEndpoints, ["/models", "/responses"]);
  assert.equal(config.hideHeaders, false);
  assert.equal(config.logBodies, true);
  assert.equal(config.longTextThreshold, 321);
  assert.equal(config.delayMs, 17);
  assert.equal(config.incomingApiKey, "client-secret");
  assert.equal(config.upstreamApiKey, "upstream-secret");
  assert.deepEqual(config.allowedModels, ["model-a"]);
  assert.deepEqual(config.allowedServiceTiers, ["standard"]);
  assert.equal(
    config.budget.statePath,
    path.join(root, "state", "ledger.json"),
  );
  assert.equal(config.budget.serializeRequests, false);
  assert.equal(config.budget.ensureStreamUsage, false);
  assert.equal(config.blockedStatus, 430);
  assert.equal(config.unauthorizedStatus, 431);
  assert.equal(config.invalidModelStatus, 432);
  assert.equal(config.unsupportedEndpointStatus, 433);
});

test("configured secrets must be supplied through named environment variables", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "openai-proxy-config-"));
  const configPath = path.join(root, "reviewer.json");
  fs.writeFileSync(
    configPath,
    JSON.stringify({
      listen: { port: 4321 },
      upstream: {
        base_url: "https://api.example.test/v1",
        api_key_env: "MISSING_UPSTREAM_KEY",
      },
    }),
  );

  assert.throws(
    () => loadProxyConfiguration({ help: false, configPath }, {}),
    /upstream API key environment variable MISSING_UPSTREAM_KEY is not set/,
  );
});
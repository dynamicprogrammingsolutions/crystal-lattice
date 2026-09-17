const fs = require("node:fs");
const path = require("node:path");

function objectValue(value, label) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`${label} must be an object`);
  }
  return value;
}

function stringValue(value, label, { required = true } = {}) {
  if (value === undefined || value === null) {
    if (!required) return null;
    throw new Error(`${label} is required`);
  }
  if (typeof value !== "string" || !value.trim()) {
    throw new Error(`${label} must be a non-empty string`);
  }
  return value.trim();
}

function numberValue(value, label, { minimum, maximum } = {}) {
  const parsed = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(parsed)) {
    throw new Error(`${label} must be numeric`);
  }
  if (minimum !== undefined && parsed < minimum) {
    throw new Error(`${label} must be at least ${minimum}`);
  }
  if (maximum !== undefined && parsed > maximum) {
    throw new Error(`${label} must be at most ${maximum}`);
  }
  return parsed;
}

function booleanValue(value, fallback) {
  return typeof value === "boolean" ? value : fallback;
}

function normalizeBasePath(value) {
  const basePath = stringValue(value ?? "/api/v1", "routing.base_path");
  if (!basePath.startsWith("/")) {
    throw new Error("routing.base_path must start with '/'");
  }
  return basePath === "/" ? "" : basePath.replace(/\/+$/, "");
}

function optionalEnvironmentValue(env, name, label) {
  if (!name) return null;
  const value = env[name];
  if (typeof value !== "string" || !value) {
    throw new Error(`${label} environment variable ${name} is not set`);
  }
  return value;
}

function normalizePricing(raw) {
  const pricing = objectValue(raw, "budget.pricing_per_million");
  return {
    input: numberValue(pricing.input, "budget.pricing_per_million.input", {
      minimum: 0,
    }),
    cachedInput: numberValue(
      pricing.cached_input,
      "budget.pricing_per_million.cached_input",
      { minimum: 0 },
    ),
    output: numberValue(pricing.output, "budget.pricing_per_million.output", {
      minimum: 0,
    }),
  };
}

function normalizeLongContext(raw) {
  if (raw === undefined || raw === null) return null;
  const value = objectValue(raw, "budget.long_context");
  return {
    inputTokenThreshold: numberValue(
      value.input_token_threshold,
      "budget.long_context.input_token_threshold",
      { minimum: 0 },
    ),
    inputMultiplier: numberValue(
      value.input_multiplier,
      "budget.long_context.input_multiplier",
      { minimum: 0 },
    ),
    cachedInputMultiplier: numberValue(
      value.cached_input_multiplier,
      "budget.long_context.cached_input_multiplier",
      { minimum: 0 },
    ),
    outputMultiplier: numberValue(
      value.output_multiplier,
      "budget.long_context.output_multiplier",
      { minimum: 0 },
    ),
  };
}

function normalizeBudget(raw, configDirectory) {
  if (raw === undefined || raw === null) return null;
  const value = objectValue(raw, "budget");
  if (booleanValue(value.enabled, true) === false) return null;
  const configuredStatePath = stringValue(
    value.state_path,
    "budget.state_path",
  );
  return {
    limitUsd: numberValue(value.limit_usd, "budget.limit_usd", {
      minimum: 0,
    }),
    cooldownSeconds: numberValue(
      value.cooldown_seconds,
      "budget.cooldown_seconds",
      { minimum: 1 },
    ),
    statePath: path.isAbsolute(configuredStatePath)
      ? configuredStatePath
      : path.resolve(configDirectory, configuredStatePath),
    pricing: normalizePricing(value.pricing_per_million),
    longContext: normalizeLongContext(value.long_context),
    ignoreWebSearch: Array.isArray(value.ignored_charges)
      ? value.ignored_charges.includes("web_search")
      : true,
    serializeRequests: booleanValue(value.serialize_requests, true),
    ensureStreamUsage: booleanValue(value.ensure_stream_usage, true),
  };
}

function normalizeRequestOverrides(raw) {
  if (raw === undefined || raw === null) return {};
  const configured = objectValue(raw, "models.request_overrides");
  return Object.fromEntries(
    Object.entries(configured).map(([endpoint, value]) => [
      stringValue(endpoint, "models.request_overrides endpoint"),
      { ...objectValue(value, `models.request_overrides.${endpoint}`) },
    ]),
  );
}

function normalizeConfiguredProxy(raw, configPath, env) {
  const config = objectValue(raw, "configuration");
  const listen = objectValue(config.listen ?? {}, "listen");
  const upstream = objectValue(config.upstream, "upstream");
  const routing = objectValue(config.routing ?? {}, "routing");
  const clientAuth = objectValue(config.client_auth ?? {}, "client_auth");
  const models = objectValue(config.models ?? {}, "models");
  const logging = objectValue(config.logging ?? {}, "logging");
  const forwarding = objectValue(config.forwarding ?? {}, "forwarding");
  const responses = objectValue(config.responses ?? {}, "responses");
  const allowedModels = Array.isArray(models.allowed)
    ? models.allowed.map((item, index) =>
        stringValue(item, `models.allowed[${index}]`),
      )
    : [];
  const allowedServiceTiers = Array.isArray(models.allowed_service_tiers)
    ? models.allowed_service_tiers.map((item, index) =>
        stringValue(item, `models.allowed_service_tiers[${index}]`),
      )
    : [];
  const incomingApiKeyEnv = stringValue(
    clientAuth.api_key_env,
    "client_auth.api_key_env",
    { required: false },
  );
  const upstreamApiKeyEnv = stringValue(
    upstream.api_key_env,
    "upstream.api_key_env",
    { required: false },
  );
  const configDirectory = path.dirname(path.resolve(configPath));

  return {
    configPath: path.resolve(configPath),
    endpoint: stringValue(upstream.base_url, "upstream.base_url").replace(
      /\/+$/,
      "",
    ),
    host: stringValue(listen.host ?? "127.0.0.1", "listen.host"),
    port: numberValue(listen.port, "listen.port", {
      minimum: 1,
      maximum: 65535,
    }),
    basePath: normalizeBasePath(routing.base_path),
    hideHeaders: !booleanValue(logging.headers, false),
    logBodies: booleanValue(logging.bodies, false),
    longTextThreshold: numberValue(
      logging.long_text_threshold ?? 1000,
      "logging.long_text_threshold",
      { minimum: 0 },
    ),
    delayMs: numberValue(
      forwarding.delay_ms ?? 0,
      "forwarding.delay_ms",
      { minimum: 0, maximum: 300000 },
    ),
    incomingApiKeyEnv,
    incomingApiKey: optionalEnvironmentValue(
      env,
      incomingApiKeyEnv,
      "client API key",
    ),
    upstreamApiKeyEnv,
    upstreamApiKey: optionalEnvironmentValue(
      env,
      upstreamApiKeyEnv,
      "upstream API key",
    ),
    allowedModels,
    allowedServiceTiers,
    requestOverrides: normalizeRequestOverrides(models.request_overrides),
    budget: normalizeBudget(config.budget, configDirectory),
    blockedStatus: numberValue(
      responses.blocked_status ?? 429,
      "responses.blocked_status",
      { minimum: 400, maximum: 599 },
    ),
    unauthorizedStatus: numberValue(
      responses.unauthorized_status ?? 401,
      "responses.unauthorized_status",
      { minimum: 400, maximum: 599 },
    ),
    invalidModelStatus: numberValue(
      responses.invalid_model_status ?? 400,
      "responses.invalid_model_status",
      { minimum: 400, maximum: 599 },
    ),
  };
}

function legacyProxyConfiguration(parsedArgs, env) {
  const incomingApiKeyEnv = parsedArgs.requireApiKeyEnv;
  return {
    configPath: null,
    endpoint: parsedArgs.endpoint.replace(/\/+$/, ""),
    host: "0.0.0.0",
    port: parsedArgs.port,
    basePath: parsedArgs.basePath,
    hideHeaders: parsedArgs.hideHeaders,
    logBodies: true,
    longTextThreshold: 1000,
    delayMs: parsedArgs.delayMs,
    incomingApiKeyEnv,
    incomingApiKey: optionalEnvironmentValue(
      env,
      incomingApiKeyEnv,
      "client API key",
    ),
    upstreamApiKeyEnv: null,
    upstreamApiKey: null,
    allowedModels: [],
    allowedServiceTiers: [],
    requestOverrides: {},
    budget: null,
    blockedStatus: 429,
    unauthorizedStatus: 401,
    invalidModelStatus: 400,
  };
}

function loadProxyConfiguration(parsedArgs, env = process.env) {
  if (!parsedArgs.configPath) {
    return legacyProxyConfiguration(parsedArgs, env);
  }
  const configPath = path.resolve(parsedArgs.configPath);
  let payload;
  try {
    payload = JSON.parse(fs.readFileSync(configPath, "utf8"));
  } catch (error) {
    throw new Error(`Could not load proxy configuration ${configPath}: ${error.message}`);
  }
  return normalizeConfiguredProxy(payload, configPath, env);
}

module.exports = {
  loadProxyConfiguration,
  normalizeConfiguredProxy,
};
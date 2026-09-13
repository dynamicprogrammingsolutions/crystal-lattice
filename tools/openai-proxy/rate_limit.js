const fs = require("node:fs");
const path = require("node:path");

function finiteToken(value) {
  return typeof value === "number" && Number.isFinite(value)
    ? Math.max(0, value)
    : 0;
}

function normalizeUsage(raw) {
  if (!raw || typeof raw !== "object") return null;
  const inputTokens = finiteToken(raw.input_tokens ?? raw.prompt_tokens);
  const outputTokens = finiteToken(
    raw.output_tokens ?? raw.completion_tokens,
  );
  const inputDetails =
    raw.input_tokens_details ?? raw.prompt_tokens_details ?? {};
  const cachedTokens = finiteToken(inputDetails.cached_tokens);
  if (inputTokens === 0 && outputTokens === 0 && cachedTokens === 0) {
    return null;
  }
  return {
    inputTokens,
    cachedTokens: Math.min(inputTokens, cachedTokens),
    outputTokens,
  };
}

function usageFromPayload(payload) {
  if (!payload || typeof payload !== "object") return null;
  return (
    normalizeUsage(payload.usage) ||
    normalizeUsage(payload.response?.usage) ||
    null
  );
}

function calculateUsageCost(usage, budget) {
  if (!usage || !budget) return 0;
  const longContext =
    budget.longContext &&
    usage.inputTokens > budget.longContext.inputTokenThreshold
      ? budget.longContext
      : null;
  const ordinaryInput = Math.max(0, usage.inputTokens - usage.cachedTokens);
  const inputMultiplier = longContext?.inputMultiplier ?? 1;
  const cachedMultiplier = longContext?.cachedInputMultiplier ?? 1;
  const outputMultiplier = longContext?.outputMultiplier ?? 1;
  return (
    (ordinaryInput * budget.pricing.input * inputMultiplier +
      usage.cachedTokens * budget.pricing.cachedInput * cachedMultiplier +
      usage.outputTokens * budget.pricing.output * outputMultiplier) /
    1_000_000
  );
}

class SseUsageCollector {
  constructor() {
    this.buffer = "";
    this.usage = null;
  }

  push(chunk) {
    this.buffer += chunk.toString("utf8");
    const records = this.buffer.split(/\r?\n\r?\n/);
    this.buffer = records.pop() ?? "";
    for (const record of records) {
      this.consumeRecord(record);
    }
  }

  finish() {
    if (this.buffer.trim()) this.consumeRecord(this.buffer);
    return this.usage;
  }

  consumeRecord(record) {
    for (const line of record.split(/\r?\n/)) {
      if (!line.startsWith("data:")) continue;
      const text = line.slice(5).trim();
      if (!text || text === "[DONE]") continue;
      try {
        const parsed = JSON.parse(text);
        this.usage = usageFromPayload(parsed) ?? this.usage;
      } catch {
        continue;
      }
    }
  }
}

class BudgetLedger {
  constructor(configuration, now = () => Date.now()) {
    this.configuration = configuration;
    this.now = now;
    this.state = { spentUsd: 0, blockedUntil: null };
    this.queue = Promise.resolve();
    if (configuration) this.load();
  }

  load() {
    try {
      const raw = JSON.parse(
        fs.readFileSync(this.configuration.statePath, "utf8"),
      );
      this.state = {
        spentUsd: finiteToken(raw.spent_usd),
        blockedUntil:
          typeof raw.blocked_until === "string" ? raw.blocked_until : null,
      };
    } catch (error) {
      if (error.code !== "ENOENT") throw error;
    }
    this.refreshExpiredBlock();
  }

  refreshExpiredBlock() {
    if (
      this.state.blockedUntil &&
      Date.parse(this.state.blockedUntil) <= this.now()
    ) {
      this.state = { spentUsd: 0, blockedUntil: null };
      this.persist();
    }
  }

  status() {
    this.refreshExpiredBlock();
    const blockedUntilMs = this.state.blockedUntil
      ? Date.parse(this.state.blockedUntil)
      : null;
    return {
      spentUsd: this.state.spentUsd,
      blockedUntil: this.state.blockedUntil,
      blocked: blockedUntilMs !== null && blockedUntilMs > this.now(),
      retryAfterSeconds:
        blockedUntilMs === null
          ? 0
          : Math.max(1, Math.ceil((blockedUntilMs - this.now()) / 1000)),
    };
  }

  async acquire() {
    if (!this.configuration?.serializeRequests) return () => {};
    let release;
    const previous = this.queue;
    this.queue = new Promise((resolve) => {
      release = resolve;
    });
    await previous;
    return release;
  }

  charge(usage) {
    if (!this.configuration || !usage) return 0;
    this.refreshExpiredBlock();
    const cost = calculateUsageCost(usage, this.configuration);
    this.state.spentUsd += cost;
    if (this.state.spentUsd >= this.configuration.limitUsd) {
      this.state.blockedUntil = new Date(
        this.now() + this.configuration.cooldownSeconds * 1000,
      ).toISOString();
    }
    this.persist();
    return cost;
  }

  persist() {
    if (!this.configuration) return;
    const statePath = this.configuration.statePath;
    fs.mkdirSync(path.dirname(statePath), { recursive: true });
    const temporaryPath = `${statePath}.${process.pid}.tmp`;
    fs.writeFileSync(
      temporaryPath,
      `${JSON.stringify(
        {
          spent_usd: this.state.spentUsd,
          blocked_until: this.state.blockedUntil,
          updated_at: new Date(this.now()).toISOString(),
        },
        null,
        2,
      )}\n`,
      { encoding: "utf8", mode: 0o600 },
    );
    fs.renameSync(temporaryPath, statePath);
  }
}

module.exports = {
  BudgetLedger,
  SseUsageCollector,
  calculateUsageCost,
  normalizeUsage,
  usageFromPayload,
};
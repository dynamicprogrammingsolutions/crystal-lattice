const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");

const {
  BudgetLedger,
  SseUsageCollector,
  calculateUsageCost,
  normalizeUsage,
} = require("../rate_limit");

function budget(statePath, overrides = {}) {
  return {
    limitUsd: 1,
    cooldownSeconds: 86400,
    statePath,
    pricing: {
      input: 0.2,
      cachedInput: 0.02,
      output: 1.2,
    },
    longContext: {
      inputTokenThreshold: 272000,
      inputMultiplier: 2,
      cachedInputMultiplier: 2,
      outputMultiplier: 1.5,
    },
    serializeRequests: true,
    ensureStreamUsage: true,
    ...overrides,
  };
}

test("normalizes Responses and Chat Completions usage fields", () => {
  assert.deepEqual(
    normalizeUsage({
      input_tokens: 100,
      input_tokens_details: { cached_tokens: 40 },
      output_tokens: 20,
    }),
    { inputTokens: 100, cachedTokens: 40, outputTokens: 20 },
  );
  assert.deepEqual(
    normalizeUsage({
      prompt_tokens: 50,
      prompt_tokens_details: { cached_tokens: 80 },
      completion_tokens: 5,
    }),
    { inputTokens: 50, cachedTokens: 50, outputTokens: 5 },
  );
});

test("calculates ordinary, cached, output, and long-context cost", () => {
  const configuration = budget("/tmp/unused");
  const ordinary = calculateUsageCost(
    { inputTokens: 200_000, cachedTokens: 20_000, outputTokens: 10_000 },
    configuration,
  );
  assert.equal(ordinary, 0.0484);

  const longContext = calculateUsageCost(
    { inputTokens: 300_000, cachedTokens: 100_000, outputTokens: 10_000 },
    configuration,
  );
  assert.equal(longContext, 0.102);
});

test("extracts completed usage from fragmented streaming events", () => {
  const collector = new SseUsageCollector();
  collector.push(
    Buffer.from(
      'event: response.completed\ndata: {"type":"response.completed","response":{"usage":{"input_tokens":12,',
    ),
  );
  collector.push(
    Buffer.from(
      '"input_tokens_details":{"cached_tokens":2},"output_tokens":3}}}\n\n',
    ),
  );
  assert.deepEqual(collector.finish(), {
    inputTokens: 12,
    cachedTokens: 2,
    outputTokens: 3,
  });
});

test("persists threshold cooldown and resets it after expiry", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "openai-proxy-budget-"));
  const statePath = path.join(root, "ledger.json");
  let now = Date.parse("2026-09-13T12:00:00Z");
  const configuration = budget(statePath, {
    limitUsd: 0.000001,
    cooldownSeconds: 60,
  });
  const ledger = new BudgetLedger(configuration, () => now);
  ledger.charge({ inputTokens: 100, cachedTokens: 0, outputTokens: 10 });

  assert.equal(ledger.status().blocked, true);
  const restored = new BudgetLedger(configuration, () => now);
  assert.equal(restored.status().blocked, true);
  assert.equal(restored.status().retryAfterSeconds, 60);

  now += 61_000;
  assert.equal(restored.status().blocked, false);
  assert.equal(restored.status().spentUsd, 0);
});
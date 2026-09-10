const assert = require("node:assert/strict");
const { spawn } = require("node:child_process");
const http = require("node:http");
const path = require("node:path");
const test = require("node:test");

const { parseProxyArgs } = require("../proxy_args");

const PROXY_PATH = path.resolve(__dirname, "..", "proxy.js");

test("parses backward-compatible positional arguments and hide flag", () => {
  assert.deepEqual(parseProxyArgs(["https://example.test/v1", "3000"]), {
    help: false,
    endpoint: "https://example.test/v1",
    port: 3000,
    basePath: "/api/v1",
    hideHeaders: false,
    requireApiKeyEnv: null,
    delayMs: 0,
  });
  assert.deepEqual(
    parseProxyArgs(["https://example.test", "3001", "/v1", "--hide-headers"]),
    {
      help: false,
      endpoint: "https://example.test",
      port: 3001,
      basePath: "/v1",
      hideHeaders: true,
      requireApiKeyEnv: null,
      delayMs: 0,
    },
  );
  assert.deepEqual(
    parseProxyArgs([
      "http://127.0.0.1:11434/v1",
      "3002",
      "/v1",
      "--require-api-key-env",
      "CRYSTAL_PROXY_API_KEY",
      "--delay-ms",
      "75",
    ]),
    {
      help: false,
      endpoint: "http://127.0.0.1:11434/v1",
      port: 3002,
      basePath: "/v1",
      hideHeaders: false,
      requireApiKeyEnv: "CRYSTAL_PROXY_API_KEY",
      delayMs: 75,
    },
  );
});

test("rejects unknown flags, extra arguments, and invalid ports", () => {
  assert.throws(
    () => parseProxyArgs(["https://example.test", "3000", "--unknown"]),
    /Unknown flag/,
  );
  assert.throws(
    () => parseProxyArgs(["https://example.test", "3000", "/v1", "extra"]),
    /Usage:/,
  );
  assert.throws(
    () => parseProxyArgs(["https://example.test", "0"]),
    /Port must be/,
  );
  assert.throws(
    () =>
      parseProxyArgs(["https://example.test", "3000", "--require-api-key-env"]),
    /requires an environment name/,
  );
  assert.throws(
    () => parseProxyArgs(["https://example.test", "3000", "--delay-ms", "-1"]),
    /between 0 and 300000/,
  );
});

async function listen(server) {
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  return server.address().port;
}

async function close(server) {
  if (typeof server.closeAllConnections === "function") {
    server.closeAllConnections();
  }
  await new Promise((resolve) => server.close(resolve));
}

async function freePort() {
  const server = http.createServer();
  const port = await listen(server);
  await close(server);
  return port;
}

function waitForOutput(state, pattern, timeoutMs = 10000) {
  return new Promise((resolve, reject) => {
    const started = Date.now();
    const interval = setInterval(() => {
      if (pattern.test(state.output)) {
        clearInterval(interval);
        resolve();
        return;
      }
      if (Date.now() - started > timeoutMs) {
        clearInterval(interval);
        reject(new Error(`Timed out waiting for ${pattern}: ${state.output}`));
      }
    }, 20);
  });
}

async function request(
  port,
  {
    authorization = "Bearer proxy-secret-token",
    headerName = "x-proxy-test-secret",
    headerValue = "proxy-header-value",
  } = {},
) {
  return await new Promise((resolve, reject) => {
    const headers = {
      "content-type": "application/json",
      [headerName]: headerValue,
    };
    if (authorization !== null) {
      headers.authorization = authorization;
    }
    const req = http.request(
      {
        host: "127.0.0.1",
        port,
        path: "/api/v1/echo",
        method: "POST",
        headers,
      },
      (res) => {
        const chunks = [];
        res.on("data", (chunk) => chunks.push(chunk));
        res.on("end", () =>
          resolve({
            status: res.statusCode,
            body: Buffer.concat(chunks).toString("utf8"),
          }),
        );
      },
    );
    req.on("error", reject);
    req.end(JSON.stringify({ prompt: "inspect headers" }));
  });
}

async function runProxyCase({ hideHeaders }) {
  let receivedHeaders = null;
  const target = http.createServer((req, res) => {
    receivedHeaders = req.headers;
    res.setHeader("content-type", "application/json");
    res.end(JSON.stringify({ ok: true }));
  });
  const targetPort = await listen(target);
  const proxyPort = await freePort();
  const args = [
    PROXY_PATH,
    `http://127.0.0.1:${targetPort}`,
    String(proxyPort),
  ];
  if (hideHeaders) {
    args.push("--hide-headers");
  }

  const child = spawn(process.execPath, args, {
    stdio: ["ignore", "pipe", "pipe"],
  });
  const state = { output: "" };
  child.stdout.on("data", (chunk) => {
    state.output += chunk.toString("utf8");
  });
  child.stderr.on("data", (chunk) => {
    state.output += chunk.toString("utf8");
  });

  try {
    await Promise.race([
      waitForOutput(state, /Waiting for requests/),
      new Promise((_, reject) => {
        child.once("exit", (code) => {
          reject(
            new Error(
              `Proxy exited before becoming ready with code ${code}: ${state.output}`,
            ),
          );
        });
      }),
    ]);
    const response = await request(proxyPort);
    assert.equal(response.status, 200);
    await waitForOutput(state, /Response status: 200/);
    assert.equal(receivedHeaders.authorization, "Bearer proxy-secret-token");
    assert.equal(receivedHeaders["x-proxy-test-secret"], "proxy-header-value");
    return state.output;
  } finally {
    if (child.exitCode === null) {
      child.kill("SIGINT");
      await new Promise((resolve) => child.once("exit", resolve));
    }
    await close(target);
  }
}

test("hidden mode suppresses header names and values without changing forwarding", async () => {
  const output = await runProxyCase({ hideHeaders: true });
  assert.match(output, /Headers: \[hidden\]/);
  assert.doesNotMatch(output, /authorization/i);
  assert.doesNotMatch(output, /proxy-secret-token/);
  assert.doesNotMatch(output, /x-proxy-test-secret/i);
  assert.doesNotMatch(output, /proxy-header-value/);
});

test("default mode retains request-header logging", async () => {
  const output = await runProxyCase({ hideHeaders: false });
  assert.match(output, /authorization/i);
  assert.match(output, /proxy-secret-token/);
  assert.match(output, /x-proxy-test-secret/i);
  assert.match(output, /proxy-header-value/);
});

test("required API key rejects invalid clients, strips auth upstream, delays, and redacts logs", async () => {
  let receivedHeaders = null;
  let targetRequests = 0;
  const target = http.createServer((req, res) => {
    targetRequests += 1;
    receivedHeaders = req.headers;
    res.setHeader("content-type", "application/json");
    res.end(JSON.stringify({ ok: true }));
  });
  const targetPort = await listen(target);
  const proxyPort = await freePort();
  const child = spawn(
    process.execPath,
    [
      PROXY_PATH,
      `http://127.0.0.1:${targetPort}`,
      String(proxyPort),
      "/api/v1",
      "--require-api-key-env",
      "CRYSTAL_PROXY_TEST_KEY",
      "--delay-ms",
      "75",
    ],
    {
      env: {
        ...process.env,
        CRYSTAL_PROXY_TEST_KEY: "review-proxy-secret",
      },
      stdio: ["ignore", "pipe", "pipe"],
    },
  );
  const state = { output: "" };
  child.stdout.on("data", (chunk) => {
    state.output += chunk.toString("utf8");
  });
  child.stderr.on("data", (chunk) => {
    state.output += chunk.toString("utf8");
  });

  try {
    await waitForOutput(state, /Waiting for requests/);
    const unauthorized = await request(proxyPort, {
      authorization: "Bearer wrong-key",
    });
    assert.equal(unauthorized.status, 401);
    assert.equal(targetRequests, 0);

    const started = Date.now();
    const authorized = await request(proxyPort, {
      authorization: "Bearer review-proxy-secret",
    });
    assert.equal(authorized.status, 200);
    assert.ok(Date.now() - started >= 60);
    assert.equal(targetRequests, 1);
    assert.equal(receivedHeaders.authorization, undefined);
    await waitForOutput(state, /Response status: 200/);
    assert.doesNotMatch(state.output, /review-proxy-secret/);
    assert.match(state.output, /"authorization": "\[redacted\]"/);
  } finally {
    if (child.exitCode === null) {
      child.kill("SIGINT");
      await new Promise((resolve) => child.once("exit", resolve));
    }
    await close(target);
  }
});

test("required API key environment must be populated", async () => {
  const proxyPort = await freePort();
  const child = spawn(
    process.execPath,
    [
      PROXY_PATH,
      "http://127.0.0.1:11434",
      String(proxyPort),
      "--require-api-key-env",
      "CRYSTAL_PROXY_MISSING_TEST_KEY",
    ],
    {
      env: {
        ...process.env,
        CRYSTAL_PROXY_MISSING_TEST_KEY: "",
      },
      stdio: ["ignore", "pipe", "pipe"],
    },
  );
  const state = { output: "" };
  child.stdout.on("data", (chunk) => {
    state.output += chunk.toString("utf8");
  });
  child.stderr.on("data", (chunk) => {
    state.output += chunk.toString("utf8");
  });

  const exitCode = await new Promise((resolve) => child.once("exit", resolve));
  assert.equal(exitCode, 1);
  assert.match(state.output, /required API key environment variable/);
});

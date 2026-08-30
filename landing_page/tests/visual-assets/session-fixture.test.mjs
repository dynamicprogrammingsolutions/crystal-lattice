import assert from "node:assert/strict";
import test from "node:test";

import { parseSessionFixtureArguments } from "../../scripts/visual-assets/session-fixture.mjs";

test("session refresh arguments require explicit runtime inputs", () => {
  assert.deepEqual(
    parseSessionFixtureArguments(
      [
        "coding-plan",
        "--config-dir",
        "/tmp/config",
        "--agent",
        "codex-openai",
        "--python",
        "/tmp/venv/bin/python",
      ],
      { runtimeRequired: true },
    ),
    {
      assetId: "coding-plan",
      options: {
        config_dir: "/tmp/config",
        agent: "codex-openai",
        python: "/tmp/venv/bin/python",
      },
    },
  );
  assert.throws(
    () =>
      parseSessionFixtureArguments(["coding-plan"], {
        runtimeRequired: true,
      }),
    /--config-dir is required/,
  );
});

test("session promotion accepts only the asset selector", () => {
  assert.deepEqual(
    parseSessionFixtureArguments(["coding-plan"], {
      runtimeRequired: false,
    }),
    { assetId: "coding-plan", options: {} },
  );
  assert.throws(
    () =>
      parseSessionFixtureArguments(
        ["coding-plan", "--unexpected", "value"],
        { runtimeRequired: false },
      ),
    /Unknown option/,
  );
});
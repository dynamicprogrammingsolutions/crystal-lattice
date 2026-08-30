import assert from "node:assert/strict";
import test from "node:test";

import { parseRuntimeUiArguments } from "../../scripts/visual-assets/runtime-ui-fixture.mjs";

test("runtime UI refresh requires an explicit Python executable", () => {
  assert.deepEqual(
    parseRuntimeUiArguments(
      [
        "mobile-workbench",
        "--python",
        "/tmp/venv/bin/python",
      ],
      { pythonRequired: true },
    ),
    {
      assetId: "mobile-workbench",
      options: { python: "/tmp/venv/bin/python" },
    },
  );
  assert.throws(
    () =>
      parseRuntimeUiArguments(["mobile-workbench"], {
        pythonRequired: true,
      }),
    /--python is required/,
  );
});

test("runtime UI promotion accepts only the asset selector", () => {
  assert.deepEqual(
    parseRuntimeUiArguments(["mobile-workbench"], {
      pythonRequired: false,
    }),
    { assetId: "mobile-workbench", options: {} },
  );
  assert.throws(
    () =>
      parseRuntimeUiArguments(
        ["mobile-workbench", "--unexpected", "value"],
        { pythonRequired: false },
      ),
    /Unknown option/,
  );
});
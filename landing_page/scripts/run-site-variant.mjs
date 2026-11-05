#!/usr/bin/env node

import { spawnSync } from "node:child_process";

const [variant, command, ...args] = process.argv.slice(2);

if (!["production", "staging"].includes(variant)) {
  console.error("Usage: run-site-variant.mjs <production|staging> <command> [...args]");
  process.exit(2);
}
if (!command) {
  console.error("Missing command");
  process.exit(2);
}

const result = spawnSync(command, args, {
  env: {
    ...process.env,
    CRYSTAL_LATTICE_SITE_VARIANT: variant,
  },
  stdio: "inherit",
  shell: process.platform === "win32",
});

if (result.error) {
  throw result.error;
}
process.exit(result.status ?? 1);
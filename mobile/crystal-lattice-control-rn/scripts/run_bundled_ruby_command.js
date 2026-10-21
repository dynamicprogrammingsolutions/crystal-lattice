#!/usr/bin/env node

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const projectRoot = path.resolve(__dirname, "..");
const expectedRuby = fs
  .readFileSync(path.join(projectRoot, ".ruby-version"), "utf8")
  .trim();
const lockfile = fs.readFileSync(
  path.join(projectRoot, "Gemfile.lock"),
  "utf8"
);
const bundlerMatch = lockfile.match(/\nBUNDLED WITH\n\s+([^\s]+)\s*$/);

if (!bundlerMatch) {
  console.error(
    "Unable to determine the required Bundler version from Gemfile.lock."
  );
  process.exit(1);
}

const expectedBundler = bundlerMatch[1];
const requestedArgs = process.argv.slice(2);
const checkOnly = requestedArgs.length === 1 && requestedArgs[0] === "--check";

if (!checkOnly && requestedArgs.length === 0) {
  console.error(
    "Usage: node scripts/run_bundled_ruby_command.js <command> [arguments...]"
  );
  process.exit(1);
}

function capture(command, args, env = process.env) {
  const result = spawnSync(command, args, {
    cwd: projectRoot,
    env,
    encoding: "utf8",
  });

  return {
    ok: result.status === 0,
    output: `${result.stdout || ""}${result.stderr || ""}`.trim(),
  };
}

function rubyVersion(command, prefixArgs, env) {
  const result = capture(
    command,
    [...prefixArgs, "ruby", "-e", "print RUBY_VERSION"],
    env
  );
  return result.ok ? result.output : null;
}

function bundlerVersion(command, prefixArgs, env) {
  const result = capture(command, [...prefixArgs, "bundle", "--version"], env);
  if (!result.ok) {
    return null;
  }
  const match = result.output.match(
    /(?:Bundler version\s+)?([0-9]+\.[0-9]+\.[0-9]+)\s*$/
  );
  return match ? match[1] : null;
}

function captureDirectRuby() {
  const result = capture("ruby", ["-e", "print RUBY_VERSION"]);
  return result.ok ? result.output : null;
}

function captureDirectBundler() {
  const result = capture("bundle", ["--version"]);
  if (!result.ok) {
    return null;
  }
  const match = result.output.match(
    /(?:Bundler version\s+)?([0-9]+\.[0-9]+\.[0-9]+)\s*$/
  );
  return match ? match[1] : null;
}

function selectToolchain() {
  const directRuby = captureDirectRuby();
  const directBundler = captureDirectBundler();
  if (directRuby === expectedRuby && directBundler === expectedBundler) {
    return {
      command: "bundle",
      prefixArgs: [],
      env: process.env,
      ruby: directRuby,
      bundler: directBundler,
      source: "current PATH",
    };
  }

  const rbenvCheck = capture("rbenv", ["--version"]);
  if (rbenvCheck.ok) {
    const env = { ...process.env, RBENV_VERSION: expectedRuby };
    const ruby = rubyVersion("rbenv", ["exec"], env);
    const bundler = bundlerVersion("rbenv", ["exec"], env);
    if (ruby === expectedRuby && bundler === expectedBundler) {
      return {
        command: "rbenv",
        prefixArgs: ["exec", "bundle"],
        env,
        ruby,
        bundler,
        source: `rbenv Ruby ${expectedRuby}`,
      };
    }
  }

  console.error(
    [
      "The mobile Ruby toolchain is not ready.",
      `Expected Ruby ${expectedRuby} with Bundler ${expectedBundler}.`,
      `Current PATH provides Ruby ${directRuby || "unavailable"} and Bundler ${
        directBundler || "unavailable"
      }.`,
      "",
      "Install/select the repository Ruby and Bundler, then retry:",
      `  rbenv install -s ${expectedRuby}`,
      `  RBENV_VERSION=${expectedRuby} rbenv exec gem install bundler -v ${expectedBundler}`,
      `  RBENV_VERSION=${expectedRuby} rbenv exec bundle install`,
    ].join("\n")
  );
  process.exit(1);
}

const toolchain = selectToolchain();

if (checkOnly) {
  console.log(
    `Ruby toolchain ready: Ruby ${toolchain.ruby}, Bundler ${toolchain.bundler} (${toolchain.source}).`
  );
  process.exit(0);
}

const result = spawnSync(
  toolchain.command,
  [...toolchain.prefixArgs, "exec", ...requestedArgs],
  {
    cwd: projectRoot,
    env: toolchain.env,
    stdio: "inherit",
  }
);

if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}

process.exit(result.status == null ? 1 : result.status);

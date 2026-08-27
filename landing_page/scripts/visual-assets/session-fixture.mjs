import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

function expandHome(value) {
  if (value === "~") {
    return process.env.HOME;
  }
  if (value.startsWith("~/")) {
    return path.join(process.env.HOME, value.slice(2));
  }
  return value;
}

export function parseSessionFixtureArguments(args, { runtimeRequired }) {
  const [assetId, ...rest] = args;
  if (!assetId || assetId.startsWith("--")) {
    throw new Error("Select one session fixture asset");
  }
  const options = {};
  for (let index = 0; index < rest.length; index += 1) {
    const name = rest[index];
    if (!["--config-dir", "--agent", "--python"].includes(name)) {
      throw new Error(`Unknown option: ${name}`);
    }
    const value = rest[index + 1];
    if (!value || value.startsWith("--")) {
      throw new Error(`${name} requires a value`);
    }
    options[name.slice(2).replaceAll("-", "_")] = expandHome(value);
    index += 1;
  }
  if (runtimeRequired) {
    for (const key of ["config_dir", "agent", "python"]) {
      if (!options[key]) {
        throw new Error(`--${key.replaceAll("_", "-")} is required`);
      }
    }
  }
  return { assetId, options };
}

function runPythonRefresh({ repositoryRoot, landingRoot, artifactRoot, config }, input) {
  const outputDirectory = path.join(
    artifactRoot,
    "session-fixtures",
    config.fixtureId,
  );
  fs.mkdirSync(outputDirectory, { recursive: true });
  const candidatePath = path.join(outputDirectory, "candidate.json");
  const provenancePath = path.join(outputDirectory, "provenance.json");
  const helperPath = path.join(
    landingRoot,
    "scripts",
    "visual-assets",
    "refresh_session_fixture.py",
  );
  const manifestPath = path.join(landingRoot, config.manifest);
  const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  const generationConfigPath = path.join(
    path.dirname(manifestPath),
    manifest.config_file,
  );
  const result = spawnSync(
    input.python,
    [
      helperPath,
      "--repository-root",
      repositoryRoot,
      "--manifest",
      manifestPath,
      "--config-dir",
      input.config_dir,
      "--config",
      generationConfigPath,
      "--agent",
      input.agent,
      "--candidate",
      candidatePath,
      "--provenance",
      provenancePath,
    ],
    {
      cwd: repositoryRoot,
      encoding: "utf8",
      maxBuffer: 64 * 1024 * 1024,
      stdio: ["ignore", "pipe", "pipe"],
    },
  );
  if (result.status !== 0) {
    throw new Error(
      result.stderr?.trim() ||
        result.stdout?.trim() ||
        "session fixture refresh failed",
    );
  }
  const candidate = JSON.parse(fs.readFileSync(candidatePath, "utf8"));
  const provenance = JSON.parse(fs.readFileSync(provenancePath, "utf8"));
  return {
    asset_id: config.fixtureId,
    candidate: path.relative(repositoryRoot, candidatePath),
    provenance: path.relative(repositoryRoot, provenancePath),
    messages: candidate.messages.length,
    tool_activity: provenance.tool_activity,
    bytes: fs.statSync(candidatePath).size,
  };
}

export function sessionFixtureAssetCommands() {
  const inspect = ({ repositoryRoot, landingRoot, artifactRoot, config }) => {
    const manifestPath = path.join(landingRoot, config.manifest);
    const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
    const promptPath = path.join(
      path.dirname(manifestPath),
      manifest.prompt_file,
    );
    if (!fs.readFileSync(promptPath, "utf8").trim()) {
      throw new Error(`Empty session prompt: ${promptPath}`);
    }
    const reviewedPath = path.resolve(repositoryRoot, config.reviewedFixture);
    const candidatePath = path.join(
      artifactRoot,
      "session-fixtures",
      config.fixtureId,
      "candidate.json",
    );
    if (fs.existsSync(reviewedPath)) {
      JSON.parse(fs.readFileSync(reviewedPath, "utf8"));
    }
    if (fs.existsSync(candidatePath)) {
      JSON.parse(fs.readFileSync(candidatePath, "utf8"));
    }
    return {
      asset_id: config.fixtureId,
      variant: "session-fixture",
      manifest: path.relative(repositoryRoot, manifestPath),
      reviewed_exists: fs.existsSync(reviewedPath),
      candidate_exists: fs.existsSync(candidatePath),
      bytes: fs.existsSync(reviewedPath)
        ? fs.statSync(reviewedPath).size
        : 0,
    };
  };
  return {
    list: ({ config }) => ({
      id: config.fixtureId,
      commands: ["refresh-session", "promote-session"],
    }),
    "refresh-session": (context) => runPythonRefresh(context, context.input),
    inspect,
    check: inspect,
    "promote-session": ({ repositoryRoot, artifactRoot, config }) => {
      const candidatePath = path.join(
        artifactRoot,
        "session-fixtures",
        config.fixtureId,
        "candidate.json",
      );
      const reviewedPath = path.resolve(repositoryRoot, config.reviewedFixture);
      if (!fs.existsSync(candidatePath)) {
        throw new Error(`Missing session candidate: ${candidatePath}`);
      }
      JSON.parse(fs.readFileSync(candidatePath, "utf8"));
      return {
        report: {
          asset_id: config.fixtureId,
          candidate: path.relative(repositoryRoot, candidatePath),
          reviewed: path.relative(repositoryRoot, reviewedPath),
          bytes: fs.statSync(candidatePath).size,
        },
        async apply() {
          fs.mkdirSync(path.dirname(reviewedPath), { recursive: true });
          fs.copyFileSync(candidatePath, reviewedPath);
        },
      };
    },
  };
}

export async function runSessionFixtureCatalogCommand(
  context,
  commandName,
  { runtimeRequired = false, mutate = false } = {},
) {
  const { assetId, options } = parseSessionFixtureArguments(context.arguments, {
    runtimeRequired,
  });
  const asset = context.catalog.assetMap.get(assetId);
  if (!asset?.hasCommand(commandName)) {
    throw new Error(`${assetId} does not support ${commandName}`);
  }
  const result = await asset.runCommand(
    commandName,
    {
      repositoryRoot: context.repositoryRoot,
      landingRoot: context.landingRoot,
      artifactRoot: context.artifactRoot,
    },
    options,
  );
  if (mutate) {
    await context.applyAll([result]);
    return context.writeReport(commandName, { results: [result.report] });
  }
  return context.writeReport(commandName, { results: [result] });
}
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

function defaultPython() {
  const configured =
    process.env.CRYSTAL_PLUGIN_PYTHON || process.env.PYTHON;
  if (configured) {
    return configured;
  }
  const crystalPython = path.join(
    process.env.HOME ?? "",
    ".crystal",
    "dev-cli-venv",
    "bin",
    "python",
  );
  return fs.existsSync(crystalPython) ? crystalPython : "python3";
}

export function parseRuntimeUiArguments(args, { pythonRequired }) {
  const [assetId, ...rest] = args;
  if (!assetId || assetId.startsWith("--")) {
    throw new Error("Select one runtime UI fixture asset");
  }
  const options = {};
  for (let index = 0; index < rest.length; index += 1) {
    const name = rest[index];
    if (name !== "--python") {
      throw new Error(`Unknown option: ${name}`);
    }
    const value = rest[index + 1];
    if (!value || value.startsWith("--")) {
      throw new Error("--python requires a value");
    }
    options.python = expandHome(value);
    index += 1;
  }
  if (pythonRequired && !options.python) {
    throw new Error("--python is required");
  }
  return { assetId, options };
}

function fixturePaths({ repositoryRoot, landingRoot, artifactRoot, config }) {
  return {
    helperPath: path.join(
      landingRoot,
      "scripts",
      "visual-assets",
      "refresh_runtime_ui_fixture.py",
    ),
    configPath: path.join(landingRoot, config.config),
    sessionFixturePath: path.resolve(repositoryRoot, config.sessionFixture),
    candidatePath: path.join(
      artifactRoot,
      "runtime-ui",
      config.fixtureId,
      "candidate.json",
    ),
    reviewedPath: path.resolve(repositoryRoot, config.reviewedFixture),
  };
}

function generateCandidate(context, python) {
  const paths = fixturePaths(context);
  fs.mkdirSync(path.dirname(paths.candidatePath), { recursive: true });
  const result = spawnSync(
    python,
    [
      paths.helperPath,
      "--repository-root",
      context.repositoryRoot,
      "--config",
      paths.configPath,
      "--session-fixture",
      paths.sessionFixturePath,
      "--agent",
      context.config.agent,
      "--candidate",
      paths.candidatePath,
    ],
    {
      cwd: context.repositoryRoot,
      encoding: "utf8",
      maxBuffer: 64 * 1024 * 1024,
      stdio: ["ignore", "pipe", "pipe"],
    },
  );
  if (result.status !== 0) {
    throw new Error(
      result.stderr?.trim() ||
        result.stdout?.trim() ||
        "runtime UI fixture refresh failed",
    );
  }
  return paths;
}

function summarizeFixture(filePath) {
  const fixture = JSON.parse(fs.readFileSync(filePath, "utf8"));
  return {
    bytes: fs.statSync(filePath).size,
    settings: Array.isArray(fixture.session_ui_schema)
      ? fixture.session_ui_schema.filter(
          (element) => (element.ui_type ?? "config") === "config",
        ).length
      : 0,
    session_actions: Array.isArray(fixture.session_application_ui_schema)
      ? fixture.session_application_ui_schema.filter(
          (element) => element.ui_type === "session_action",
        ).length
      : 0,
    message_actions: [
      ...(Array.isArray(fixture.session_application_ui_schema)
        ? fixture.session_application_ui_schema
        : []),
      ...(Array.isArray(fixture.session_ui_schema)
        ? fixture.session_ui_schema
        : []),
    ].filter((element) => element.ui_type === "message_action").length,
    snapshots: Array.isArray(fixture.snapshots)
      ? fixture.snapshots.length
      : 0,
  };
}

export function runtimeUiFixtureAssetCommands() {
  return {
    list: ({ config }) => ({
      id: config.fixtureId,
      commands: ["refresh-runtime-ui", "promote-runtime-ui"],
    }),
    "refresh-runtime-ui": (context) => {
      const paths = generateCandidate(context, context.input.python);
      return {
        asset_id: context.config.fixtureId,
        candidate: path.relative(context.repositoryRoot, paths.candidatePath),
        ...summarizeFixture(paths.candidatePath),
      };
    },
    inspect: (context) => {
      const paths = fixturePaths(context);
      const selected = fs.existsSync(paths.reviewedPath)
        ? paths.reviewedPath
        : paths.candidatePath;
      return {
        asset_id: context.config.fixtureId,
        variant: "runtime-ui",
        reviewed_exists: fs.existsSync(paths.reviewedPath),
        candidate_exists: fs.existsSync(paths.candidatePath),
        ...(fs.existsSync(selected)
          ? summarizeFixture(selected)
          : { bytes: 0, settings: 0, session_actions: 0, message_actions: 0, snapshots: 0 }),
      };
    },
    check: (context) => {
      const paths = generateCandidate(context, defaultPython());
      if (!fs.existsSync(paths.reviewedPath)) {
        throw new Error(`Missing reviewed runtime UI fixture: ${paths.reviewedPath}`);
      }
      const candidate = fs.readFileSync(paths.candidatePath);
      const reviewed = fs.readFileSync(paths.reviewedPath);
      if (!candidate.equals(reviewed)) {
        throw new Error(
          `${context.config.fixtureId} runtime UI fixture is stale; refresh and promote it`,
        );
      }
      return {
        asset_id: context.config.fixtureId,
        variant: "runtime-ui",
        ...summarizeFixture(paths.reviewedPath),
      };
    },
    "promote-runtime-ui": (context) => {
      const paths = fixturePaths(context);
      if (!fs.existsSync(paths.candidatePath)) {
        throw new Error(`Missing runtime UI candidate: ${paths.candidatePath}`);
      }
      JSON.parse(fs.readFileSync(paths.candidatePath, "utf8"));
      return {
        report: {
          asset_id: context.config.fixtureId,
          candidate: path.relative(context.repositoryRoot, paths.candidatePath),
          reviewed: path.relative(context.repositoryRoot, paths.reviewedPath),
          ...summarizeFixture(paths.candidatePath),
        },
        async apply() {
          fs.mkdirSync(path.dirname(paths.reviewedPath), { recursive: true });
          fs.copyFileSync(paths.candidatePath, paths.reviewedPath);
        },
      };
    },
  };
}

export async function runRuntimeUiCatalogCommand(
  context,
  commandName,
  { pythonRequired = false, mutate = false } = {},
) {
  const { assetId, options } = parseRuntimeUiArguments(context.arguments, {
    pythonRequired,
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
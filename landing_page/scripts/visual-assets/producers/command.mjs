import fs from "node:fs";
import path from "node:path";

import { captureOutput } from "../api.mjs";

export function commandCapture({
  id,
  projectDirectory,
  command,
  outputs,
  environment = {},
}) {
  if (!id || !projectDirectory || !Array.isArray(command) || command.length === 0) {
    throw new Error(
      "commandCapture requires id, projectDirectory, and command",
    );
  }

  let pendingRun;

  async function execute(context) {
    if (!pendingRun) {
      pendingRun = context
        .run(command[0], command.slice(1), {
          cwd: path.resolve(context.repositoryRoot, projectDirectory),
          env: environment,
          stdio: "inherit",
        })
        .catch((error) => {
          pendingRun = undefined;
          throw error;
        });
    }
    await pendingRun;
  }

  return {
    id,
    output(name) {
      const candidatePath = outputs[name];
      if (!candidatePath) {
        throw new Error(`${id}: unknown capture output ${name}`);
      }
      return captureOutput({
        candidatePath,
        async capture(context) {
          await execute(context);
          const absolutePath = path.resolve(
            context.repositoryRoot,
            candidatePath,
          );
          if (!fs.existsSync(absolutePath)) {
            throw new Error(
              `${id}/${name}: command did not create ${candidatePath}`,
            );
          }
          return absolutePath;
        },
      });
    },
  };
}
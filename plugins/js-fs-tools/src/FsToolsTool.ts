import * as fs from "node:fs/promises";
import * as path from "node:path";

type ToolHostEmit = (event: { type: string; payload?: unknown }) => void;

type ToolState = {
  config: Record<string, unknown>;
};

function resolvePath(filePath: unknown, config: Record<string, unknown>) {
  const cwd =
    typeof config?.working_directory === "string" && config.working_directory
      ? config.working_directory
      : process.cwd();

  if (typeof filePath !== "string" || !filePath) {
    throw new Error("file_path must be a non-empty string");
  }
  return path.resolve(cwd, filePath);
}

function isAllowed(targetPath: string, config: Record<string, unknown>) {
  const allowed = Array.isArray(config?.allowed_paths) ? config.allowed_paths : [];
  if (!allowed.length) {
    return false;
  }

  const target = path.resolve(targetPath);
  for (const baseRaw of allowed) {
    if (typeof baseRaw !== "string" || !baseRaw) {
      continue;
    }
    const base = path.resolve(baseRaw);
    const rel = path.relative(base, target);
    if (rel === "" || (!rel.startsWith(".." + path.sep) && rel !== "..")) {
      return true;
    }
  }
  return false;
}

function shouldStreamParts(config: Record<string, unknown>) {
  if (Object.prototype.hasOwnProperty.call(config, "node_tool_stream_parts")) {
    return Boolean((config as any).node_tool_stream_parts);
  }
  return true;
}

export const FsToolsTool = {
  name: "js_fs_tools",
  version: "0.1.0",

  init(config: Record<string, unknown>): ToolState {
    return { config };
  },

  getToolSchemas() {
    return [
      {
        type: "function",
        function: {
          name: "write_file",
          description: "Write text content to a file path.",
          parameters: {
            type: "object",
            properties: {
              file_path: { type: "string" },
              content: { type: "string" },
            },
            required: ["file_path", "content"],
          },
        },
      },
      {
        type: "function",
        function: {
          name: "read_file",
          description: "Read text content from a file path.",
          parameters: {
            type: "object",
            properties: {
              file_path: { type: "string" },
            },
            required: ["file_path"],
          },
        },
      },
    ];
  },

  async executeTool(
    toolName: string,
    args: Record<string, unknown>,
    state: ToolState,
    emit: ToolHostEmit
  ) {
    const config = state?.config ?? {};
    const stream = shouldStreamParts(config);

    if (toolName === "write_file") {
      const resolved = resolvePath(args?.file_path, config);
      if (!isAllowed(resolved, config)) {
        return { success: false, error: `Path not allowed: ${resolved}` };
      }
      if (stream) {
        emit({ type: "part", payload: { message: "write_file: start" } });
        emit({ type: "part", payload: { message: "write_file: writing" } });
      }
      await fs.mkdir(path.dirname(resolved), { recursive: true });
      await fs.writeFile(resolved, String(args?.content ?? ""), { encoding: "utf-8" });
      return {
        success: true,
        result: {
          file_path: resolved,
          bytes: String(args?.content ?? "").length,
        },
      };
    }

    if (toolName === "read_file") {
      const resolved = resolvePath(args?.file_path, config);
      if (!isAllowed(resolved, config)) {
        return { success: false, error: `Path not allowed: ${resolved}` };
      }
      if (stream) {
        emit({ type: "part", payload: { message: "read_file: start" } });
        emit({ type: "part", payload: { message: "read_file: reading" } });
      }
      const text = await fs.readFile(resolved, { encoding: "utf-8" });
      return { success: true, result: { file_path: resolved, content: text } };
    }

    return { success: false, error: `Unknown tool: ${toolName}` };
  },

  formatToolResult(result: any) {
    if (!result?.success) {
      return `Error: ${String(result?.error ?? "unknown")}`;
    }
    if (result?.result?.content != null) {
      return `File contents: ${String(result.result.content)}`;
    }
    if (result?.result?.file_path) {
      return `Wrote file: ${String(result.result.file_path)}`;
    }
    return `Result: ${JSON.stringify(result.result ?? null)}`;
  },
} as const;

export default FsToolsTool;

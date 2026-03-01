export type ToolHostEmit = (event: { type: string; payload?: unknown }) => void;

type ToolState = {
  config: Record<string, unknown>;
};

export default class ClassEchoTool {
  name = "js_class_tool";
  version = "0.1.0";

  init(config: Record<string, unknown>): ToolState {
    return { config };
  }

  getToolSchemas() {
    return [
      {
        type: "function",
        function: {
          name: "class_echo",
          description: "Echo implemented as a TypeScript class.",
          parameters: {
            type: "object",
            properties: {
              value: { type: "string" },
            },
            required: ["value"],
          },
        },
      },
    ];
  }

  async executeTool(
    toolName: string,
    args: Record<string, unknown>,
    _state: ToolState,
    emit: ToolHostEmit
  ) {
    if (toolName !== "class_echo") {
      return { success: false, error: `Unknown tool: ${toolName}` };
    }

    emit({ type: "part", payload: { message: "class_echo: start" } });
    emit({ type: "part", payload: { message: "class_echo: working" } });

    return { success: true, result: String(args?.value ?? "") };
  }

  formatToolResult(result: any) {
    if (!result?.success) {
      return `Error: ${String(result?.error ?? "unknown")}`;
    }
    return `ClassEcho: ${String(result?.result ?? "")}`;
  }
}

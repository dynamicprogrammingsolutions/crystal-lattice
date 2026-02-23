type ToolHostEmit = (event: { type: string; payload?: unknown }) => void;

export const UpperTool = {
  name: "js_single_file_tool",
  version: "0.1.0",

  init(config: Record<string, unknown>) {
    return { config };
  },

  getToolSchemas() {
    return [
      {
        type: "function",
        function: {
          name: "upper",
          description: "Uppercase the provided string.",
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
  },

  async executeTool(toolName: string, args: Record<string, unknown>, _state: any, emit: ToolHostEmit) {
    if (toolName !== "upper") {
      return { success: false, error: `Unknown tool: ${toolName}` };
    }
    emit({ type: "part", payload: { message: "uppercasing" } });
    return { success: true, result: String(args?.value ?? "").toUpperCase() };
  },
} as const;

export default UpperTool;

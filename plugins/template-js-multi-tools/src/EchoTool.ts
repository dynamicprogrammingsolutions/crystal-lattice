export type ToolHostEmit = (event: { type: string; payload?: unknown }) => void;

type ToolSchema = Record<string, unknown>;

export const echoTool = {
  name: "template_js_echo",
  version: "0.1.0",

  init(config: Record<string, unknown>) {
    return { config };
  },

  getToolSchemas(): ToolSchema[] {
    return [
      {
        type: "function",
        function: {
          name: "echo",
          description: "Echo back the provided value.",
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
    if (toolName !== "echo") {
      return { success: false, error: `Unknown tool: ${toolName}` };
    }
    emit({ type: "part", payload: { message: "echoing" } });
    return { success: true, result: String(args?.value ?? "") };
  },
} as const;

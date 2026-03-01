export type ToolHostEmit = (event: { type: string; payload?: unknown }) => void;

type ToolSchema = Record<string, unknown>;

export const reverseTool = {
  name: "js_reverse",
  version: "0.1.0",

  init(config: Record<string, unknown>) {
    return { config };
  },

  getToolSchemas(): ToolSchema[] {
    return [
      {
        type: "function",
        function: {
          name: "reverse",
          description: "Reverse the provided string.",
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
    if (toolName !== "reverse") {
      return { success: false, error: `Unknown tool: ${toolName}` };
    }
    const value = String(args?.value ?? "");
    emit({ type: "part", payload: { message: "reversing" } });
    return { success: true, result: value.split("").reverse().join("") };
  },
} as const;

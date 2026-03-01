export type ToolHostEmit = (event: { type: string; payload?: unknown }) => void;

type ToolSchema = Record<string, unknown>;

type ToolState = {
  config: Record<string, unknown>;
  calls?: number;
};

export const EchoTool = {
  name: "js_echo_tool",
  version: "0.1.0",

  init(config: Record<string, unknown>): ToolState {
    return { config, calls: 0 };
  },

  getToolSchemas(_state: ToolState): ToolSchema[] {
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

  async executeTool(
    toolName: string,
    args: Record<string, unknown>,
    state: ToolState,
    emit: ToolHostEmit
  ) {
    if (toolName !== "echo") {
      return { success: false, error: `Unknown tool: ${toolName}` };
    }

    state.calls = (state.calls ?? 0) + 1;
    emit({ type: "part", payload: { message: "starting" } });
    emit({ type: "part", payload: { message: "working" } });

    return {
      success: true,
      result: {
        value: String(args?.value ?? ""),
        calls: state.calls,
      },
    };
  },

  formatToolResult(result: any) {
    if (!result?.success) {
      return `Error: ${String(result?.error ?? "unknown")}`;
    }
    const value = result?.result?.value;
    const calls = result?.result?.calls;
    return `Echo: ${String(value)} (calls=${String(calls)})`;
  },

  toDisplayFormat(text: string, result: any) {
    const single = result?.success
      ? `echo ${String(result?.result?.value ?? "")}`
      : "echo (error)";
    return { type: "text", content: text, single_line: single };
  },
} as const;

export default EchoTool;

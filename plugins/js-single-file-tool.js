export default {
  name: "js_single_file_tool",
  version: "0.1.0",

  init(config) {
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

  async executeTool(toolName, args, _state, emit) {
    if (toolName !== "upper") {
      return { success: false, error: `Unknown tool: ${toolName}` };
    }
    emit({ type: "part", payload: { message: "uppercasing" } });
    return { success: true, result: String(args?.value ?? "").toUpperCase() };
  },
};

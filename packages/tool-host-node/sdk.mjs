export function defineToolPlugin(plugin) {
  if (!plugin || (typeof plugin !== "object" && typeof plugin !== "function")) {
    throw new Error("defineToolPlugin: plugin must be an object or a class");
  }

  // When given a plain object, validate required methods.
  // (Classes/factories are validated by the tool host at runtime.)
  if (typeof plugin === "object") {
    if (
      typeof plugin.getToolSchemas !== "function" &&
      typeof plugin.get_tool_schemas !== "function"
    ) {
      throw new Error("defineToolPlugin: plugin must implement getToolSchemas(state)");
    }
    if (typeof plugin.executeTool !== "function" && typeof plugin.execute_tool !== "function") {
      throw new Error(
        "defineToolPlugin: plugin must implement executeTool(toolName, args, state, emit)"
      );
    }
  }

  return plugin;
}

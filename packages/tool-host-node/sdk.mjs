export function defineToolPlugin(plugin) {
  if (!plugin || typeof plugin !== "object") {
    throw new Error("defineToolPlugin: plugin must be an object");
  }
  if (typeof plugin.getToolSchemas !== "function" && typeof plugin.get_tool_schemas !== "function") {
    throw new Error("defineToolPlugin: plugin must implement getToolSchemas(state)");
  }
  if (typeof plugin.executeTool !== "function" && typeof plugin.execute_tool !== "function") {
    throw new Error(
      "defineToolPlugin: plugin must implement executeTool(toolName, args, state, emit)"
    );
  }
  return plugin;
}

import readline from "node:readline";
import { pathToFileURL } from "node:url";

const PROTOCOL_VERSION = 1;

function parseArgs(argv) {
  const args = { entry: null, exportName: null };
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (token === "--entry") {
      args.entry = argv[i + 1] ?? null;
      i += 1;
      continue;
    }
    if (token === "--export") {
      args.exportName = argv[i + 1] ?? null;
      i += 1;
      continue;
    }
  }
  return args;
}

function writeLine(obj) {
  process.stdout.write(`${JSON.stringify(obj)}\n`);
}

function toErrorPayload(error) {
  if (error instanceof Error) {
    return {
      type: error.name || "Error",
      detail: String(error.message || error),
      stack: error.stack || "",
    };
  }
  return {
    type: "Error",
    detail: String(error),
    stack: "",
  };
}

function normalizePlugin(plugin) {
  if (!plugin || typeof plugin !== "object") {
    throw new Error("Loaded plugin is not an object");
  }

  const methodMap = {
    get_config_schema: ["get_config_schema", "getConfigSchema"],
    get_ui_elements: ["get_ui_elements", "getUiElements"],
    init: ["init"],
    get_tags: ["get_tags", "getTags"],
    required_tags: ["required_tags", "requiredTags"],
    get_tool_schemas: ["get_tool_schemas", "getToolSchemas"],
    execute_tool: ["execute_tool", "executeTool"],
    format_tool_result: ["format_tool_result", "formatToolResult"],
    format_tool_call_preview: [
      "format_tool_call_preview",
      "formatToolCallPreview",
    ],
    to_display_format: ["to_display_format", "toDisplayFormat"],
  };

  const methods = {};
  for (const [rpcName, candidates] of Object.entries(methodMap)) {
    for (const name of candidates) {
      if (typeof plugin[name] === "function") {
        methods[rpcName] = plugin[name].bind(plugin);
        break;
      }
    }
  }

  return {
    name: typeof plugin.name === "string" ? plugin.name : "node_tool",
    version: typeof plugin.version === "string" ? plugin.version : "unknown",
    methods,
  };
}

function instantiatePluginIfNeeded(value) {
  if (typeof value !== "function") {
    return value;
  }

  // Support exporting a class (preferred) or a factory function.
  try {
    return new value();
  } catch (err) {
    // If it's not constructable, fall back to calling as a function.
    try {
      return value();
    } catch (_err2) {
      throw err;
    }
  }
}

async function loadPlugin(entryPath, exportName) {
  const url = pathToFileURL(entryPath).href;
  const mod = await import(url);

  let plugin = null;
  if (exportName) {
    plugin = mod[exportName];
  } else if (mod && mod.default) {
    plugin = mod.default;
  } else {
    plugin = mod;
  }

  // CommonJS interop: sometimes the namespace object contains the actual
  // exports under `.default`.
  if (!exportName && plugin && typeof plugin === "object" && plugin.default) {
    const maybe = plugin.default;
    if (maybe && typeof maybe === "object") {
      plugin = maybe;
    }
  }

  if (!plugin) {
    throw new Error(
      exportName
        ? `No named export ${JSON.stringify(exportName)} found in ${entryPath}`
        : `No default export found in ${entryPath}`
    );
  }
  const instantiated = instantiatePluginIfNeeded(plugin);
  return normalizePlugin(instantiated);
}

function protocolViolation(detail) {
  const err = new Error(detail);
  err.name = "ProtocolError";
  return err;
}

async function main() {
  const { entry, exportName } = parseArgs(process.argv.slice(2));
  if (!entry) {
    process.stderr.write("Missing required --entry argument\n");
    process.exit(2);
  }

  const plugin = await loadPlugin(entry, exportName);

  const rl = readline.createInterface({
    input: process.stdin,
    crlfDelay: Infinity,
  });

  for await (const rawLine of rl) {
    const line = rawLine.trim();
    if (!line) {
      continue;
    }

    let msg;
    try {
      msg = JSON.parse(line);
    } catch (err) {
      writeLine({
        v: PROTOCOL_VERSION,
        id: null,
        ok: false,
        error: toErrorPayload(protocolViolation(`Invalid JSON: ${err}`)),
      });
      continue;
    }

    const id = msg?.id ?? null;
    try {
      if (!msg || typeof msg !== "object") {
        throw protocolViolation("Message must be a JSON object");
      }
      if (msg.v !== PROTOCOL_VERSION) {
        throw protocolViolation(
          `Unsupported protocol version ${String(msg.v)} (expected ${PROTOCOL_VERSION})`
        );
      }
      if (typeof msg.id !== "string" || !msg.id) {
        throw protocolViolation("Missing request id");
      }
      if (typeof msg.method !== "string" || !msg.method) {
        throw protocolViolation("Missing method");
      }

      const method = msg.method;
      const params = msg.params && typeof msg.params === "object" ? msg.params : {};

      if (method === "handshake") {
        writeLine({
          v: PROTOCOL_VERSION,
          id,
          ok: true,
          result: {
            value: {
              protocolVersion: PROTOCOL_VERSION,
              host: "tool-host-node",
              node: process.version,
              plugin: { name: plugin.name, version: plugin.version },
            },
          },
        });
        continue;
      }

      const fn = plugin.methods[method];
      const optionalDefaults = {
        get_config_schema: {},
        get_ui_elements: [],
        get_tags: [],
        required_tags: [],
        format_tool_result: "",
        format_tool_call_preview: "",
        to_display_format: null,
      };

      if (typeof fn !== "function") {
        if (method === "init") {
          const cfg = params && typeof params === "object" ? params.config ?? {} : {};
          const state = { config: cfg };
          writeLine({
            v: PROTOCOL_VERSION,
            id,
            ok: true,
            result: { value: state, state },
          });
          continue;
        }
        if (Object.prototype.hasOwnProperty.call(optionalDefaults, method)) {
          writeLine({
            v: PROTOCOL_VERSION,
            id,
            ok: true,
            result: { value: optionalDefaults[method] },
          });
          continue;
        }
        throw protocolViolation(`Unknown method: ${method}`);
      }

      const emit = (event) => {
        if (!event || typeof event !== "object") {
          return;
        }
        writeLine({
          v: PROTOCOL_VERSION,
          id,
          event,
        });
      };

      let value;
      let state = params.state;

      if (method === "execute_tool") {
        const toolName = params.tool_name;
        const args = params.arguments;
        state = params.state;
        value = await fn(toolName, args ?? {}, state ?? {}, emit);
      } else if (method === "get_tool_schemas") {
        state = params.state;
        value = await fn(state ?? {});
      } else if (method === "init") {
        value = await fn(params.config ?? {});
        state = value && typeof value === "object" ? value : { config: params.config ?? {} };
        value = state;
      } else if (method === "get_tags") {
        value = await fn(params.config ?? {}, params.models ?? []);
      } else if (method === "required_tags") {
        value = await fn();
      } else if (method === "format_tool_result") {
        state = params.state;
        value = await fn(params.result ?? {}, state ?? {});
      } else if (method === "format_tool_call_preview") {
        state = params.state;
        value = await fn(params.tool_name, params.arguments ?? {}, state ?? {});
      } else if (method === "to_display_format") {
        state = params.state;
        value = await fn(params.text ?? "", params.result ?? {}, state ?? {});
      } else if (method === "get_config_schema" || method === "get_ui_elements") {
        value = await fn();
      } else {
        value = await fn(params);
      }

      const result = { value };
      if (Object.prototype.hasOwnProperty.call(params, "state") || method === "init") {
        result.state = state;
      }

      writeLine({ v: PROTOCOL_VERSION, id, ok: true, result });
    } catch (err) {
      writeLine({ v: PROTOCOL_VERSION, id, ok: false, error: toErrorPayload(err) });
    }
  }
}

try {
  await main();
} catch (err) {
  process.stderr.write(`${err instanceof Error ? err.stack || err.message : String(err)}\n`);
  process.exit(1);
}

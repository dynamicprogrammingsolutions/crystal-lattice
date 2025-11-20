"""
PROJECT_PLAN Example 6: FastAPI/WebSocket App (Ollama)
Runs a simple WS endpoint using the core and plugins.
"""

from fastapi import FastAPI, WebSocket  # type: ignore[reportMissingImports]
from agent_core import AgentCore
from plugins.providers.openai.python.openai_provider import OpenAICompatibleProvider
from examples.example3_web_search_feature import WebSearchFeature
from examples.example4_file_reader_tool import FileReaderTool
import json

app = FastAPI()

# Load and resolve config (application responsibility)
import os


def resolve_config(config):
    """Resolve ${env:...} and ${file:...} references"""
    resolved = {}
    for key, value in config.items():
        if isinstance(value, str):
            if value.startswith("${env:"):
                var_name = value[6:-1]
                resolved[key] = os.getenv(var_name)
            elif value.startswith("${file:"):
                file_path = value[7:-1]
                with open(os.path.expanduser(file_path)) as f:
                    resolved[key] = f.read().strip()
            else:
                resolved[key] = value
        else:
            resolved[key] = value
    return resolved


# Load config from file
with open("config.json") as f:
    config = json.load(f)

# Initialize core
core = AgentCore()

# Register plugins (just classes, no config)
core.register_provider(OpenAICompatibleProvider)
core.register_feature(WebSearchFeature)
core.register_tool(FileReaderTool)


# Application resolves and merges config
def get_agent_config(agent_name):
    """Resolve and merge config for an agent."""
    agent_config = config["agents"][agent_name]
    provider_name = agent_config.get("provider", "openai")

    # Start with provider defaults
    merged = resolve_config(config["providers"]["defaults"][provider_name].copy())

    # Merge agent-specific config (flat structure)
    merged.update(resolve_config(agent_config))

    return merged


# Application manages sessions
sessions = {}


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()

    if session_id not in sessions:
        sessions[session_id] = core.create_session(session_id)
    session = sessions[session_id]

    # Application manages config
    agent_config = get_agent_config("default")
    # Initialize tool state once per connection
    file_reader_tool = FileReaderTool()
    file_reader_state = file_reader_tool.init(agent_config)

    try:
        while True:
            data = await websocket.receive_json()

            if data["type"] == "message":
                # Add user message (functional)
                session = core.add_message(session, "user", data["content"])

                # Tool loop (application logic)
                max_iterations = 5
                for i in range(max_iterations):
                    # Stream response (functional - pass config)
                    final_messages = []
                    async for chunk in core.send_request_stream_async(
                        session, agent_config
                    ):
                        if chunk["type"] == "partial":
                            await websocket.send_json(
                                {
                                    "type": "partial",
                                    "content": chunk["message"]["content"],
                                }
                            )
                        elif chunk["type"] == "final":
                            session = chunk["session"]
                            final_messages = chunk["messages"]

                    # Check for tool calls
                    tool_calls = (
                        (final_messages[-1] if final_messages else {})
                        .get("metadata", {})
                        .get("tool_calls", [])
                    )

                    if not tool_calls:
                        # Done
                        await websocket.send_json(
                            {"type": "final", "messages": final_messages}
                        )
                        break

                    # Execute tools
                    for tool_call in tool_calls:
                        tool_name = tool_call["function"]["name"]
                        arguments = json.loads(tool_call["function"]["arguments"])

                        # Notify frontend
                        await websocket.send_json(
                            {
                                "type": "tool_call",
                                "name": tool_name,
                                "arguments": arguments,
                            }
                        )

                        # Execute (stateful - pass initialized tool state)
                        result = file_reader_tool.execute_tool(
                            tool_name, arguments, file_reader_state
                        )
                        formatted = file_reader_tool.format_tool_result(
                            result, file_reader_state
                        )

                        # Add tool result (functional)
                        session = core.add_message(
                            session,
                            "tool",
                            formatted,
                            metadata={
                                "tool_call_id": tool_call["id"],
                                "name": tool_name,
                            },
                        )

                    # Continue loop with tool results

            elif data["type"] == "update_config":
                # Application updates its config
                agent_config = {**agent_config, **data["updates"]}
                sessions[session_id] = session  # Store updated session

    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()


# Optional function so tests can import without running a server
def run_example():  # pragma: no cover
    return app

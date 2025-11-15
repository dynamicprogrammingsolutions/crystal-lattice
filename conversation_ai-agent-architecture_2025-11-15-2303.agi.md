# Ai agent architecture
A Big-AGI conversation, updated on 11/13/2025, 9:39:54 PM.

## System message ##

*You are an experienced developer.
Current date: Thu, 13 Nov 2025 at 09 pm CET

This note is empty*

---

## 👤 You ##

What are the common elements of an AI agent platform and what is the internal flow of a user request (including special cases like tool call handling)? I am interested in the core, the part that handles the Api call, function call results, streaming, storing the conversation state. Also interested in the implementation details. Think of a minimum viable product for local use.

---

## Assistant · *Claude 4 Sonnet* ##

# AI Agent Platform Architecture - Core Components & Flow

Let me break down the essential components and flow for an MVP AI agent platform.

## Core Components

### 1. **Conversation Manager**
- Stores and retrieves conversation history
- Manages message state (user/assistant/system/tool messages)
- Handles context window management

### 2. **LLM Client**
- API communication with LLM provider (OpenAI, Anthropic, etc.)
- Handles streaming responses
- Manages retries and error handling

### 3. **Tool Registry & Executor**
- Registers available functions/tools
- Validates tool calls
- Executes functions and returns results

### 4. **Agent Loop Controller**
- Orchestrates the request-response cycle
- Handles multi-turn tool calling
- Determines when the response is complete

## Request Flow

Here's the internal flow with implementation details:

```python
from typing import List, Dict, Callable, Optional, Generator
import json
from dataclasses import dataclass, asdict
from enum import Enum

class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

@dataclass
class Message:
    role: MessageRole
    content: str
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None  # For tool results

@dataclass
class ToolCall:
    id: str
    name: str
    arguments: Dict

class ConversationManager:
    """Manages conversation state and history"""
    
    def __init__(self, max_history: int = 50):
        self.messages: List[Message] = []
        self.max_history = max_history
    
    def add_message(self, message: Message):
        self.messages.append(message)
        self._trim_history()
    
    def _trim_history(self):
        """Keep only recent messages within context limit"""
        if len(self.messages) > self.max_history:
            # Keep system message if present
            system_msgs = [m for m in self.messages if m.role == MessageRole.SYSTEM]
            other_msgs = [m for m in self.messages if m.role != MessageRole.SYSTEM]
            self.messages = system_msgs + other_msgs[-self.max_history:]
    
    def get_messages_for_api(self) -> List[Dict]:
        """Convert messages to API format"""
        api_messages = []
        for msg in self.messages:
            msg_dict = {"role": msg.role.value, "content": msg.content}
            if msg.tool_calls:
                msg_dict["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                msg_dict["tool_call_id"] = msg.tool_call_id
            if msg.name:
                msg_dict["name"] = msg.name
            api_messages.append(msg_dict)
        return api_messages


class ToolRegistry:
    """Registry for available tools/functions"""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.schemas: List[Dict] = []
    
    def register(self, name: str, func: Callable, schema: Dict):
        """Register a tool with its schema"""
        self.tools[name] = func
        self.schemas.append(schema)
    
    def execute(self, tool_call: ToolCall) -> str:
        """Execute a tool and return result as string"""
        if tool_call.name not in self.tools:
            return f"Error: Tool '{tool_call.name}' not found"
        
        try:
            func = self.tools[tool_call.name]
            result = func(**tool_call.arguments)
            return json.dumps(result) if not isinstance(result, str) else result
        except Exception as e:
            return f"Error executing {tool_call.name}: {str(e)}"


class LLMClient:
    """Handles communication with LLM API"""
    
    def __init__(self, api_key: str, model: str = "gpt-4", base_url: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://api.openai.com/v1"
    
    def chat_completion(
        self, 
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> Dict:
        """Non-streaming completion"""
        import requests
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream
        }
        
        if tools:
            payload["tools"] = tools
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def chat_completion_stream(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None
    ) -> Generator[Dict, None, None]:
        """Streaming completion"""
        import requests
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True
        }
        
        if tools:
            payload["tools"] = tools
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            stream=True
        )
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    try:
                        yield json.loads(data)
                    except json.JSONDecodeError:
                        continue


class AgentLoop:
    """Main agent orchestration loop"""
    
    def __init__(
        self,
        llm_client: LLMClient,
        tool_registry: ToolRegistry,
        conversation_manager: ConversationManager,
        max_iterations: int = 10
    ):
        self.llm = llm_client
        self.tools = tool_registry
        self.conversation = conversation_manager
        self.max_iterations = max_iterations
    
    def run(self, user_message: str, stream: bool = False) -> Generator[str, None, None]:
        """Main agent loop - handles tool calling automatically"""
        
        # Add user message
        self.conversation.add_message(
            Message(role=MessageRole.USER, content=user_message)
        )
        
        iteration = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            
            # Get messages for API
            api_messages = self.conversation.get_messages_for_api()
            tool_schemas = self.tools.schemas if self.tools.schemas else None
            
            if stream and iteration == 1:  # Only stream final response
                # Streaming response
                accumulated_content = ""
                accumulated_tool_calls = []
                
                for chunk in self.llm.chat_completion_stream(
                    api_messages, 
                    tools=tool_schemas
                ):
                    delta = chunk.get('choices', [{}])[0].get('delta', {})
                    
                    # Stream content tokens
                    if 'content' in delta and delta['content']:
                        content = delta['content']
                        accumulated_content += content
                        yield content
                    
                    # Accumulate tool calls
                    if 'tool_calls' in delta:
                        # Handle tool call accumulation (simplified)
                        accumulated_tool_calls.extend(delta['tool_calls'])
                
                # Process complete response
                if accumulated_tool_calls:
                    # Tool calls present - don't return yet
                    self._handle_tool_calls(accumulated_tool_calls)
                    continue  # Continue loop for tool execution
                else:
                    # Final response - save and return
                    self.conversation.add_message(
                        Message(role=MessageRole.ASSISTANT, content=accumulated_content)
                    )
                    break
            else:
                # Non-streaming or tool execution round
                response = self.llm.chat_completion(
                    api_messages,
                    tools=tool_schemas,
                    stream=False
                )
                
                choice = response['choices'][0]
                message = choice['message']
                
                # Check for tool calls
                if message.get('tool_calls'):
                    # Execute tools and continue loop
                    self._handle_tool_calls_response(message)
                else:
                    # Final response
                    content = message.get('content', '')
                    self.conversation.add_message(
                        Message(role=MessageRole.ASSISTANT, content=content)
                    )
                    if not stream:
                        yield content
                    break
        
        if iteration >= self.max_iterations:
            yield "\n[Max iterations reached]"
    
    def _handle_tool_calls_response(self, message: Dict):
        """Handle tool calls from API response"""
        
        # Save assistant message with tool calls
        self.conversation.add_message(
            Message(
                role=MessageRole.ASSISTANT,
                content=message.get('content', ''),
                tool_calls=message['tool_calls']
            )
        )
        
        # Execute each tool
        for tool_call in message['tool_calls']:
            tool_call_obj = ToolCall(
                id=tool_call['id'],
                name=tool_call['function']['name'],
                arguments=json.loads(tool_call['function']['arguments'])
            )
            
            # Execute tool
            result = self.tools.execute(tool_call_obj)
            
            # Add tool result to conversation
            self.conversation.add_message(
                Message(
                    role=MessageRole.TOOL,
                    content=result,
                    tool_call_id=tool_call['id'],
                    name=tool_call_obj.name
                )
            )


# Example Usage
def main():
    # Initialize components
    llm = LLMClient(api_key="your-api-key", model="gpt-4")
    tools = ToolRegistry()
    conversation = ConversationManager()
    
    # Register tools
    def get_weather(location: str) -> Dict:
        """Get weather for a location"""
        # Simulate API call
        return {"location": location, "temperature": 72, "condition": "sunny"}
    
    tools.register(
        name="get_weather",
        func=get_weather,
        schema={
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name"
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    )
    
    # Add system message
    conversation.add_message(
        Message(
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant with access to tools."
        )
    )
    
    # Create agent
    agent = AgentLoop(llm, tools, conversation)
    
    # Run with streaming
    print("User: What's the weather in San Francisco?")
    print("Assistant: ", end="", flush=True)
    
    for chunk in agent.run("What's the weather in San Francisco?", stream=True):
        print(chunk, end="", flush=True)
    print("\n")


if __name__ == "__main__":
    main()
```

## Detailed Flow Diagram

### Standard Request Flow:
```
1. User Input
   ↓
2. Add to Conversation History
   ↓
3. Send to LLM API (with tool schemas)
   ↓
4. Receive Response
   ↓
5. Check Response Type:
   ├─→ Tool Call? 
   │   ├─→ Execute Tool(s)
   │   ├─→ Add Tool Results to History
   │   └─→ LOOP back to step 3
   │
   └─→ Text Response?
       ├─→ Add to History
       └─→ Return to User
```

### Streaming Special Case:
```
1. User Input
   ↓
2. Start Streaming Request
   ↓
3. For each chunk:
   ├─→ Content delta? → Stream to user immediately
   ├─→ Tool call delta? → Accumulate
   └─→ Done?
       ├─→ Has tool calls? → Execute & restart (non-streaming)
       └─→ Text only? → Complete
```

## Key Implementation Details

### 1. **Tool Call Accumulation (Streaming)**
When streaming, tool calls come in chunks and must be accumulated:

```python
def accumulate_tool_calls(chunks: List[Dict]) -> List[Dict]:
    """Accumulate tool call deltas from streaming"""
    tool_calls_map = {}
    
    for chunk in chunks:
        delta = chunk.get('delta', {})
        if 'tool_calls' in delta:
            for tc in delta['tool_calls']:
                idx = tc.get('index', 0)
                if idx not in tool_calls_map:
                    tool_calls_map[idx] = {
                        'id': '',
                        'type': 'function',
                        'function': {'name': '', 'arguments': ''}
                    }
                
                if 'id' in tc:
                    tool_calls_map[idx]['id'] = tc['id']
                if 'function' in tc:
                    if 'name' in tc['function']:
                        tool_calls_map[idx]['function']['name'] = tc['function']['name']
                    if 'arguments' in tc['function']:
                        tool_calls_map[idx]['function']['arguments'] += tc['function']['arguments']
    
    return list(tool_calls_map.values())
```

### 2. **Context Window Management**
```python
def estimate_tokens(text: str) -> int:
    """Rough token estimation"""
    return len(text) // 4

def trim_conversation(messages: List[Message], max_tokens: int = 4000) -> List[Message]:
    """Trim conversation to fit context window"""
    system_msgs = [m for m in messages if m.role == MessageRole.SYSTEM]
    other_msgs = [m for m in messages if m.role != MessageRole.SYSTEM]
    
    total_tokens = sum(estimate_tokens(m.content) for m in system_msgs)
    trimmed = []
    
    for msg in reversed(other_msgs):
        msg_tokens = estimate_tokens(msg.content)
        if total_tokens + msg_tokens > max_tokens:
            break
        trimmed.insert(0, msg)
        total_tokens += msg_tokens
    
    return system_msgs + trimmed
```

### 3. **Error Handling & Retries**
```python
import time
from typing import Optional

class RetryableError(Exception):
    pass

def with_retry(
    func: Callable,
    max_retries: int = 3,
    backoff_factor: float = 2.0
):
    """Retry wrapper for API calls"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = backoff_factor ** attempt
            time.sleep(wait_time)
```

### 4. **Conversation Persistence**
```python
import json
from pathlib import Path

class PersistentConversationManager(ConversationManager):
    """Conversation manager with file persistence"""
    
    def __init__(self, save_path: str, **kwargs):
        super().__init__(**kwargs)
        self.save_path = Path(save_path)
        self.load()
    
    def load(self):
        """Load conversation from file"""
        if self.save_path.exists():
            with open(self.save_path, 'r') as f:
                data = json.load(f)
                self.messages = [
                    Message(
                        role=MessageRole(m['role']),
                        content=m['content'],
                        tool_calls=m.get('tool_calls'),
                        tool_call_id=m.get('tool_call_id'),
                        name=m.get('name')
                    )
                    for m in data
                ]
    
    def save(self):
        """Save conversation to file"""
        with open(self.save_path, 'w') as f:
            data = [
                {
                    'role': m.role.value,
                    'content': m.content,
                    'tool_calls': m.tool_calls,
                    'tool_call_id': m.tool_call_id,
                    'name': m.name
                }
                for m in self.messages
            ]
            json.dump(data, f, indent=2)
    
    def add_message(self, message: Message):
        super().add_message(message)
        self.save()
```

## MVP Architecture Summary

**Minimum components needed:**
1. **Message storage** (list/dict)
2. **HTTP client** for API calls
3. **Tool registry** (dict of functions)
4. **Main loop** with tool call detection
5. **Basic streaming handler**

**Flow states:**
- `WAITING`: Ready for input
- `CALLING_LLM`: API request in flight
- `EXECUTING_TOOLS`: Running functions
- `STREAMING`: Sending response chunks
- `COMPLETE`: Response finished

This architecture is production-ready for local use and can be extended with:
- Multiple conversation sessions
- Token counting and cost tracking
- Async support for parallel tool execution
- Vector database for RAG
- Web UI or CLI interface

Would you like me to elaborate on any specific component or add features like parallel tool execution, async support, or specific LLM provider integrations?

---

## 👤 You ##

Perfect this was the starting point I looked for. Now please think with me. I want this to be made fully modular, and in a way that adheres to functional paradigm. 
I will describe few things I want in a specific way, and then few ideas how I imagine modularity:
A separate provider module is needed. Apart from the core provider handling, the provider itself is a module (like a plugin users may contribute to). Each provider have a different internal structure and it's better to keep this intact, and use it as it is, for the next message (an example of provider specific thing is the way GPT-5 requires reasoning messages having an id, along with the id required on the next message). However, thinking about modularity, there may be a module that strips old messages out. For this reason, there could be a conversion function in the provider plugin, that will convert the messages to a compatibilit format, for common transformation, and then convert back. Similar, but one-way conversion could be for representation. Thinking about functional paradigm, a pure function could be part of the provider module (and the plugin) that processes the chunks received (input is the message history, and chunk, output is new message history, in an enhanced version it input and output could also include an optional incomplete message, or a more universal meta state - any information that is bot part of the actual message history). Modularity should also be extended to the configuration. Providers may add specific configuration keys (like Api keys or other way of authentication), but for example let's say we want to support web search with a model for specific provider: It would add configuration option for the model, would add a checkbox to the UI, would add something to the body, and additional processing to preserve citations (so may need to alter the provider chunk processing), need to alter the presentation conversion functions too (display citations). We are not talkng about the UI yet, just how the core architecturw could be made so that it's fully extensible.

---

## Assistant · *Claude 4 Sonnet* ##

Excellent! Let's design a fully modular, functional architecture. I'll break this down into layers with clear separation of concerns.

## Core Architecture: Functional & Modular Design

### 1. Core Type System (Immutable Data Structures)

```python
from typing import Protocol, Callable, Any, Optional, List, Dict, Tuple
from dataclasses import dataclass, field, replace
from abc import abstractmethod
import json

# ============================================================================
# Core Immutable Data Types
# ============================================================================

@dataclass(frozen=True)
class Message:
    """Universal message format - used internally"""
    role: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def with_metadata(self, **kwargs) -> 'Message':
        """Return new message with updated metadata"""
        new_metadata = {**self.metadata, **kwargs}
        return replace(self, metadata=new_metadata)


@dataclass(frozen=True)
class ToolCall:
    """Universal tool call representation"""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass(frozen=True)
class ToolResult:
    """Universal tool result representation"""
    tool_call_id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConversationState:
    """Immutable conversation state"""
    messages: Tuple[Message, ...] = field(default_factory=tuple)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, message: Message) -> 'ConversationState':
        """Return new state with added message"""
        return replace(self, messages=self.messages + (message,))
    
    def with_metadata(self, **kwargs) -> 'ConversationState':
        """Return new state with updated metadata"""
        new_metadata = {**self.metadata, **kwargs}
        return replace(self, metadata=new_metadata)


@dataclass(frozen=True)
class StreamChunk:
    """Universal streaming chunk"""
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_final: bool = False


@dataclass(frozen=True)
class ProcessingContext:
    """Context passed through processing pipeline"""
    conversation: ConversationState
    incomplete_message: Optional[Dict[str, Any]] = None
    meta_state: Dict[str, Any] = field(default_factory=dict)
    
    def update_conversation(self, conversation: ConversationState) -> 'ProcessingContext':
        return replace(self, conversation=conversation)
    
    def update_meta(self, **kwargs) -> 'ProcessingContext':
        new_meta = {**self.meta_state, **kwargs}
        return replace(self, meta_state=new_meta)


# ============================================================================
# Provider Protocol - Plugin Interface
# ============================================================================

class ProviderProtocol(Protocol):
    """Protocol that all provider plugins must implement"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier"""
        ...
    
    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """
        Returns JSON schema for provider-specific configuration
        Example: {"api_key": {"type": "string", "required": True}}
        """
        ...
    
    @abstractmethod
    def to_native_messages(self, messages: Tuple[Message, ...]) -> List[Dict[str, Any]]:
        """Convert universal messages to provider-specific format"""
        ...
    
    @abstractmethod
    def from_native_messages(self, native_messages: List[Dict[str, Any]]) -> Tuple[Message, ...]:
        """Convert provider-specific messages to universal format"""
        ...
    
    @abstractmethod
    def to_native_request_body(
        self, 
        messages: List[Dict[str, Any]], 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build provider-specific request body"""
        ...
    
    @abstractmethod
    def process_chunk(
        self, 
        context: ProcessingContext, 
        native_chunk: Dict[str, Any]
    ) -> ProcessingContext:
        """
        Pure function: Process a streaming chunk
        Input: current context + native chunk
        Output: new context with updated state
        """
        ...
    
    @abstractmethod
    def process_response(
        self,
        context: ProcessingContext,
        native_response: Dict[str, Any]
    ) -> ProcessingContext:
        """Process complete (non-streaming) response"""
        ...
    
    @abstractmethod
    def to_display_format(self, message: Message) -> Dict[str, Any]:
        """Convert message to display/representation format (one-way)"""
        ...


# ============================================================================
# Feature Plugin Protocol
# ============================================================================

class FeatureProtocol(Protocol):
    """Protocol for feature plugins (like web search, citations, etc.)"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Feature identifier"""
        ...
    
    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """Additional configuration this feature needs"""
        ...
    
    @abstractmethod
    def get_ui_elements(self) -> List[Dict[str, Any]]:
        """
        UI elements this feature adds
        Example: [{"type": "checkbox", "key": "enable_search", "label": "Enable Web Search"}]
        """
        ...
    
    @abstractmethod
    def modify_request_body(
        self, 
        body: Dict[str, Any], 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Pure function: Modify request body with feature-specific additions
        """
        ...
    
    @abstractmethod
    def process_chunk(
        self,
        context: ProcessingContext,
        chunk: StreamChunk
    ) -> ProcessingContext:
        """
        Pure function: Process chunk with feature-specific logic
        Can be composed with provider's process_chunk
        """
        ...
    
    @abstractmethod
    def modify_display_format(
        self,
        display_data: Dict[str, Any],
        message: Message
    ) -> Dict[str, Any]:
        """
        Pure function: Enhance display format with feature-specific data
        """
        ...
    
    @abstractmethod
    def transform_to_compatibility(self, message: Message) -> Message:
        """Transform message before common operations (like trimming)"""
        ...
    
    @abstractmethod
    def transform_from_compatibility(self, message: Message) -> Message:
        """Transform message back after common operations"""
        ...


# ============================================================================
# Configuration System
# ============================================================================

@dataclass(frozen=True)
class ConfigSchema:
    """Merged configuration schema from multiple sources"""
    fields: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def merge(self, other: 'ConfigSchema') -> 'ConfigSchema':
        """Merge two schemas"""
        merged_fields = {**self.fields, **other.fields}
        return ConfigSchema(fields=merged_fields)


@dataclass(frozen=True)
class Config:
    """Immutable configuration"""
    values: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)
    
    def merge(self, other: 'Config') -> 'Config':
        merged = {**self.values, **other.values}
        return Config(values=merged)


class ConfigBuilder:
    """Functional builder for configuration"""
    
    @staticmethod
    def build_schema(
        provider: ProviderProtocol,
        features: List[FeatureProtocol]
    ) -> ConfigSchema:
        """Pure function: Build merged configuration schema"""
        schema = ConfigSchema(fields=provider.get_config_schema())
        
        for feature in features:
            feature_schema = ConfigSchema(fields=feature.get_config_schema())
            schema = schema.merge(feature_schema)
        
        return schema
    
    @staticmethod
    def validate_config(config: Config, schema: ConfigSchema) -> Tuple[bool, List[str]]:
        """Pure function: Validate configuration against schema"""
        errors = []
        
        for field_name, field_spec in schema.fields.items():
            if field_spec.get('required', False):
                if field_name not in config.values:
                    errors.append(f"Required field '{field_name}' is missing")
        
        return len(errors) == 0, errors


# ============================================================================
# Message Transformation Pipeline
# ============================================================================

# Type aliases for pure functions
MessageTransform = Callable[[Message], Message]
MessagesTransform = Callable[[Tuple[Message, ...]], Tuple[Message, ...]]
ContextTransform = Callable[[ProcessingContext], ProcessingContext]


class MessageTransformer:
    """Pure functional transformations on messages"""
    
    @staticmethod
    def to_compatibility(
        messages: Tuple[Message, ...],
        features: List[FeatureProtocol]
    ) -> Tuple[Message, ...]:
        """
        Pure function: Convert to compatibility format through feature chain
        Each feature can transform messages for common operations
        """
        result = messages
        for feature in features:
            result = tuple(feature.transform_to_compatibility(msg) for msg in result)
        return result
    
    @staticmethod
    def from_compatibility(
        messages: Tuple[Message, ...],
        features: List[FeatureProtocol]
    ) -> Tuple[Message, ...]:
        """
        Pure function: Convert back from compatibility format
        Apply in reverse order
        """
        result = messages
        for feature in reversed(features):
            result = tuple(feature.transform_from_compatibility(msg) for msg in result)
        return result
    
    @staticmethod
    def compose_transforms(*transforms: MessageTransform) -> MessageTransform:
        """Compose multiple message transformations"""
        def composed(message: Message) -> Message:
            result = message
            for transform in transforms:
                result = transform(result)
            return result
        return composed
    
    @staticmethod
    def apply_to_all(transform: MessageTransform) -> MessagesTransform:
        """Lift a single message transform to operate on all messages"""
        def transformed(messages: Tuple[Message, ...]) -> Tuple[Message, ...]:
            return tuple(transform(msg) for msg in messages)
        return transformed


# ============================================================================
# Common Message Operations (work on compatibility format)
# ============================================================================

class MessageOperations:
    """Common operations that work on compatibility format"""
    
    @staticmethod
    def trim_by_count(max_count: int, keep_system: bool = True) -> MessagesTransform:
        """Pure function: Trim messages to maximum count"""
        def trim(messages: Tuple[Message, ...]) -> Tuple[Message, ...]:
            if keep_system:
                system_msgs = tuple(m for m in messages if m.role == "system")
                other_msgs = tuple(m for m in messages if m.role != "system")
                trimmed_others = other_msgs[-max_count:] if max_count > 0 else ()
                return system_msgs + trimmed_others
            else:
                return messages[-max_count:] if max_count > 0 else ()
        return trim
    
    @staticmethod
    def trim_by_tokens(
        max_tokens: int,
        token_counter: Callable[[str], int],
        keep_system: bool = True
    ) -> MessagesTransform:
        """Pure function: Trim messages to fit token budget"""
        def trim(messages: Tuple[Message, ...]) -> Tuple[Message, ...]:
            system_msgs = tuple(m for m in messages if m.role == "system")
            other_msgs = tuple(m for m in messages if m.role != "system")
            
            # Count system tokens
            system_tokens = sum(token_counter(m.content) for m in system_msgs)
            remaining_budget = max_tokens - system_tokens
            
            # Add messages from end while budget allows
            result = []
            for msg in reversed(other_msgs):
                msg_tokens = token_counter(msg.content)
                if msg_tokens <= remaining_budget:
                    result.insert(0, msg)
                    remaining_budget -= msg_tokens
                else:
                    break
            
            return system_msgs + tuple(result) if keep_system else tuple(result)
        return trim
    
    @staticmethod
    def filter_by_role(*roles: str) -> MessagesTransform:
        """Pure function: Keep only messages with specific roles"""
        def filter_msgs(messages: Tuple[Message, ...]) -> Tuple[Message, ...]:
            return tuple(m for m in messages if m.role in roles)
        return filter_msgs


# ============================================================================
# Processing Pipeline - Composable Functions
# ============================================================================

class ProcessingPipeline:
    """Compose processing functions into a pipeline"""
    
    @staticmethod
    def compose(*transforms: ContextTransform) -> ContextTransform:
        """Compose context transformations"""
        def composed(context: ProcessingContext) -> ProcessingContext:
            result = context
            for transform in transforms:
                result = transform(result)
            return result
        return composed
    
    @staticmethod
    def create_chunk_processor(
        provider: ProviderProtocol,
        features: List[FeatureProtocol]
    ) -> Callable[[ProcessingContext, Dict[str, Any]], ProcessingContext]:
        """
        Create a composed chunk processor
        Provider processes first, then features layer on top
        """
        def process_chunk(context: ProcessingContext, native_chunk: Dict[str, Any]) -> ProcessingContext:
            # Provider processes native chunk
            ctx = provider.process_chunk(context, native_chunk)
            
            # Features process the universal chunk
            # (features need to extract chunk from context)
            for feature in features:
                # Extract the last chunk info from context if needed
                # This is simplified - real implementation would pass StreamChunk
                ctx = feature.process_chunk(ctx, StreamChunk())
            
            return ctx
        
        return process_chunk
    
    @staticmethod
    def create_request_body_builder(
        provider: ProviderProtocol,
        features: List[FeatureProtocol]
    ) -> Callable[[Tuple[Message, ...], Config], Dict[str, Any]]:
        """
        Create a composed request body builder
        """
        def build_body(messages: Tuple[Message, ...], config: Config) -> Dict[str, Any]:
            # Convert to native format
            native_messages = provider.to_native_messages(messages)
            
            # Build base body
            body = provider.to_native_request_body(native_messages, config.values)
            
            # Let features modify body
            for feature in features:
                body = feature.modify_request_body(body, config.values)
            
            return body
        
        return build_body


# ============================================================================
# Provider Plugins - Examples
# ============================================================================

class OpenAIProvider:
    """OpenAI provider plugin"""
    
    name = "openai"
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "openai_api_key": {
                "type": "string",
                "required": True,
                "description": "OpenAI API Key"
            },
            "openai_model": {
                "type": "string",
                "required": False,
                "default": "gpt-4",
                "description": "Model name"
            },
            "openai_base_url": {
                "type": "string",
                "required": False,
                "default": "https://api.openai.com/v1",
                "description": "API base URL"
            }
        }
    
    def to_native_messages(self, messages: Tuple[Message, ...]) -> List[Dict[str, Any]]:
        """Convert universal to OpenAI format"""
        native = []
        for msg in messages:
            native_msg = {
                "role": msg.role,
                "content": msg.content
            }
            
            # Add OpenAI-specific fields from metadata
            if "tool_calls" in msg.metadata:
                native_msg["tool_calls"] = msg.metadata["tool_calls"]
            if "tool_call_id" in msg.metadata:
                native_msg["tool_call_id"] = msg.metadata["tool_call_id"]
            if "name" in msg.metadata:
                native_msg["name"] = msg.metadata["name"]
            
            native.append(native_msg)
        
        return native
    
    def from_native_messages(self, native_messages: List[Dict[str, Any]]) -> Tuple[Message, ...]:
        """Convert OpenAI format to universal"""
        messages = []
        for native_msg in native_messages:
            metadata = {}
            
            # Extract OpenAI-specific fields to metadata
            if "tool_calls" in native_msg:
                metadata["tool_calls"] = native_msg["tool_calls"]
            if "tool_call_id" in native_msg:
                metadata["tool_call_id"] = native_msg["tool_call_id"]
            if "name" in native_msg:
                metadata["name"] = native_msg["name"]
            
            msg = Message(
                role=native_msg["role"],
                content=native_msg.get("content", ""),
                metadata=metadata
            )
            messages.append(msg)
        
        return tuple(messages)
    
    def to_native_request_body(
        self,
        messages: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build OpenAI request body"""
        return {
            "model": config.get("openai_model", "gpt-4"),
            "messages": messages,
            "stream": config.get("stream", False)
        }
    
    def process_chunk(
        self,
        context: ProcessingContext,
        native_chunk: Dict[str, Any]
    ) -> ProcessingContext:
        """Process OpenAI streaming chunk"""
        # Extract delta
        delta = native_chunk.get("choices", [{}])[0].get("delta", {})
        
        # Get or create incomplete message from meta state
        incomplete = context.meta_state.get("incomplete_message", {
            "role": "assistant",
            "content": "",
            "tool_calls": {}
        })
        
        # Accumulate content
        if "content" in delta and delta["content"]:
            incomplete["content"] += delta["content"]
        
        # Accumulate tool calls
        if "tool_calls" in delta:
            for tc in delta["tool_calls"]:
                idx = tc.get("index", 0)
                if idx not in incomplete["tool_calls"]:
                    incomplete["tool_calls"][idx] = {
                        "id": "",
                        "type": "function",
                        "function": {"name": "", "arguments": ""}
                    }
                
                if "id" in tc:
                    incomplete["tool_calls"][idx]["id"] = tc["id"]
                if "function" in tc:
                    if "name" in tc["function"]:
                        incomplete["tool_calls"][idx]["function"]["name"] = tc["function"]["name"]
                    if "arguments" in tc["function"]:
                        incomplete["tool_calls"][idx]["function"]["arguments"] += tc["function"]["arguments"]
        
        # Check if final
        finish_reason = native_chunk.get("choices", [{}])[0].get("finish_reason")
        if finish_reason:
            # Complete - create message and add to conversation
            metadata = {}
            if incomplete["tool_calls"]:
                metadata["tool_calls"] = list(incomplete["tool_calls"].values())
            
            message = Message(
                role=incomplete["role"],
                content=incomplete["content"],
                metadata=metadata
            )
            
            new_conversation = context.conversation.add_message(message)
            return context.update_conversation(new_conversation).update_meta(incomplete_message=None)
        else:
            # Still streaming
            return context.update_meta(incomplete_message=incomplete)
    
    def process_response(
        self,
        context: ProcessingContext,
        native_response: Dict[str, Any]
    ) -> ProcessingContext:
        """Process OpenAI complete response"""
        choice = native_response["choices"][0]
        message_data = choice["message"]
        
        metadata = {}
        if "tool_calls" in message_data:
            metadata["tool_calls"] = message_data["tool_calls"]
        
        message = Message(
            role=message_data["role"],
            content=message_data.get("content", ""),
            metadata=metadata
        )
        
        new_conversation = context.conversation.add_message(message)
        return context.update_conversation(new_conversation)
    
    def to_display_format(self, message: Message) -> Dict[str, Any]:
        """Convert to display format"""
        display = {
            "role": message.role,
            "content": message.content,
            "type": "text"
        }
        
        if message.metadata.get("tool_calls"):
            display["type"] = "tool_calls"
            display["tool_calls"] = message.metadata["tool_calls"]
        
        return display


class AnthropicProvider:
    """Anthropic (Claude) provider plugin"""
    
    name = "anthropic"
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "anthropic_api_key": {
                "type": "string",
                "required": True,
                "description": "Anthropic API Key"
            },
            "anthropic_model": {
                "type": "string",
                "required": False,
                "default": "claude-3-5-sonnet-20241022",
                "description": "Model name"
            }
        }
    
    def to_native_messages(self, messages: Tuple[Message, ...]) -> List[Dict[str, Any]]:
        """Convert to Anthropic format - system message separate"""
        native = []
        
        for msg in messages:
            if msg.role == "system":
                continue  # System handled separately in Anthropic
            
            # Anthropic uses different structure for tool results
            if msg.role == "tool":
                native.append({
                    "role": "user",  # Tool results come as user messages
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.metadata.get("tool_call_id"),
                        "content": msg.content
                    }]
                })
            else:
                native.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        return native
    
    def from_native_messages(self, native_messages: List[Dict[str, Any]]) -> Tuple[Message, ...]:
        """Convert from Anthropic format"""
        messages = []
        
        for native_msg in native_messages:
            # Handle different content structures
            content = native_msg.get("content", "")
            metadata = {}
            
            if isinstance(content, list):
                # Complex content structure
                text_content = ""
                for block in content:
                    if block.get("type") == "text":
                        text_content += block.get("text", "")
                    elif block.get("type") == "tool_use":
                        # Store tool use in metadata
                        if "tool_calls" not in metadata:
                            metadata["tool_calls"] = []
                        metadata["tool_calls"].append({
                            "id": block.get("id"),
                            "type": "function",
                            "function": {
                                "name": block.get("name"),
                                "arguments": json.dumps(block.get("input", {}))
                            }
                        })
                content = text_content
            
            messages.append(Message(
                role=native_msg["role"],
                content=content if isinstance(content, str) else "",
                metadata=metadata
            ))
        
        return tuple(messages)
    
    def to_native_request_body(
        self,
        messages: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build Anthropic request body"""
        # Extract system message
        system_message = None
        for msg in messages:
            if msg.get("role") == "system":
                system_message = msg.get("content")
                break
        
        body = {
            "model": config.get("anthropic_model", "claude-3-5-sonnet-20241022"),
            "messages": [m for m in messages if m.get("role") != "system"],
            "max_tokens": config.get("max_tokens", 4096),
            "stream": config.get("stream", False)
        }
        
        if system_message:
            body["system"] = system_message
        
        return body
    
    def process_chunk(
        self,
        context: ProcessingContext,
        native_chunk: Dict[str, Any]
    ) -> ProcessingContext:
        """Process Anthropic streaming chunk"""
        chunk_type = native_chunk.get("type")
        
        incomplete = context.meta_state.get("incomplete_message", {
            "role": "assistant",
            "content": "",
            "tool_uses": []
        })
        
        if chunk_type == "content_block_delta":
            delta = native_chunk.get("delta", {})
            if delta.get("type") == "text_delta":
                incomplete["content"] += delta.get("text", "")
        
        elif chunk_type == "content_block_start":
            block = native_chunk.get("content_block", {})
            if block.get("type") == "tool_use":
                incomplete["tool_uses"].append({
                    "id": block.get("id"),
                    "name": block.get("name"),
                    "input": ""
                })
        
        elif chunk_type == "message_stop":
            # Complete
            metadata = {}
            if incomplete["tool_uses"]:
                metadata["tool_calls"] = [
                    {
                        "id": tu["id"],
                        "type": "function",
                        "function": {
                            "name": tu["name"],
                            "arguments": tu["input"]
                        }
                    }
                    for tu in incomplete["tool_uses"]
                ]
            
            message = Message(
                role="assistant",
                content=incomplete["content"],
                metadata=metadata
            )
            
            new_conversation = context.conversation.add_message(message)
            return context.update_conversation(new_conversation).update_meta(incomplete_message=None)
        
        return context.update_meta(incomplete_message=incomplete)
    
    def process_response(
        self,
        context: ProcessingContext,
        native_response: Dict[str, Any]
    ) -> ProcessingContext:
        """Process Anthropic complete response"""
        content_blocks = native_response.get("content", [])
        
        text_content = ""
        tool_uses = []
        
        for block in content_blocks:
            if block.get("type") == "text":
                text_content += block.get("text", "")
            elif block.get("type") == "tool_use":
                tool_uses.append(block)
        
        metadata = {}
        if tool_uses:
            metadata["tool_calls"] = [
                {
                    "id": tu["id"],
                    "type": "function",
                    "function": {
                        "name": tu["name"],
                        "arguments": json.dumps(tu["input"])
                    }
                }
                for tu in tool_uses
            ]
        
        message = Message(
            role="assistant",
            content=text_content,
            metadata=metadata
        )
        
        new_conversation = context.conversation.add_message(message)
        return context.update_conversation(new_conversation)
    
    def to_display_format(self, message: Message) -> Dict[str, Any]:
        """Convert to display format"""
        return {
            "role": message.role,
            "content": message.content,
            "type": "text" if not message.metadata.get("tool_calls") else "tool_calls",
            "tool_calls": message.metadata.get("tool_calls", [])
        }


# ============================================================================
# Feature Plugins - Examples
# ============================================================================

class WebSearchFeature:
    """Web search feature plugin"""
    
    name = "web_search"
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "web_search_enabled": {
                "type": "boolean",
                "required": False,
                "default": False,
                "description": "Enable web search"
            },
            "web_search_model": {
                "type": "string",
                "required": False,
                "default": None,
                "description": "Model to use for web search (provider-specific)"
            }
        }
    
    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "checkbox",
                "key": "web_search_enabled",
                "label": "Enable Web Search",
                "section": "features"
            },
            {
                "type": "text",
                "key": "web_search_model",
                "label": "Search Model",
                "section": "features",
                "condition": {"web_search_enabled": True}
            }
        ]
    
    def modify_request_body(
        self,
        body: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add web search parameters to request"""
        if config.get("web_search_enabled"):
            # This is provider-specific, but shows the concept
            new_body = {**body}
            
            # For OpenAI-style
            if "model" in body and config.get("web_search_model"):
                new_body["model"] = config["web_search_model"]
            
            # Could add other search-specific parameters
            new_body["search_enabled"] = True
            
            return new_body
        
        return body
    
    def process_chunk(
        self,
        context: ProcessingContext,
        chunk: StreamChunk
    ) -> ProcessingContext:
        """Extract and store citation information"""
        if not chunk.metadata:
            return context
        
        # Look for citations in metadata
        citations = chunk.metadata.get("citations", [])
        if citations:
            # Store citations in meta state for later use
            existing_citations = context.meta_state.get("citations", [])
            new_citations = existing_citations + citations
            return context.update_meta(citations=new_citations)
        
        return context
    
    def modify_display_format(
        self,
        display_data: Dict[str, Any],
        message: Message
    ) -> Dict[str, Any]:
        """Add citations to display format"""
        citations = message.metadata.get("citations", [])
        
        if citations:
            display_data["citations"] = citations
            display_data["has_citations"] = True
        
        return display_data
    
    def transform_to_compatibility(self, message: Message) -> Message:
        """
        Before common operations (like trimming), we might want to
        preserve citations differently or strip them temporarily
        """
        if "citations" in message.metadata:
            # Store citations in a special format for preservation
            preserved = message.metadata.copy()
            preserved["_preserved_citations"] = preserved.pop("citations")
            return replace(message, metadata=preserved)
        return message
    
    def transform_from_compatibility(self, message: Message) -> Message:
        """Restore citations after common operations"""
        if "_preserved_citations" in message.metadata:
            restored = message.metadata.copy()
            restored["citations"] = restored.pop("_preserved_citations")
            return replace(message, metadata=restored)
        return message


class ReasoningTracesFeature:
    """
    Feature to handle reasoning traces (like o1 models or GPT-5 reasoning)
    Shows how to handle provider-specific extensions
    """
    
    name = "reasoning_traces"
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "show_reasoning": {
                "type": "boolean",
                "required": False,
                "default": False,
                "description": "Show reasoning traces"
            }
        }
    
    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "checkbox",
                "key": "show_reasoning",
                "label": "Show Reasoning Traces",
                "section": "features"
            }
        ]
    
    def modify_request_body(
        self,
        body: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enable reasoning in request if supported"""
        if config.get("show_reasoning"):
            # This might be provider-specific
            new_body = {**body}
            new_body["reasoning"] = True
            return new_body
        return body
    
    def process_chunk(
        self,
        context: ProcessingContext,
        chunk: StreamChunk
    ) -> ProcessingContext:
        """
        Handle reasoning trace chunks
        For GPT-5 style reasoning that needs message IDs
        """
        if chunk.metadata.get("type") == "reasoning":
            # Store reasoning separately
            reasoning_id = chunk.metadata.get("reasoning_id")
            reasoning_content = chunk.content or ""
            
            # Accumulate reasoning
            reasoning_traces = context.meta_state.get("reasoning_traces", {})
            if reasoning_id not in reasoning_traces:
                reasoning_traces[reasoning_id] = ""
            reasoning_traces[reasoning_id] += reasoning_content
            
            return context.update_meta(reasoning_traces=reasoning_traces)
        
        return context
    
    def modify_display_format(
        self,
        display_data: Dict[str, Any],
        message: Message
    ) -> Dict[str, Any]:
        """Add reasoning traces to display"""
        if "reasoning_trace" in message.metadata:
            display_data["reasoning"] = message.metadata["reasoning_trace"]
            display_data["has_reasoning"] = True
        
        return display_data
    
    def transform_to_compatibility(self, message: Message) -> Message:
        """Strip reasoning for common operations"""
        if "reasoning_trace" in message.metadata:
            # Strip reasoning when doing operations like trimming
            # (reasoning is expensive in tokens)
            cleaned = {k: v for k, v in message.metadata.items() 
                      if k != "reasoning_trace"}
            return replace(message, metadata=cleaned)
        return message
    
    def transform_from_compatibility(self, message: Message) -> Message:
        """Reasoning traces can't be restored after common ops"""
        # In a real implementation, you might store them elsewhere
        return message


# ============================================================================
# Provider Registry
# ============================================================================

class ProviderRegistry:
    """Registry for provider plugins"""
    
    def __init__(self):
        self.providers: Dict[str, ProviderProtocol] = {}
    
    def register(self, provider: ProviderProtocol):
        self.providers[provider.name] = provider
    
    def get(self, name: str) -> Optional[ProviderProtocol]:
        return self.providers.get(name)
    
    def list_providers(self) -> List[str]:
        return list(self.providers.keys())


class FeatureRegistry:
    """Registry for feature plugins"""
    
    def __init__(self):
        self.features: Dict[str, FeatureProtocol] = {}
    
    def register(self, feature: FeatureProtocol):
        self.features[feature.name] = feature
    
    def get(self, name: str) -> Optional[FeatureProtocol]:
        return self.features.get(name)
    
    def get_enabled_features(self, config: Config) -> List[FeatureProtocol]:
        """Get list of enabled features based on config"""
        enabled = []
        for feature in self.features.values():
            # Check if feature is enabled (convention: feature_name_enabled)
            if config.get(f"{feature.name}_enabled", False):
                enabled.append(feature)
        return enabled
    
    def list_features(self) -> List[str]:
        return list(self.features.keys())


```

### 2. Usage Example - Putting It All Together

```python
# ============================================================================
# Example: Using the Modular System
# ============================================================================

def example_usage():
    """Example of how to use the modular system"""
    
    # Setup registries
    provider_registry = ProviderRegistry()
    provider_registry.register(OpenAIProvider())
    provider_registry.register(AnthropicProvider())
    
    feature_registry = FeatureRegistry()
    feature_registry.register(WebSearchFeature())
    feature_registry.register(ReasoningTracesFeature())
    
    # Build configuration
    config = Config(values={
        "openai_api_key": "sk-...",
        "openai_model": "gpt-4",
        "web_search_enabled": True,
        "web_search_model": "gpt-4-search",
        "show_reasoning": False,
        "stream": True
    })
    
    # Get provider and features
    provider = provider_registry.get("openai")
    enabled_features = feature_registry.get_enabled_features(config)
    
    # Build configuration schema
    schema = ConfigBuilder.build_schema(provider, enabled_features)
    is_valid, errors = ConfigBuilder.validate_config(config, schema)
    
    if not is_valid:
        print(f"Config errors: {errors}")
        return
    
    # Initialize conversation
    conversation = ConversationState()
    conversation = conversation.add_message(
        Message(role="system", content="You are a helpful assistant.")
    )
    conversation = conversation.add_message(
        Message(role="user", content="What's the weather in Paris?")
    )
    
    # Apply common operations (trim by count)
    # First convert to compatibility format
    compat_messages = MessageTransformer.to_compatibility(
        conversation.messages,
        enabled_features
    )
    
    # Apply trimming
    trim_fn = MessageOperations.trim_by_count(max_count=10, keep_system=True)
    trimmed_messages = trim_fn(compat_messages)
    
    # Convert back from compatibility format
    final_messages = MessageTransformer.from_compatibility(
        trimmed_messages,
        enabled_features
    )
    
    conversation = replace(conversation, messages=final_messages)
    
    # Build request
    body_builder = ProcessingPipeline.create_request_body_builder(
        provider,
        enabled_features
    )
    
    request_body = body_builder(conversation.messages, config)
    print(f"Request body: {json.dumps(request_body, indent=2)}")
    
    # Process streaming response (simulated)
    context = ProcessingContext(conversation=conversation)
    
    # Create chunk processor
    chunk_processor = ProcessingPipeline.create_chunk_processor(
        provider,
        enabled_features
    )
    
    # Simulate processing chunks
    mock_chunks = [
        {"choices": [{"delta": {"content": "The "}, "finish_reason": None}]},
        {"choices": [{"delta": {"content": "weather "}, "finish_reason": None}]},
        {"choices": [{"delta": {"content": "is sunny"}, "finish_reason": "stop"}]}
    ]
    
    for chunk in mock_chunks:
        context = chunk_processor(context, chunk)
        
        # Access incomplete message for streaming output
        if "incomplete_message" in context.meta_state:
            incomplete = context.meta_state["incomplete_message"]
            print(f"Streaming: {incomplete['content']}", end="", flush=True)
    
    print("\n")
    
    # Final conversation state
    print(f"Final messages: {len(context.conversation.messages)}")
    
    # Convert to display format
    for msg in context.conversation.messages:
        display = provider.to_display_format(msg)
        
        # Let features enhance display
        for feature in enabled_features:
            display = feature.modify_display_format(display, msg)
        
        print(f"Display: {json.dumps(display, indent=2)}")


if __name__ == "__main__":
    example_usage()
```

## Key Design Principles Achieved

### 1. **Modularity**
- Providers are plugins implementing `ProviderProtocol`
- Features are plugins implementing `FeatureProtocol`
- Both can be registered and composed dynamically

### 2. **Functional Paradigm**
- Immutable data structures (`@dataclass(frozen=True)`)
- Pure functions for transformations
- Function composition via pipelines
- No side effects in core logic

### 3. **Bidirectional Conversion**
- `to_native_messages` / `from_native_messages` for provider format
- `transform_to_compatibility` / `transform_from_compatibility` for features
- `to_display_format` for one-way representation

### 4. **Extensible Configuration**
- Providers contribute config schema
- Features contribute additional schema
- Merged into single schema
- UI elements generated from feature definitions

### 5. **Composable Processing**
- Provider processes native chunks first
- Features layer additional processing
- Pure functions can be composed in pipelines
- Context passed immutably through chain

This architecture allows for:
- Adding new providers without touching core
- Adding new features that modify any provider
- Common operations work on compatible format
- Provider-specific quirks stay contained
- Full functional programming style maintained

Would you like me to elaborate on any specific part or add more features like parallel tool execution, caching layers, or error handling patterns?

---

## 👤 You ##

Feature plugins may affect one specific provider, or select providers, or all providers, similarly they may affect specific models with specific features. This could be some with Protocols, so that a feature may be applied with a provider or model implementing a specific protocol. A single feature plugin may contain different processing for different models or providers implementing different protocols. The provider should be able to tell which models belong to which protocols (an API call may be required though). The protocol for the provider could be a fixed list.

---

## Assistant · *Claude 4 Sonnet* ##

Excellent insight! Let's extend the architecture with a protocol-based capability system where features can target specific protocols that providers/models implement.

## Protocol-Based Feature System

```python
from typing import Protocol, List, Dict, Set, Optional, Callable, Any, Type, Union
from dataclasses import dataclass, field, replace
from abc import abstractmethod
from enum import Enum
import json

# ============================================================================
# Protocol (Capability) System
# ============================================================================

class ProviderCapability(str, Enum):
    """Standard provider capabilities/protocols"""
    # Basic capabilities
    TEXT_GENERATION = "text_generation"
    STREAMING = "streaming"
    
    # Tool/Function capabilities
    TOOL_CALLING = "tool_calling"
    PARALLEL_TOOL_CALLING = "parallel_tool_calling"
    
    # Content capabilities
    VISION = "vision"
    IMAGE_GENERATION = "image_generation"
    AUDIO_INPUT = "audio_input"
    AUDIO_OUTPUT = "audio_output"
    
    # Advanced reasoning
    REASONING_TRACES = "reasoning_traces"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    
    # Search and grounding
    WEB_SEARCH = "web_search"
    GROUNDING = "grounding"
    CITATIONS = "citations"
    
    # Message handling
    SYSTEM_MESSAGES = "system_messages"
    MULTI_TURN = "multi_turn"
    
    # Structured output
    JSON_MODE = "json_mode"
    STRUCTURED_OUTPUT = "structured_output"
    
    # Context
    LARGE_CONTEXT = "large_context"  # >32k tokens
    EXTENDED_CONTEXT = "extended_context"  # >128k tokens


@dataclass(frozen=True)
class ModelCapabilities:
    """Capabilities for a specific model"""
    model_id: str
    capabilities: Set[ProviderCapability]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def supports(self, capability: ProviderCapability) -> bool:
        """Check if model supports a capability"""
        return capability in self.capabilities
    
    def supports_all(self, *capabilities: ProviderCapability) -> bool:
        """Check if model supports all given capabilities"""
        return all(cap in self.capabilities for cap in capabilities)
    
    def supports_any(self, *capabilities: ProviderCapability) -> bool:
        """Check if model supports any of given capabilities"""
        return any(cap in self.capabilities for cap in capabilities)


@dataclass(frozen=True)
class ProviderCapabilities:
    """Capabilities for a provider"""
    provider_name: str
    default_capabilities: Set[ProviderCapability]
    model_capabilities: Dict[str, ModelCapabilities] = field(default_factory=dict)
    
    def get_model_capabilities(self, model_id: str) -> ModelCapabilities:
        """Get capabilities for a specific model"""
        if model_id in self.model_capabilities:
            return self.model_capabilities[model_id]
        
        # Return default capabilities if model not specifically defined
        return ModelCapabilities(
            model_id=model_id,
            capabilities=self.default_capabilities
        )
    
    def supports_capability(
        self, 
        capability: ProviderCapability,
        model_id: Optional[str] = None
    ) -> bool:
        """Check if provider/model supports a capability"""
        if model_id:
            return self.get_model_capabilities(model_id).supports(capability)
        return capability in self.default_capabilities


# ============================================================================
# Protocol-Based Feature Interface
# ============================================================================

class ProtocolHandler(Protocol):
    """
    Handler for a specific protocol within a feature
    Each protocol handler implements feature behavior for that protocol
    """
    
    @property
    @abstractmethod
    def required_capabilities(self) -> Set[ProviderCapability]:
        """Capabilities required for this handler to work"""
        ...
    
    @abstractmethod
    def can_handle(self, capabilities: ModelCapabilities) -> bool:
        """Check if this handler can work with given capabilities"""
        ...
    
    @abstractmethod
    def modify_request_body(
        self,
        body: Dict[str, Any],
        config: Dict[str, Any],
        capabilities: ModelCapabilities
    ) -> Dict[str, Any]:
        """Modify request body for this protocol"""
        ...
    
    @abstractmethod
    def process_chunk(
        self,
        context: 'ProcessingContext',
        chunk: 'StreamChunk',
        capabilities: ModelCapabilities
    ) -> 'ProcessingContext':
        """Process chunk for this protocol"""
        ...
    
    @abstractmethod
    def transform_to_compatibility(
        self,
        message: 'Message',
        capabilities: ModelCapabilities
    ) -> 'Message':
        """Transform message for this protocol"""
        ...
    
    @abstractmethod
    def transform_from_compatibility(
        self,
        message: 'Message',
        capabilities: ModelCapabilities
    ) -> 'Message':
        """Transform message back for this protocol"""
        ...
    
    @abstractmethod
    def modify_display_format(
        self,
        display_data: Dict[str, Any],
        message: 'Message',
        capabilities: ModelCapabilities
    ) -> Dict[str, Any]:
        """Modify display format for this protocol"""
        ...


class FeatureProtocol(Protocol):
    """Enhanced feature protocol with capability awareness"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Feature identifier"""
        ...
    
    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """Configuration schema for this feature"""
        ...
    
    @abstractmethod
    def get_ui_elements(self) -> List[Dict[str, Any]]:
        """UI elements for this feature"""
        ...
    
    @abstractmethod
    def get_protocol_handlers(self) -> Dict[str, ProtocolHandler]:
        """
        Get protocol handlers for this feature
        Key is a handler identifier (e.g., "openai_style", "anthropic_style")
        """
        ...
    
    @abstractmethod
    def select_handler(
        self,
        capabilities: ModelCapabilities
    ) -> Optional[ProtocolHandler]:
        """
        Select appropriate handler based on model capabilities
        Returns None if feature not supported for this model
        """
        ...
    
    @abstractmethod
    def is_applicable(
        self,
        capabilities: ModelCapabilities,
        config: Dict[str, Any]
    ) -> bool:
        """
        Check if feature is applicable for given capabilities and config
        """
        ...


# ============================================================================
# Enhanced Provider Protocol
# ============================================================================

class ProviderProtocol(Protocol):
    """Enhanced provider protocol with capability declaration"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier"""
        ...
    
    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """Configuration schema"""
        ...
    
    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities:
        """
        Get static capabilities for this provider
        Returns default capabilities and known model capabilities
        """
        ...
    
    @abstractmethod
    def detect_model_capabilities(
        self,
        model_id: str,
        config: Dict[str, Any]
    ) -> Optional[ModelCapabilities]:
        """
        Dynamically detect model capabilities via API
        Returns None if detection not supported or fails
        """
        ...
    
    @abstractmethod
    def to_native_messages(self, messages: tuple['Message', ...]) -> List[Dict[str, Any]]:
        """Convert universal to native format"""
        ...
    
    @abstractmethod
    def from_native_messages(self, native_messages: List[Dict[str, Any]]) -> tuple['Message', ...]:
        """Convert native to universal format"""
        ...
    
    @abstractmethod
    def to_native_request_body(
        self,
        messages: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build provider-specific request body"""
        ...
    
    @abstractmethod
    def process_chunk(
        self,
        context: 'ProcessingContext',
        native_chunk: Dict[str, Any]
    ) -> 'ProcessingContext':
        """Process streaming chunk"""
        ...
    
    @abstractmethod
    def process_response(
        self,
        context: 'ProcessingContext',
        native_response: Dict[str, Any]
    ) -> 'ProcessingContext':
        """Process complete response"""
        ...
    
    @abstractmethod
    def to_display_format(self, message: 'Message') -> Dict[str, Any]:
        """Convert to display format"""
        ...


# ============================================================================
# Example: Enhanced OpenAI Provider with Capabilities
# ============================================================================

class OpenAIProvider:
    """OpenAI provider with capability declarations"""
    
    name = "openai"
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "openai_api_key": {
                "type": "string",
                "required": True,
                "description": "OpenAI API Key"
            },
            "openai_model": {
                "type": "string",
                "required": False,
                "default": "gpt-4",
                "description": "Model name"
            },
            "openai_base_url": {
                "type": "string",
                "required": False,
                "default": "https://api.openai.com/v1"
            }
        }
    
    def get_capabilities(self) -> ProviderCapabilities:
        """Define capabilities for OpenAI models"""
        
        # Default capabilities for OpenAI
        default_caps = {
            ProviderCapability.TEXT_GENERATION,
            ProviderCapability.STREAMING,
            ProviderCapability.SYSTEM_MESSAGES,
            ProviderCapability.MULTI_TURN,
        }
        
        # Specific model capabilities
        model_caps = {
            "gpt-4": ModelCapabilities(
                model_id="gpt-4",
                capabilities={
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.STREAMING,
                    ProviderCapability.TOOL_CALLING,
                    ProviderCapability.PARALLEL_TOOL_CALLING,
                    ProviderCapability.SYSTEM_MESSAGES,
                    ProviderCapability.MULTI_TURN,
                    ProviderCapability.JSON_MODE,
                },
                metadata={"context_window": 8192, "max_output": 4096}
            ),
            "gpt-4-turbo": ModelCapabilities(
                model_id="gpt-4-turbo",
                capabilities={
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.STREAMING,
                    ProviderCapability.TOOL_CALLING,
                    ProviderCapability.PARALLEL_TOOL_CALLING,
                    ProviderCapability.VISION,
                    ProviderCapability.SYSTEM_MESSAGES,
                    ProviderCapability.MULTI_TURN,
                    ProviderCapability.JSON_MODE,
                    ProviderCapability.LARGE_CONTEXT,
                },
                metadata={"context_window": 128000, "max_output": 4096}
            ),
            "gpt-4o": ModelCapabilities(
                model_id="gpt-4o",
                capabilities={
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.STREAMING,
                    ProviderCapability.TOOL_CALLING,
                    ProviderCapability.PARALLEL_TOOL_CALLING,
                    ProviderCapability.VISION,
                    ProviderCapability.AUDIO_INPUT,
                    ProviderCapability.AUDIO_OUTPUT,
                    ProviderCapability.SYSTEM_MESSAGES,
                    ProviderCapability.MULTI_TURN,
                    ProviderCapability.JSON_MODE,
                    ProviderCapability.STRUCTURED_OUTPUT,
                    ProviderCapability.LARGE_CONTEXT,
                },
                metadata={"context_window": 128000, "max_output": 16384}
            ),
            "o1-preview": ModelCapabilities(
                model_id="o1-preview",
                capabilities={
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.REASONING_TRACES,
                    ProviderCapability.CHAIN_OF_THOUGHT,
                    ProviderCapability.LARGE_CONTEXT,
                    # Note: o1 models don't support system messages or tools currently
                },
                metadata={"context_window": 128000, "reasoning_model": True}
            ),
            "gpt-4-search": ModelCapabilities(
                model_id="gpt-4-search",
                capabilities={
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.STREAMING,
                    ProviderCapability.TOOL_CALLING,
                    ProviderCapability.WEB_SEARCH,
                    ProviderCapability.GROUNDING,
                    ProviderCapability.CITATIONS,
                    ProviderCapability.SYSTEM_MESSAGES,
                    ProviderCapability.MULTI_TURN,
                    ProviderCapability.LARGE_CONTEXT,
                },
                metadata={"context_window": 128000, "search_enabled": True}
            ),
        }
        
        return ProviderCapabilities(
            provider_name=self.name,
            default_capabilities=default_caps,
            model_capabilities=model_caps
        )
    
    def detect_model_capabilities(
        self,
        model_id: str,
        config: Dict[str, Any]
    ) -> Optional[ModelCapabilities]:
        """
        Dynamically detect model capabilities via API
        OpenAI has a models API we can query
        """
        try:
            import requests
            
            api_key = config.get("openai_api_key")
            base_url = config.get("openai_base_url", "https://api.openai.com/v1")
            
            response = requests.get(
                f"{base_url}/models/{model_id}",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            
            if response.status_code == 200:
                model_data = response.json()
                
                # Infer capabilities from model data
                capabilities = {
                    ProviderCapability.TEXT_GENERATION,
                    ProviderCapability.STREAMING,
                }
                
                # Check for specific capabilities
                if "gpt-4" in model_id or "gpt-3.5" in model_id:
                    capabilities.add(ProviderCapability.TOOL_CALLING)
                
                if "vision" in model_id or "gpt-4-turbo" in model_id or "gpt-4o" in model_id:
                    capabilities.add(ProviderCapability.VISION)
                
                return ModelCapabilities(
                    model_id=model_id,
                    capabilities=capabilities,
                    metadata=model_data
                )
            
        except Exception as e:
            print(f"Failed to detect capabilities: {e}")
        
        return None
    
    # ... rest of the provider implementation from before ...
    
    def to_native_messages(self, messages: tuple) -> List[Dict[str, Any]]:
        """Convert universal to OpenAI format"""
        native = []
        for msg in messages:
            native_msg = {
                "role": msg.role,
                "content": msg.content
            }
            
            if "tool_calls" in msg.metadata:
                native_msg["tool_calls"] = msg.metadata["tool_calls"]
            if "tool_call_id" in msg.metadata:
                native_msg["tool_call_id"] = msg.metadata["tool_call_id"]
            if "name" in msg.metadata:
                native_msg["name"] = msg.metadata["name"]
            
            native.append(native_msg)
        
        return native
    
    def from_native_messages(self, native_messages: List[Dict[str, Any]]) -> tuple:
        """Convert OpenAI format to universal"""
        from dataclasses import dataclass
        
        @dataclass(frozen=True)
        class Message:
            role: str
            content: str
            metadata: Dict[str, Any] = field(default_factory=dict)
        
        messages = []
        for native_msg in native_messages:
            metadata = {}
            
            if "tool_calls" in native_msg:
                metadata["tool_calls"] = native_msg["tool_calls"]
            if "tool_call_id" in native_msg:
                metadata["tool_call_id"] = native_msg["tool_call_id"]
            if "name" in native_msg:
                metadata["name"] = native_msg["name"]
            
            msg = Message(
                role=native_msg["role"],
                content=native_msg.get("content", ""),
                metadata=metadata
            )
            messages.append(msg)
        
        return tuple(messages)
    
    def to_native_request_body(
        self,
        messages: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "model": config.get("openai_model", "gpt-4"),
            "messages": messages,
            "stream": config.get("stream", False)
        }
    
    def process_chunk(self, context, native_chunk: Dict[str, Any]):
        # Implementation from before
        pass
    
    def process_response(self, context, native_response: Dict[str, Any]):
        # Implementation from before
        pass
    
    def to_display_format(self, message) -> Dict[str, Any]:
        # Implementation from before
        pass


# ============================================================================
# Example: Web Search Feature with Multiple Protocol Handlers
# ============================================================================

class OpenAISearchHandler:
    """Handler for OpenAI-style search (models with native search)"""
    
    @property
    def required_capabilities(self) -> Set[ProviderCapability]:
        return {
            ProviderCapability.WEB_SEARCH,
            ProviderCapability.CITATIONS,
            ProviderCapability.GROUNDING
        }
    
    def can_handle(self, capabilities: ModelCapabilities) -> bool:
        """Check if model has native search capabilities"""
        return capabilities.supports_all(
            ProviderCapability.WEB_SEARCH,
            ProviderCapability.CITATIONS
        )
    
    def modify_request_body(
        self,
        body: Dict[str, Any],
        config: Dict[str, Any],
        capabilities: ModelCapabilities
    ) -> Dict[str, Any]:
        """Enable native search in OpenAI models"""
        new_body = {**body}
        
        # OpenAI-specific search configuration
        new_body["search"] = {
            "enabled": True,
            "max_results": config.get("search_max_results", 5)
        }
        
        return new_body
    
    def process_chunk(
        self,
        context: 'ProcessingContext',
        chunk: 'StreamChunk',
        capabilities: ModelCapabilities
    ) -> 'ProcessingContext':
        """Process search citations in OpenAI format"""
        
        # OpenAI returns citations in metadata
        if chunk.metadata.get("citations"):
            citations = chunk.metadata["citations"]
            
            # Store in meta state
            existing = context.meta_state.get("citations", [])
            new_citations = existing + citations
            
            return context.update_meta(citations=new_citations)
        
        return context
    
    def transform_to_compatibility(
        self,
        message: 'Message',
        capabilities: ModelCapabilities
    ) -> 'Message':
        """Preserve citations during transformations"""
        if "citations" in message.metadata:
            # Mark citations for preservation
            preserved = message.metadata.copy()
            preserved["_preserved_citations"] = preserved["citations"]
            return replace(message, metadata=preserved)
        return message
    
    def transform_from_compatibility(
        self,
        message: 'Message',
        capabilities: ModelCapabilities
    ) -> 'Message':
        """Restore citations after transformations"""
        if "_preserved_citations" in message.metadata:
            restored = message.metadata.copy()
            restored["citations"] = restored.pop("_preserved_citations")
            return replace(message, metadata=restored)
        return message
    
    def modify_display_format(
        self,
        display_data: Dict[str, Any],
        message: 'Message',
        capabilities: ModelCapabilities
    ) -> Dict[str, Any]:
        """Add citations to display in OpenAI format"""
        if "citations" in message.metadata:
            display_data["citations"] = message.metadata["citations"]
            display_data["citation_format"] = "openai"
        return display_data


class ToolBasedSearchHandler:
    """
    Handler for models without native search - implements search via tool calling
    """
    
    @property
    def required_capabilities(self) -> Set[ProviderCapability]:
        return {ProviderCapability.TOOL_CALLING}
    
    def can_handle(self, capabilities: ModelCapabilities) -> bool:
        """Check if model supports tool calling (for search via tools)"""
        return (
            capabilities.supports(ProviderCapability.TOOL_CALLING) and
            not capabilities.supports(ProviderCapability.WEB_SEARCH)
        )
    
    def modify_request_body(
        self,
        body: Dict[str, Any],
        config: Dict[str, Any],
        capabilities: ModelCapabilities
    ) -> Dict[str, Any]:
        """Add search tool to available tools"""
        new_body = {**body}
        
        # Add search tool definition
        tools = new_body.get("tools", [])
        
        search_tool = {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results to return",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            }
        }
        
        tools.append(search_tool)
        new_body["tools"] = tools
        
        return new_body
    
    def process_chunk(
        self,
        context: 'ProcessingContext',
        chunk: 'StreamChunk',
        capabilities: ModelCapabilities
    ) -> 'ProcessingContext':
        """
        Process tool calls - if web_search tool is called, 
        we'll need to execute it and add results
        """
        
        if chunk.tool_calls:
            for tool_call in chunk.tool_calls:
                if tool_call.name == "web_search":
                    # Mark that search was used
                    searches = context.meta_state.get("search_queries", [])
                    searches.append(tool_call.arguments.get("query"))
                    context = context.update_meta(search_queries=searches)
        
        return context
    
    def transform_to_compatibility(
        self,
        message: 'Message',
        capabilities: ModelCapabilities
    ) -> 'Message':
        """
        For tool-based search, we may want to strip search tool calls
        during certain operations to save tokens
        """
        if "tool_calls" in message.metadata:
            tool_calls = message.metadata["tool_calls"]
            # Filter out search tool calls if configured
            non_search_calls = [
                tc for tc in tool_calls 
                if tc.get("function", {}).get("name") != "web_search"
            ]
            
            if len(non_search_calls) < len(tool_calls):
                # Some were filtered
                new_metadata = message.metadata.copy()
                new_metadata["tool_calls"] = non_search_calls
                new_metadata["_removed_search_calls"] = [
                    tc for tc in tool_calls 
                    if tc.get("function", {}).get("name") == "web_search"
                ]
                return replace(message, metadata=new_metadata)
        
        return message
    
    def transform_from_compatibility(
        self,
        message: 'Message',
        capabilities: ModelCapabilities
    ) -> 'Message':
        """Restore search tool calls if needed"""
        if "_removed_search_calls" in message.metadata:
            restored = message.metadata.copy()
            tool_calls = restored.get("tool_calls", [])
            tool_calls.extend(restored.pop("_removed_search_calls"))
            restored["tool_calls"] = tool_calls
            return replace(message, metadata=restored)
        return message
    
    def modify_display_format(
        self,
        display_data: Dict[str, Any],
        message: 'Message',
        capabilities: ModelCapabilities
    ) -> Dict[str, Any]:
        """Add search information to display"""
        if "search_queries" in message.metadata:
            display_data["performed_searches"] = message.metadata["search_queries"]
            display_data["citation_format"] = "tool_based"
        return display_data


class AnthropicGroundingHandler:
    """Handler for Anthropic-style grounding (if they add it)"""
    
    @property
    def required_capabilities(self) -> Set[ProviderCapability]:
        return {ProviderCapability.GROUNDING}
    
    def can_handle(self, capabilities: ModelCapabilities) -> bool:
        """Check for Anthropic grounding"""
        # This would check for Anthropic-specific grounding capability
        return (
            capabilities.supports(ProviderCapability.GROUNDING) and
            capabilities.metadata.get("provider") == "anthropic"
        )
    
    def modify_request_body(
        self,
        body: Dict[str, Any],
        config: Dict[str, Any],
        capabilities: ModelCapabilities
    ) -> Dict[str, Any]:
        """Enable Anthropic grounding"""
        new_body = {**body}
        
        # Anthropic-specific grounding configuration
        new_body["grounding"] = {
            "enabled": True,
            "sources": config.get("grounding_sources", ["web"])
        }
        
        return new_body
    
    def process_chunk(
        self,
        context: 'ProcessingContext',
        chunk: 'StreamChunk',
        capabilities: ModelCapabilities
    ) -> 'ProcessingContext':
        """Process Anthropic grounding metadata"""
        
        # Anthropic might return grounding in a different format
        if chunk.metadata.get("grounding_sources"):
            sources = chunk.metadata["grounding_sources"]
            existing = context.meta_state.get("grounding_sources", [])
            return context.update_meta(grounding_sources=existing + sources)
        
        return context
    
    def transform_to_compatibility(
        self,
        message: 'Message',
        capabilities: ModelCapabilities
    ) -> 'Message':
        """Handle Anthropic-specific grounding format"""
        if "grounding_sources" in message.metadata:
            # Convert to standard format
            preserved = message.metadata.copy()
            preserved["_anthropic_grounding"] = preserved.pop("grounding_sources")
            return replace(message, metadata=preserved)
        return message
    
    def transform_from_compatibility(
        self,
        message: 'Message',
        capabilities: ModelCapabilities
    ) -> 'Message':
        """Restore Anthropic grounding format"""
        if "_anthropic_grounding" in message.metadata:
            restored = message.metadata.copy()
            restored["grounding_sources"] = restored.pop("_anthropic_grounding")
            return replace(message, metadata=restored)
        return message
    
    def modify_display_format(
        self,
        display_data: Dict[str, Any],
        message: 'Message',
        capabilities: ModelCapabilities
    ) -> Dict[str, Any]:
        """Add grounding sources to display"""
        if "grounding_sources" in message.metadata:
            display_data["sources"] = message.metadata["grounding_sources"]
            display_data["citation_format"] = "anthropic"
        return display_data


class WebSearchFeature:
    """
    Web search feature with multiple protocol handlers
    Automatically selects the right handler based on model capabilities
    """
    
    name = "web_search"
    
    def __init__(self):
        self.handlers = {
            "openai_native": OpenAISearchHandler(),
            "tool_based": ToolBasedSearchHandler(),
            "anthropic_grounding": AnthropicGroundingHandler(),
        }
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "web_search_enabled": {
                "type": "boolean",
                "required": False,
                "default": False,
                "description": "Enable web search"
            },
            "search_max_results": {
                "type": "integer",
                "required": False,
                "default": 5,
                "description": "Maximum search results"
            },
            "grounding_sources": {
                "type": "array",
                "items": {"type": "string"},
                "required": False,
                "default": ["web"],
                "description": "Grounding sources"
            }
        }
    
    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "checkbox",
                "key": "web_search_enabled",
                "label": "Enable Web Search",
                "section": "features"
            },
            {
                "type": "number",
                "key": "search_max_results",
                "label": "Max Results",
                "section": "features",
                "condition": {"web_search_enabled": True}
            }
        ]
    
    def get_protocol_handlers(self) -> Dict[str, ProtocolHandler]:
        """Return all available handlers"""
        return self.handlers
    
    def select_handler(
        self,
        capabilities: ModelCapabilities
    ) -> Optional[ProtocolHandler]:
        """
        Select the best handler for given capabilities
        Priority: native search > grounding > tool-based
        """
        
        # Try native search first
        if self.handlers["openai_native"].can_handle(capabilities):
            return self.handlers["openai_native"]
        
        # Try Anthropic grounding
        if self.handlers["anthropic_grounding"].can_handle(capabilities):
            return self.handlers["anthropic_grounding"]
        
        # Fall back to tool-based
        if self.handlers["tool_based"].can_handle(capabilities):
            return self.handlers["tool_based"]
        
        # No suitable handler
        return None
    
    def is_applicable(
        self,
        capabilities: ModelCapabilities,
        config: Dict[str, Any]
    ) -> bool:
        """Check if feature can be applied"""
        if not config.get("web_search_enabled", False):
            return False
        
        return self.select_handler(capabilities) is not None
    
    # Delegate to selected handler
    
    def modify_request_body(
        self,
        body: Dict[str, Any],
        config: Dict[str, Any],
        capabilities: ModelCapabilities
    ) -> Dict[str, Any]:
        """Delegate to appropriate handler"""
        if not self.is_applicable(capabilities, config):
            return body
        
        handler = self.select_handler(capabilities)
        if handler:
            return handler.modify_request_body(body, config, capabilities)
        
        return body
    
    def process_chunk(
        self,
        context: 'ProcessingContext',
        chunk: 'StreamChunk',
        capabilities: ModelCapabilities
    ) -> 'ProcessingContext':
        """Delegate to appropriate handler"""
        handler = self.select_handler(capabilities)
        if handler:
            return handler.process_chunk(context, chunk, capabilities)
        return context
    
    def transform_to_compatibility(
        self,
        message: 'Message',
        capabilities: ModelCapabilities
    ) -> 'Message':
        """Delegate to appropriate handler"""
        handler = self.select_handler(capabilities)
        if handler:
            return handler.transform_to_compatibility(message, capabilities)
        return message
    
    def transform_from_compatibility(
        self,
        message: 'Message',
        capabilities: ModelCapabilities
    ) -> 'Message':
        """Delegate to appropriate handler"""
        handler = self.select_handler(capabilities)
        if handler:
            return handler.transform_from_compatibility(message, capabilities)
        return message
    
    def modify_display_format(
        self,
        display_data: Dict[str, Any],
        message: 'Message',
        capabilities: ModelCapabilities
    ) -> Dict[str, Any]:
        """Delegate to appropriate handler"""
        handler = self.select_handler(capabilities)
        if handler:
            return handler.modify_display_format(display_data, message, capabilities)
        return display_data


# ============================================================================
# Capability-Aware Processing Pipeline
# ============================================================================

class CapabilityAwarePipeline:
    """Processing pipeline that considers capabilities"""
    
    @staticmethod
    def create_request_body_builder(
        provider: ProviderProtocol,
        features: List[FeatureProtocol],
        capabilities: ModelCapabilities
    ) -> Callable[[tuple, 'Config'], Dict[str, Any]]:
        """Create request builder considering capabilities"""
        
        def build_body(messages: tuple, config: 'Config') -> Dict[str, Any]:
            # Convert to native
            native_messages = provider.to_native_messages(messages)
            
            # Build base body
            body = provider.to_native_request_body(native_messages, config.values)
            
            # Apply features that are applicable
            for feature in features:
                if feature.is_applicable(capabilities, config.values):
                    body = feature.modify_request_body(body, config.values, capabilities)
            
            return body
        
        return build_body
    
    @staticmethod
    def create_chunk_processor(
        provider: ProviderProtocol,
        features: List[FeatureProtocol],
        capabilities: ModelCapabilities
    ) -> Callable[['ProcessingContext', Dict[str, Any]], 'ProcessingContext']:
        """Create chunk processor considering capabilities"""
        
        def process_chunk(context: 'ProcessingContext', native_chunk: Dict[str, Any]) -> 'ProcessingContext':
            # Provider processes first
            ctx = provider.process_chunk(context, native_chunk)
            
            # Apply applicable features
            for feature in features:
                if feature.is_applicable(capabilities, {}):  # Config from context
                    # Extract StreamChunk from context (simplified)
                    from dataclasses import dataclass
                    @dataclass(frozen=True)
                    class StreamChunk:
                        content: Optional[str] = None
                        tool_calls: Optional[List] = None
                        metadata: Dict[str, Any] = field(default_factory=dict)
                        is_final: bool = False
                    
                    chunk = StreamChunk()  # Would extract from context
                    ctx = feature.process_chunk(ctx, chunk, capabilities)
            
            return ctx
        
        return process_chunk
    
    @staticmethod
    def create_message_transformer(
        features: List[FeatureProtocol],
        capabilities: ModelCapabilities,
        direction: str  # "to_compatibility" or "from_compatibility"
    ) -> Callable[[tuple], tuple]:
        """Create message transformer considering capabilities"""
        
        def transform(messages: tuple) -> tuple:
            result = messages
            
            if direction == "to_compatibility":
                for feature in features:
                    result = tuple(
                        feature.transform_to_compatibility(msg, capabilities)
                        for msg in result
                    )
            else:  # from_compatibility
                for feature in reversed(features):
                    result = tuple(
                        feature.transform_from_compatibility(msg, capabilities)
                        for msg in result
                    )
            
            return result
        
        return transform


# ============================================================================
# Capability Detection and Caching
# ============================================================================

class CapabilityCache:
    """Cache for detected capabilities"""
    
    def __init__(self):
        self._cache: Dict[str, ModelCapabilities] = {}
    
    def get(
        self,
        provider_name: str,
        model_id: str
    ) -> Optional[ModelCapabilities]:
        """Get cached capabilities"""
        key = f"{provider_name}:{model_id}"
        return self._cache.get(key)
    
    def set(
        self,
        provider_name: str,
        model_id: str,
        capabilities: ModelCapabilities
    ):
        """Cache capabilities"""
        key = f"{provider_name}:{model_id}"
        self._cache[key] = capabilities
    
    def invalidate(self, provider_name: str, model_id: str):
        """Invalidate cached capabilities"""
        key = f"{provider_name}:{model_id}"
        if key in self._cache:
            del self._cache[key]


class CapabilityResolver:
    """Resolves capabilities for provider/model combinations"""
    
    def __init__(self, cache: Optional[CapabilityCache] = None):
        self.cache = cache or CapabilityCache()
    
    def resolve(
        self,
        provider: ProviderProtocol,
        model_id: str,
        config: Dict[str, Any],
        try_detect: bool = True
    ) -> ModelCapabilities:
        """
        Resolve capabilities for a model
        1. Check cache
        2. Try detection if enabled
        3. Fall back to provider defaults
        """
        
        # Check cache first
        cached = self.cache.get(provider.name, model_id)
        if cached:
            return cached
        
        # Try detection
        if try_detect:
            detected = provider.detect_model_capabilities(model_id, config)
            if detected:
                self.cache.set(provider.name, model_id, detected)
                return detected
        
        # Fall back to provider defaults
        provider_caps = provider.get_capabilities()
        model_caps = provider_caps.get_model_capabilities(model_id)
        
        # Cache the result
        self.cache.set(provider.name, model_id, model_caps)
        
        return model_caps


# ============================================================================
# Usage Example
# ============================================================================

def example_capability_aware_usage():
    """Example using capability-aware system"""
    
    # Setup
    provider_registry = ProviderRegistry()
    provider_registry.register(OpenAIProvider())
    
    feature_registry = FeatureRegistry()
    feature_registry.register(WebSearchFeature())
    
    # Configuration
    config_values = {
        "openai_api_key": "sk-...",
        "openai_model": "gpt-4-search",  # Model with native search
        "web_search_enabled": True,
        "search_max_results": 5,
        "stream": True
    }
    
    from dataclasses import dataclass
    @dataclass(frozen=True)
    class Config:
        values: Dict[str, Any]
        def get(self, key: str, default: Any = None) -> Any:
            return self.values.get(key, default)
    
    config = Config(values=config_values)
    
    # Get provider and features
    provider = provider_registry.get("openai")
    web_search = feature_registry.get("web_search")
    
    # Resolve capabilities
    resolver = CapabilityResolver()
    capabilities = resolver.resolve(
        provider,
        config.get("openai_model"),
        config.values,
        try_detect=True
    )
    
    print(f"Model: {capabilities.model_id}")
    print(f"Capabilities: {[c.value for c in capabilities.capabilities]}")
    
    # Check if web search is applicable
    is_applicable = web_search.is_applicable(capabilities, config.values)
    print(f"Web search applicable: {is_applicable}")
    
    # Get selected handler
    handler = web_search.select_handler(capabilities)
    print(f"Selected handler: {handler.__class__.__name__ if handler else None}")
    
    # Build request with capability-aware pipeline
    from dataclasses import dataclass
    @dataclass(frozen=True)
    class Message:
        role: str
        content: str
        metadata: Dict[str, Any] = field(default_factory=dict)
    
    messages = (
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="What's the latest news on AI?"),
    )
    
    body_builder = CapabilityAwarePipeline.create_request_body_builder(
        provider,
        [web_search],
        capabilities
    )
    
    body = body_builder(messages, config)
    print(f"\nRequest body:\n{json.dumps(body, indent=2)}")
    
    # The request will use native search if model supports it,
    # or fall back to tool-based search if not


if __name__ == "__main__":
    example_capability_aware_usage()
```

## Key Design Improvements

### 1. **Protocol-Based System**
- `ProviderCapability` enum defines standard capabilities
- Models declare which capabilities they support
- Features check capabilities to determine applicability

### 2. **Multiple Handlers Per Feature**
- Single feature (e.g., `WebSearchFeature`) has multiple handlers
- Each handler implements the feature for specific protocols
- Automatic handler selection based on capabilities

### 3. **Capability Declaration**
- Static: Providers define known model capabilities upfront
- Dynamic: Optional API-based detection for unknown models
- Cached: Capabilities cached to avoid repeated detection

### 4. **Flexible Feature Application**
- Features only apply if model supports required capabilities
- Same feature works differently across providers/models
- Graceful degradation (native → tool-based → unavailable)

### 5. **Clean Separation**
- Provider-specific quirks stay in provider
- Feature implementation stays in feature handlers
- Core pipeline is capability-agnostic

This architecture allows:
- Adding new capabilities without changing core
- Features that work across any provider supporting a capability
- Provider-specific optimizations within features
- Automatic fallback strategies
- Easy testing of capability-specific behavior

Would you like me to add more examples of features with multiple handlers, or elaborate on the capability detection system?

---

## 👤 You ##

For capability check, the feature may call the provider directly with a call like can_handle(capability_id, config), this way the core system would just provide a way the feature plugin. An communicate with the provider via pure function calls (if API call is required, it should be initiated by the core system upon loading).
I need a higher level architectue description, with only minimal implementation notes. Implementation notes should rather be examples, e.g usage examples, or plugin examples. The 

---

## Assistant · *Claude 4 Sonnet* ##

# AI Agent Platform - Modular Functional Architecture

## High-Level Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Core System                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Configuration Manager                        │  │
│  │  - Merges schemas from providers & features              │  │
│  │  - Validates configuration                                │  │
│  │  - Handles loading/initialization                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Capability Resolution System                   │  │
│  │  - Initiates API calls for capability detection          │  │
│  │  - Caches capabilities                                    │  │
│  │  - Provides query interface to features                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Processing Pipeline                          │  │
│  │  - Composes provider + feature transformations           │  │
│  │  - Manages conversation state (immutable)                │  │
│  │  - Orchestrates request/response flow                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Message Transformation Pipeline                 │  │
│  │  - to_compatibility / from_compatibility                 │  │
│  │  - Applies common operations (trim, filter)              │  │
│  │  - Pure functional transformations                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │
        ┌─────────────────────┴──────────────────────┐
        │                                             │
        ▼                                             ▼
┌───────────────────┐                        ┌───────────────────┐
│  Provider Plugin  │                        │  Feature Plugin   │
│                   │                        │                   │
│ - Capabilities    │                        │ - Protocol        │
│ - Native format   │◄───can_handle()────────│   Handlers        │
│ - Request/Response│                        │ - Conditional     │
│ - Streaming       │                        │   application     │
└───────────────────┘                        └───────────────────┘
        │                                             │
        │                                             │
        └─────────────────────┬──────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   User Request   │
                    │   ↓              │
                    │   Processing     │
                    │   ↓              │
                    │   Response       │
                    └──────────────────┘
```

## Core Concepts

### 1. **Immutable Data Flow**

All data structures are immutable. Transformations create new instances:

```
ConversationState (messages) 
    → [Compatibility Transform]
    → [Common Operations: trim/filter]
    → [Reverse Transform]
    → [Provider Native Format]
    → [API Request]
    → [API Response]
    → [Provider Processing]
    → [Feature Processing]
    → Updated ConversationState
```

### 2. **Capability-Based Feature Application**

Features query providers about capabilities through the core system:

```
Feature wants to enable search
    ↓
Feature: Can you handle "web_search"?
    ↓
Core → Provider.can_handle("web_search", model_id, config)
    ↓
Provider: Yes/No + metadata
    ↓
Feature: Selects appropriate handler OR skips
```

### 3. **Protocol Handlers**

A single feature contains multiple handlers for different capability protocols:

```
WebSearchFeature
├── OpenAINativeSearchHandler (requires: native_search capability)
├── ToolBasedSearchHandler (requires: tool_calling capability)
└── AnthropicGroundingHandler (requires: grounding capability)

Feature selects handler based on provider's capabilities
```

### 4. **Pure Function Composition**

All transformations are pure functions that can be composed:

```python
# Pure transformations
transform1: Message → Message
transform2: Message → Message
transform3: Messages → Messages

# Composition
composed = compose(transform1, transform2)
pipeline = apply_to_all(composed) >> transform3

# Application
result = pipeline(messages)
```

## Component Interfaces

### Provider Plugin Interface

```python
ProviderPlugin:
    # Identity
    .name: str
    
    # Capabilities
    .can_handle(capability_id, model_id, config) → bool
    .get_capabilities() → ProviderCapabilities  # Static definitions
    .detect_capabilities(model_id, config) → Optional[Capabilities]  # Called by core on init
    
    # Configuration
    .get_config_schema() → Dict  # What config this provider needs
    
    # Message Conversion (Pure Functions)
    .to_native_messages(messages) → native_messages
    .from_native_messages(native_messages) → messages
    
    # Request/Response (Core manages I/O)
    .build_request_body(native_messages, config) → body
    .process_chunk(context, native_chunk) → new_context  # Pure
    .process_response(context, native_response) → new_context  # Pure
    
    # Display
    .to_display_format(message) → display_dict
```

### Feature Plugin Interface

```python
FeaturePlugin:
    # Identity
    .name: str
    
    # Configuration
    .get_config_schema() → Dict
    .get_ui_elements() → List[UIElement]
    
    # Protocol Handlers
    .get_handlers() → Dict[str, ProtocolHandler]
    
    # Applicability (queries provider via callback)
    .is_applicable(can_handle_fn, config) → bool
        # can_handle_fn is: (capability_id) → bool
    
    # Handler Selection
    .select_handler(can_handle_fn) → Optional[Handler]
    
    # Transformations (all pure functions)
    .modify_request_body(body, config, can_handle_fn) → body
    .process_chunk(context, chunk, can_handle_fn) → context
    .transform_to_compatibility(message) → message
    .transform_from_compatibility(message) → message
    .modify_display_format(display, message) → display
```

### Protocol Handler Interface

```python
ProtocolHandler:
    # Capability Requirements
    .required_capabilities: Set[str]
    
    # All operations are pure functions
    .modify_request_body(body, config) → body
    .process_chunk(context, chunk) → context
    .transform_to_compatibility(message) → message
    .transform_from_compatibility(message) → message
    .modify_display_format(display, message) → display
```

## Data Structures

### Core Types

```python
Message (immutable):
    - role: str
    - content: str
    - metadata: Dict[str, Any]

ConversationState (immutable):
    - messages: Tuple[Message, ...]
    - metadata: Dict[str, Any]
    
ProcessingContext (immutable):
    - conversation: ConversationState
    - incomplete_message: Optional[Dict]  # For streaming
    - meta_state: Dict[str, Any]  # Handler-specific state

StreamChunk (immutable):
    - content: Optional[str]
    - tool_calls: Optional[List[ToolCall]]
    - metadata: Dict[str, Any]
    - is_final: bool

Config (immutable):
    - values: Dict[str, Any]
```

## Request Flow Architecture

### Phase 1: Initialization (Core System)

```
1. Load provider plugins
2. Load feature plugins
3. For each provider:
   - Call detect_capabilities(model_id, config) for configured models
   - Core makes API calls if needed
   - Cache results
4. Build merged configuration schema
5. Validate user configuration
```

### Phase 2: Request Preparation

```
1. User provides message
2. Add to ConversationState (immutable)
3. Apply message transformations:
   
   messages
   → Feature.transform_to_compatibility() [for each enabled feature]
   → CommonOps.trim_by_tokens() / filter() [pure functions]
   → Feature.transform_from_compatibility() [reverse order]
   → Provider.to_native_messages()
   
4. Build request body:
   
   body = Provider.build_request_body(native_messages, config)
   
   For each enabled feature:
     can_handle_fn = lambda cap: provider.can_handle(cap, model_id, config)
     if feature.is_applicable(can_handle_fn, config):
       body = feature.modify_request_body(body, config, can_handle_fn)
```

### Phase 3: API Call (Core System)

```
Core system makes actual HTTP request:
- Streaming or non-streaming based on config
- Handles retries, rate limiting, errors
- Yields chunks or returns complete response
```

### Phase 4: Response Processing

```
For each chunk/response:

1. Provider processes native format:
   context = Provider.process_chunk(context, native_chunk)
   
2. Features process (if applicable):
   For each enabled feature:
     can_handle_fn = lambda cap: provider.can_handle(cap, model_id, config)
     if feature.is_applicable(can_handle_fn, config):
       context = feature.process_chunk(context, chunk, can_handle_fn)

3. Extract completed messages from context
4. Return to Phase 2 if tool calls detected (agent loop)
```

### Phase 5: Display

```
For each message:
1. display = Provider.to_display_format(message)
2. For each enabled feature:
   display = feature.modify_display_format(display, message)
3. Render to UI
```

## Usage Example

### Basic Usage

```python
# Initialize core system
core = AgentCore()

# Register plugins
core.register_provider(OpenAIProvider())
core.register_provider(AnthropicProvider())
core.register_feature(WebSearchFeature())
core.register_feature(ReasoningTracesFeature())

# Configure
config = {
    "provider": "openai",
    "model": "gpt-4o",
    "api_key": "sk-...",
    "web_search_enabled": True,
    "max_tokens": 4096
}

# Core initializes (detects capabilities via API if needed)
session = core.create_session(config)

# User interaction
response = session.send_message("What's the latest on AI?")

# Streaming
for chunk in session.send_message_stream("Tell me about the weather"):
    print(chunk.content, end="", flush=True)

# Access conversation
history = session.get_conversation()
for msg in history.messages:
    display = session.format_for_display(msg)
    print(display)
```

### Plugin Example: Web Search Feature

```python
class WebSearchFeature:
    name = "web_search"
    
    def __init__(self):
        self.handlers = {
            "native_search": NativeSearchHandler(),
            "tool_based": ToolBasedSearchHandler(),
            "grounding": GroundingHandler()
        }
    
    def get_config_schema(self):
        return {
            "web_search_enabled": {"type": "boolean", "default": False},
            "max_search_results": {"type": "integer", "default": 5}
        }
    
    def is_applicable(self, can_handle_fn, config):
        """
        Query provider about capabilities via can_handle_fn
        """
        if not config.get("web_search_enabled"):
            return False
        
        # Check if any handler can work
        return (
            can_handle_fn("native_search") or
            can_handle_fn("tool_calling") or
            can_handle_fn("grounding")
        )
    
    def select_handler(self, can_handle_fn):
        """
        Select best handler based on what provider supports
        """
        # Priority: native > grounding > tool-based
        if can_handle_fn("native_search"):
            return self.handlers["native_search"]
        elif can_handle_fn("grounding"):
            return self.handlers["grounding"]
        elif can_handle_fn("tool_calling"):
            return self.handlers["tool_based"]
        return None
    
    def modify_request_body(self, body, config, can_handle_fn):
        """
        Delegate to selected handler
        """
        handler = self.select_handler(can_handle_fn)
        if handler:
            return handler.modify_request_body(body, config)
        return body
    
    # Other methods similarly delegate to selected handler
```

### Plugin Example: Provider with Capabilities

```python
class OpenAIProvider:
    name = "openai"
    
    def get_capabilities(self):
        """
        Static capability definitions
        """
        return {
            "default": ["text_generation", "streaming", "tool_calling"],
            "models": {
                "gpt-4": ["text_generation", "streaming", "tool_calling", "json_mode"],
                "gpt-4-turbo": ["text_generation", "streaming", "tool_calling", 
                               "vision", "json_mode", "large_context"],
                "gpt-4o": ["text_generation", "streaming", "tool_calling", 
                          "vision", "audio_input", "audio_output", "structured_output"],
                "gpt-4-search": ["text_generation", "streaming", "tool_calling",
                                "native_search", "citations", "grounding"]
            }
        }
    
    def detect_capabilities(self, model_id, config):
        """
        Called by core on initialization for unknown models
        Returns None if API call not needed/fails
        """
        # Core will make actual HTTP request via this method
        api_key = config.get("api_key")
        endpoint = f"https://api.openai.com/v1/models/{model_id}"
        
        # Return request spec for core to execute
        return {
            "method": "GET",
            "url": endpoint,
            "headers": {"Authorization": f"Bearer {api_key}"},
            "parser": self._parse_model_info  # Function to parse response
        }
    
    def _parse_model_info(self, response_json):
        """
        Parse API response to determine capabilities
        """
        capabilities = ["text_generation", "streaming"]
        
        # Infer from model data
        if "gpt-4" in response_json.get("id", ""):
            capabilities.extend(["tool_calling", "json_mode"])
        if "vision" in response_json.get("capabilities", []):
            capabilities.append("vision")
            
        return capabilities
    
    def can_handle(self, capability_id, model_id, config):
        """
        Pure function - check if model supports capability
        Uses cached capabilities (populated during init)
        """
        caps = self.get_capabilities()
        
        # Check specific model
        if model_id in caps["models"]:
            return capability_id in caps["models"][model_id]
        
        # Check default
        return capability_id in caps["default"]
    
    def to_native_messages(self, messages):
        """Pure conversion function"""
        return [
            {
                "role": msg.role,
                "content": msg.content,
                **msg.metadata  # OpenAI-specific fields from metadata
            }
            for msg in messages
        ]
    
    def process_chunk(self, context, native_chunk):
        """
        Pure function - processes one chunk
        Returns new context with updated state
        """
        # Extract delta
        delta = native_chunk.get("choices", [{}])[0].get("delta", {})
        
        # Accumulate in context.meta_state
        incomplete = context.meta_state.get("incomplete", {"content": ""})
        
        if "content" in delta:
            incomplete["content"] += delta["content"]
        
        # Check if complete
        if native_chunk.get("choices", [{}])[0].get("finish_reason"):
            # Create message and add to conversation
            new_msg = Message(
                role="assistant",
                content=incomplete["content"],
                metadata={}
            )
            new_conv = context.conversation.add_message(new_msg)
            return context.update_conversation(new_conv).update_meta(incomplete=None)
        
        return context.update_meta(incomplete=incomplete)
```

### Plugin Example: Protocol Handler

```python
class NativeSearchHandler:
    """Handler for providers with native search capability"""
    
    required_capabilities = {"native_search", "citations"}
    
    def modify_request_body(self, body, config):
        """
        Pure function - adds search parameters to request
        """
        return {
            **body,
            "search": {
                "enabled": True,
                "max_results": config.get("max_search_results", 5)
            }
        }
    
    def process_chunk(self, context, chunk):
        """
        Pure function - extracts citations from chunk
        """
        citations = chunk.metadata.get("citations", [])
        if not citations:
            return context
        
        # Accumulate citations in meta_state
        existing = context.meta_state.get("citations", [])
        return context.update_meta(citations=existing + citations)
    
    def transform_to_compatibility(self, message):
        """
        Pure function - prepare message for common operations
        Preserve citations separately
        """
        if "citations" not in message.metadata:
            return message
        
        # Store citations with special marker
        new_metadata = {
            **message.metadata,
            "_preserved_citations": message.metadata["citations"]
        }
        # Remove original to avoid interference with trimming
        del new_metadata["citations"]
        
        return Message(
            role=message.role,
            content=message.content,
            metadata=new_metadata
        )
    
    def transform_from_compatibility(self, message):
        """Pure function - restore citations"""
        if "_preserved_citations" not in message.metadata:
            return message
        
        new_metadata = {**message.metadata}
        new_metadata["citations"] = new_metadata.pop("_preserved_citations")
        
        return Message(
            role=message.role,
            content=message.content,
            metadata=new_metadata
        )
    
    def modify_display_format(self, display, message):
        """Pure function - add citations to display"""
        if "citations" in message.metadata:
            return {
                **display,
                "citations": message.metadata["citations"],
                "has_citations": True
            }
        return display
```

## Common Operations (Pure Functions)

These work on the "compatibility format" (after to_compatibility transform):

```python
# Trimming
trim_by_count(max_messages) → (messages → messages)
trim_by_tokens(max_tokens, token_counter) → (messages → messages)

# Filtering
filter_by_role(roles) → (messages → messages)
filter_by_metadata(predicate) → (messages → messages)

# Composition
compose(f1, f2, f3) → (messages → messages)
pipeline = compose(
    trim_by_count(50),
    filter_by_role("user", "assistant"),
    trim_by_tokens(4000, simple_token_counter)
)
```

## Extension Points

### 1. Add New Provider

```python
class GeminiProvider:
    name = "gemini"
    
    def get_capabilities(self):
        return {
            "default": ["text_generation", "streaming", "large_context"],
            "models": {
                "gemini-pro": ["text_generation", "streaming", "large_context"],
                "gemini-pro-vision": ["text_generation", "vision", "large_context"]
            }
        }
    
    def can_handle(self, capability_id, model_id, config):
        # Implementation
        pass
    
    # ... implement other required methods
```

### 2. Add New Feature

```python
class ImageGenerationFeature:
    name = "image_generation"
    
    def __init__(self):
        self.handlers = {
            "dalle": DALLEHandler(),           # For OpenAI
            "imagen": ImagenHandler(),         # For Google
            "tool_based": ToolImageHandler()   # Generic fallback
        }
    
    def is_applicable(self, can_handle_fn, config):
        return (
            config.get("image_generation_enabled") and
            can_handle_fn("image_generation")
        )
    
    # ... implement other required methods
```

### 3. Add New Protocol Handler

```python
class CustomSearchHandler:
    """Handler for custom search protocol"""
    
    required_capabilities = {"custom_search"}
    
    def modify_request_body(self, body, config):
        # Custom implementation
        pass
    
    # ... implement other required methods

# Add to feature
web_search_feature.handlers["custom"] = CustomSearchHandler()
```

## Key Benefits

1. **Pure Functional Core**: All transformations are pure functions, easy to test and compose
2. **Provider Isolation**: Provider-specific logic stays in provider plugins
3. **Feature Flexibility**: Features adapt to provider capabilities automatically
4. **Extensibility**: Add providers/features without touching core
5. **Capability-Driven**: Features query capabilities, select appropriate strategy
6. **Immutable State**: All state changes create new instances
7. **Type Safety**: Clear interfaces and protocols
8. **Composability**: Pure functions compose naturally
9. **Testability**: Pure functions with no side effects

## Core System Responsibilities

- Plugin loading and registration
- Configuration validation and merging
- Capability detection (making actual API calls)
- Capability caching and querying
- HTTP request execution
- Pipeline orchestration
- Conversation state management
- Error handling and retry logic
- Streaming coordination

## Plugin Responsibilities

**Providers:**
- Define capabilities
- Convert message formats
- Build request bodies
- Process responses/chunks
- Handle provider-specific quirks

**Features:**
- Define configuration needs
- Provide multiple handlers
- Query capabilities via callback
- Select appropriate handler
- Transform messages/requests/displays

---

## 👤 You ##

ProcessingContext Is not needed, metadata could be used to store incomplete message. Prefer free dynamic state. StreamChunk type should't be defined since it's the object directly received from the server, and can be different from provider to provider. Detect capabilities should be executed only for the actual provider and model, and it should rather be called init, and the result should be saved in a meta state (a free dict that can contain any data), and this could be used for other operations too. (This is implementation detail that should't be in this document, that a high-order function could be called with this data after init, that could return all the processing function so that this data is not fed to all functiona every time). For the web search example, better  not to mix in tool calls, that is outside of feature plugins' scope. A more realistic example would be the  ass that the same feature is enabled with a different key in the body with different providers (provider protocol), and require web search capability for the model in order to add that specific key. The feature plugin's feature check (or any call to the provider) should be done for all the transformation functions. Also those functions could themselves return tranformation functions after capabiliy checking. Mention that these are rough examples and the real implementation may differ.

---

## Assistant · *Claude 4 Sonnet* ##

# AI Agent Platform - Modular Functional Architecture

## High-Level Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Core System                              │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Configuration Manager                        │  │
│  │  - Merges schemas from providers & features              │  │
│  │  - Validates configuration                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Plugin Initialization System                   │  │
│  │  - Calls provider.init(model, config) once               │  │
│  │  - Stores results in free meta_state dict                │  │
│  │  - Makes API calls during init if needed                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Processing Pipeline                          │  │
│  │  - Composes provider + feature transformations           │  │
│  │  - Manages conversation state (immutable messages)       │  │
│  │  - Maintains free metadata dict for any dynamic state    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Message Transformation Pipeline                 │  │
│  │  - to_compatibility / from_compatibility                 │  │
│  │  - Applies common operations (trim, filter)              │  │
│  │  - Pure functional transformations                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │
        ┌─────────────────────┴──────────────────────┐
        │                                             │
        ▼                                             ▼
┌───────────────────┐                        ┌───────────────────┐
│  Provider Plugin  │                        │  Feature Plugin   │
│                   │                        │                   │
│ - init()          │◄───can_handle()────────│ - Protocol        │
│ - Capabilities    │                        │   Handlers        │
│ - Native format   │                        │ - Capability      │
│ - Request/Response│                        │   checking        │
└───────────────────┘                        └───────────────────┘
```

## Core Principles

### 1. **Immutable Message Flow with Dynamic Metadata**

```
ConversationState:
  - messages: Tuple[Message, ...] (immutable)
  - metadata: Dict[str, Any] (free-form, stores any state)
    - incomplete_message (for streaming)
    - citations (from features)
    - reasoning_traces (from features)
    - provider_state (from provider)
    - feature_state (from features)
    - ... (anything)
```

All transformations are pure functions that return new state.

### 2. **Capability-Based Feature Application**

Features query providers about capabilities through callbacks provided by core:

```
Feature needs web_search capability
    ↓
Feature: can_handle_fn("web_search")
    ↓
Core → Provider.can_handle("web_search", meta_state)
    ↓
Provider: Uses meta_state from init() to determine
    ↓
Returns: bool
    ↓
Feature: Proceeds or skips
```

This callback approach keeps features decoupled from providers.

### 3. **Provider Initialization**

Providers have an `init()` method called once during setup:

```python
# Core calls once per session
meta_state = provider.init(model_id, config)

# meta_state is free dict containing:
{
    "capabilities": ["text_generation", "streaming", "web_search"],
    "model_info": {...},
    "context_window": 128000,
    "provider_specific_data": {...}
}

# This meta_state is:
# - Stored by core
# - Passed to can_handle() queries
# - Available for provider's processing functions
```

**Implementation note:** *Higher-order functions can close over meta_state to avoid passing it repeatedly. For example, `init()` could return both meta_state and a set of processing functions that have access to it.*

### 4. **Higher-Order Functions Pattern**

Features return transformation functions after capability checking:

```python
# Feature method returns a function or None
def get_request_modifier(self, can_handle_fn, config):
    """
    Returns request modification function if applicable,
    None otherwise
    """
    if not config.get("search_enabled"):
        return None
    
    if not can_handle_fn("web_search"):
        return None
    
    # Return actual transformation function
    def modify_request(body):
        return {**body, "search_enabled": True}
    
    return modify_request

# Core uses it:
modifier = feature.get_request_modifier(can_handle_fn, config)
if modifier:
    body = modifier(body)
```

This allows capability checking once, then pure function application many times.

## Component Interfaces

### Provider Plugin Interface

```python
ProviderPlugin:
    # Identity
    .name: str
    
    # Initialization (called once by core)
    .init(model_id, config) → meta_state: Dict[str, Any]
        # - Can make API calls to detect capabilities
        # - Returns free-form dict with any provider data
        # - Stored by core, passed to can_handle()
    
    # Capability Queries (pure function)
    .can_handle(capability_id, meta_state) → bool
        # - Pure function using meta_state from init()
        # - Called by features via callback
    
    # Configuration
    .get_config_schema() → Dict
    
    # Message Conversion (pure functions)
    .to_native_messages(messages, meta_state) → native_messages
    .from_native_messages(native_messages, meta_state) → messages
    
    # Request Building (pure function)
    .build_request_body(native_messages, config, meta_state) → body
    
    # Response Processing (pure functions)
    # Takes provider-native chunk/response directly from API
    .process_chunk(conversation_state, native_chunk, meta_state) 
        → new_conversation_state
        
    .process_response(conversation_state, native_response, meta_state)
        → new_conversation_state
    
    # Display
    .to_display_format(message, meta_state) → display_dict
```

**Note:** *native_chunk is the raw chunk from the streaming API, format varies by provider. Not a standardized type.*

### Feature Plugin Interface

```python
FeaturePlugin:
    # Identity
    .name: str
    
    # Configuration
    .get_config_schema() → Dict
    .get_ui_elements() → List[UIElement]
    
    # Transformation Functions Return Functions
    # Each returns Optional[TransformFunction]
    
    .get_request_modifier(can_handle_fn, config, meta_state) 
        → Optional[body → body]
        
    .get_chunk_processor(can_handle_fn, config, meta_state)
        → Optional[(state, chunk) → state]
        
    .get_to_compatibility_transform(can_handle_fn, config, meta_state)
        → Optional[message → message]
        
    .get_from_compatibility_transform(can_handle_fn, config, meta_state)
        → Optional[message → message]
        
    .get_display_modifier(can_handle_fn, config, meta_state)
        → Optional[(display, message) → display]
```

**Key Pattern:** Each method checks capabilities once and returns a transformation function (or None). The returned functions are pure and can be called many times.

## Data Structures

### Core Types

```python
Message (immutable):
    - role: str
    - content: str
    - metadata: Dict[str, Any]  # Free-form, any data

ConversationState (immutable):
    - messages: Tuple[Message, ...]
    - metadata: Dict[str, Any]  # Free-form dynamic state
        Examples of what might be stored:
        - incomplete_message: Dict  # During streaming
        - citations: List  # From search feature
        - reasoning_traces: Dict  # From reasoning feature
        - provider_internal_state: Any
        - feature_internal_state: Any
        - ... anything needed

Config (immutable):
    - values: Dict[str, Any]
```

**No StreamChunk type** - chunks are provider-native format, handled directly by provider's `process_chunk()`.

## Request Flow Architecture

### Phase 1: System Initialization

```
1. Core loads provider and feature plugins
2. User provides configuration (provider, model, keys, etc.)
3. Core validates configuration against merged schema
4. Core calls provider.init(model_id, config):
   - Provider may make API calls to detect capabilities
   - Returns meta_state dict with capabilities and any data
5. Core stores meta_state
6. Core creates can_handle_fn = lambda cap: provider.can_handle(cap, meta_state)
```

### Phase 2: Feature Initialization

```
For each feature:
1. Feature calls can_handle_fn to check applicability
2. Feature returns transformation functions (or None):
   - request_modifier = feature.get_request_modifier(can_handle_fn, config, meta_state)
   - chunk_processor = feature.get_chunk_processor(...)
   - to_compat = feature.get_to_compatibility_transform(...)
   - from_compat = feature.get_from_compatibility_transform(...)
   - display_modifier = feature.get_display_modifier(...)
3. Core stores these functions for use in pipeline
```

**Implementation note:** *Features can use closure to capture meta_state, avoiding repeated passing.*

### Phase 3: Request Preparation

```
User message arrives
    ↓
Add to ConversationState.messages (immutable)
    ↓
Apply transformations:

messages
→ Apply to_compat transforms from features
→ Apply common operations (trim_by_tokens, filter, etc.)
→ Apply from_compat transforms from features (reverse order)
→ Provider.to_native_messages(messages, meta_state)
→ Provider.build_request_body(native_messages, config, meta_state)
→ Apply request_modifiers from features
    ↓
Final request body ready for API
```

### Phase 4: API Call (Core Responsibility)

```
Core makes HTTP request:
- Streaming or non-streaming
- Handles connection, retries, errors
- Yields native chunks or returns native response
```

### Phase 5: Response Processing

```
For each native chunk from API:
    ↓
Provider.process_chunk(state, native_chunk, meta_state)
    → Returns new state with updated metadata
    ↓
Apply chunk_processors from applicable features
    → Each updates state.metadata with feature-specific data
    ↓
Check state.metadata for completed messages
    ↓
If tool calls detected → Loop back to Phase 3
If complete → Continue
```

### Phase 6: Display Formatting

```
For each message:
    ↓
display = Provider.to_display_format(message, meta_state)
    ↓
Apply display_modifiers from applicable features
    → Each enhances display dict
    ↓
Return to UI
```

## Example: Web Search Feature (Rough Sketch)

*Note: This is a conceptual example. Real implementation may differ significantly.*

```python
class WebSearchFeature:
    name = "web_search"
    
    def get_config_schema(self):
        return {
            "web_search_enabled": {"type": "boolean", "default": False},
            "max_results": {"type": "integer", "default": 5}
        }
    
    def get_request_modifier(self, can_handle_fn, config, meta_state):
        """
        Returns function to modify request body if applicable
        """
        # Check config
        if not config.get("web_search_enabled"):
            return None
        
        # Check capability
        if not can_handle_fn("web_search"):
            return None
        
        # Determine which provider protocol
        # Different providers need different keys in request body
        
        if can_handle_fn("openai_search_protocol"):
            # OpenAI uses "search" key
            def modify(body):
                return {
                    **body,
                    "search": {
                        "enabled": True,
                        "max_results": config.get("max_results", 5)
                    }
                }
            return modify
        
        elif can_handle_fn("anthropic_grounding_protocol"):
            # Anthropic uses "grounding" key
            def modify(body):
                return {
                    **body,
                    "grounding": {
                        "enabled": True,
                        "max_sources": config.get("max_results", 5)
                    }
                }
            return modify
        
        elif can_handle_fn("google_search_protocol"):
            # Google uses "search_grounding" key
            def modify(body):
                return {
                    **body,
                    "search_grounding": True,
                    "search_config": {
                        "max_results": config.get("max_results", 5)
                    }
                }
            return modify
        
        return None
    
    def get_chunk_processor(self, can_handle_fn, config, meta_state):
        """
        Returns function to process chunks if applicable
        """
        if not config.get("web_search_enabled"):
            return None
        
        if not can_handle_fn("web_search"):
            return None
        
        # Return processor that accumulates citations
        def process(state, chunk):
            # Extract citations based on provider format
            # (chunk format is provider-specific)
            citations = self._extract_citations(chunk, can_handle_fn)
            
            if citations:
                # Add to metadata
                existing = state.metadata.get("citations", [])
                new_metadata = {
                    **state.metadata,
                    "citations": existing + citations
                }
                return ConversationState(
                    messages=state.messages,
                    metadata=new_metadata
                )
            
            return state
        
        return process
    
    def _extract_citations(self, chunk, can_handle_fn):
        """Extract citations from provider-native chunk"""
        if can_handle_fn("openai_search_protocol"):
            # OpenAI format
            return chunk.get("search_results", {}).get("citations", [])
        
        elif can_handle_fn("anthropic_grounding_protocol"):
            # Anthropic format
            sources = chunk.get("grounding", {}).get("sources", [])
            return [{"url": s["url"], "title": s["title"]} for s in sources]
        
        return []
    
    def get_display_modifier(self, can_handle_fn, config, meta_state):
        """
        Returns function to enhance display with citations
        """
        if not config.get("web_search_enabled"):
            return None
        
        def modify(display, message):
            # Add citations from message metadata to display
            if "citations" in message.metadata:
                return {
                    **display,
                    "citations": message.metadata["citations"],
                    "has_search_results": True
                }
            return display
        
        return modify
```

**Key Points in Example:**
- Same feature (web search) works across multiple providers
- Different providers require different request body keys
- Feature checks provider protocol capabilities
- Each provider protocol is a distinct capability
- No tool calling involved - this is native search capability
- Capability checks happen once when getting functions
- Returned functions are pure and reusable

## Example: Provider with Initialization

*Note: This is a conceptual example. Real implementation may differ.*

```python
class OpenAIProvider:
    name = "openai"
    
    def init(self, model_id, config):
        """
        Called once by core during setup
        Can make API calls to detect capabilities
        """
        api_key = config.get("api_key")
        
        # Static capabilities (known)
        capabilities = self._get_static_capabilities(model_id)
        
        # Optionally detect via API for unknown models
        if model_id not in self._known_models:
            detected = self._detect_via_api(model_id, api_key)
            if detected:
                capabilities.extend(detected)
        
        # Return free-form meta_state
        return {
            "model_id": model_id,
            "capabilities": capabilities,
            "context_window": self._get_context_window(model_id),
            "supports_parallel_tools": "gpt-4" in model_id,
            # Any other data needed for processing
        }
    
    def can_handle(self, capability_id, meta_state):
        """
        Pure function - check capability using meta_state
        """
        return capability_id in meta_state.get("capabilities", [])
    
    def _get_static_capabilities(self, model_id):
        """Define known capabilities"""
        model_caps = {
            "gpt-4o": [
                "text_generation",
                "streaming", 
                "tool_calling",
                "vision",
                "audio_input",
                "audio_output"
            ],
            "gpt-4-search": [
                "text_generation",
                "streaming",
                "tool_calling",
                "web_search",
                "openai_search_protocol",  # Protocol capability
                "citations"
            ],
            "o1-preview": [
                "text_generation",
                "reasoning_traces",
                "large_context"
            ]
        }
        return model_caps.get(model_id, ["text_generation", "streaming"])
    
    def _detect_via_api(self, model_id, api_key):
        """Make API call to detect capabilities of unknown model"""
        # Core will handle the actual HTTP request
        # This just builds and parses
        import requests
        
        try:
            response = requests.get(
                f"https://api.openai.com/v1/models/{model_id}",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                # Infer capabilities from response
                caps = []
                if data.get("capabilities", {}).get("vision"):
                    caps.append("vision")
                if data.get("capabilities", {}).get("function_calling"):
                    caps.append("tool_calling")
                return caps
        except:
            pass
        
        return []
    
    def to_native_messages(self, messages, meta_state):
        """Convert to OpenAI format"""
        native = []
        for msg in messages:
            native_msg = {
                "role": msg.role,
                "content": msg.content
            }
            
            # Add OpenAI-specific fields from message metadata
            if "tool_calls" in msg.metadata:
                native_msg["tool_calls"] = msg.metadata["tool_calls"]
            if "tool_call_id" in msg.metadata:
                native_msg["tool_call_id"] = msg.metadata["tool_call_id"]
            
            native.append(native_msg)
        
        return native
    
    def process_chunk(self, state, native_chunk, meta_state):
        """
        Process OpenAI streaming chunk
        native_chunk is the raw SSE data from OpenAI API
        """
        # Extract delta from OpenAI format
        delta = native_chunk.get("choices", [{}])[0].get("delta", {})
        
        # Get incomplete message from metadata
        incomplete = state.metadata.get("incomplete_message", {
            "role": "assistant",
            "content": "",
            "tool_calls": {}
        })
        
        # Accumulate content
        if "content" in delta and delta["content"]:
            incomplete["content"] += delta["content"]
        
        # Accumulate tool calls
        if "tool_calls" in delta:
            for tc in delta["tool_calls"]:
                idx = tc.get("index", 0)
                if idx not in incomplete["tool_calls"]:
                    incomplete["tool_calls"][idx] = {
                        "id": "", "type": "function",
                        "function": {"name": "", "arguments": ""}
                    }
                
                if "id" in tc:
                    incomplete["tool_calls"][idx]["id"] = tc["id"]
                if "function" in tc:
                    if "name" in tc["function"]:
                        incomplete["tool_calls"][idx]["function"]["name"] = tc["function"]["name"]
                    if "arguments" in tc["function"]:
                        incomplete["tool_calls"][idx]["function"]["arguments"] += tc["function"]["arguments"]
        
        # Check if complete
        finish_reason = native_chunk.get("choices", [{}])[0].get("finish_reason")
        
        if finish_reason:
            # Create completed message
            msg_metadata = {}
            if incomplete["tool_calls"]:
                msg_metadata["tool_calls"] = list(incomplete["tool_calls"].values())
            
            new_message = Message(
                role="assistant",
                content=incomplete["content"],
                metadata=msg_metadata
            )
            
            # Add to conversation, clear incomplete from metadata
            new_metadata = {k: v for k, v in state.metadata.items() 
                          if k != "incomplete_message"}
            
            return ConversationState(
                messages=state.messages + (new_message,),
                metadata=new_metadata
            )
        else:
            # Update incomplete in metadata
            return ConversationState(
                messages=state.messages,
                metadata={**state.metadata, "incomplete_message": incomplete}
            )
```

## Common Operations (Pure Functions)

These operate on messages after compatibility transformation:

```python
# Trimming functions
trim_by_count(max_count, keep_system=True)
    → (messages → messages)

trim_by_tokens(max_tokens, token_counter, keep_system=True)
    → (messages → messages)

# Filtering functions  
filter_by_role(*roles)
    → (messages → messages)

filter_by_predicate(predicate)
    → (messages → messages)

# Composition
pipeline = compose(
    trim_by_count(100),
    filter_by_role("user", "assistant"),
    trim_by_tokens(8000, token_counter)
)

result_messages = pipeline(input_messages)
```

## Core System Responsibilities

**During Initialization:**
- Plugin registration and loading
- Configuration schema merging and validation
- Calling `provider.init(model, config)` - **once per session**
- Making any API calls required by init
- Storing meta_state
- Creating capability query callback
- Collecting transformation functions from features

**During Runtime:**
- HTTP requests and streaming
- Pipeline orchestration
- State management (immutable updates)
- Error handling and retries
- Applying transformation functions in correct order

**Not Core's Job:**
- Understanding provider-specific formats
- Understanding feature-specific logic
- Capability determination (providers do this)
- Message format conversions (providers do this)

## Plugin Responsibilities

**Providers:**
- Initialize once (`init`) with capability detection
- Declare what capabilities they support (`can_handle`)
- Convert between universal and native message formats
- Build request bodies
- Process native responses/chunks
- Handle all provider-specific details

**Features:**
- Define configuration requirements
- Check capabilities via callback
- Return transformation functions after capability checking
- Use higher-order functions to avoid repeated checks
- Transform messages, requests, displays
- Work across multiple providers with different protocols

## Benefits of This Architecture

1. **Pure Functional Flow**: No hidden state, all transformations explicit
2. **Dynamic Metadata**: Free-form dict stores any needed state
3. **Capability-Driven**: Features adapt based on provider capabilities
4. **Provider Isolation**: Provider details never leak to core or features
5. **Feature Flexibility**: Same feature works across providers differently
6. **Minimal Core**: Core doesn't understand provider or feature specifics
7. **Higher-Order Functions**: Capability checks once, apply transforms many times
8. **Composability**: Pure functions compose naturally
9. **Extensibility**: Add providers/features without core changes
10. **Testability**: Pure functions with no side effects

## Implementation Notes

**These are rough conceptual examples. Real implementation will differ based on:**

- Specific language features and idioms
- Performance requirements (e.g., caching, memoization)
- Type system constraints
- Error handling strategies
- Concurrency model
- Testing framework integration
- Actual provider API variations

**Higher-order function pattern:** Functions can close over data from `init()` and capability checks, avoiding redundant parameter passing. The examples above show direct parameter passing for clarity, but production code would likely use closures.

**Metadata flexibility:** The free-form metadata dict allows any plugin to store arbitrary state without core system changes. This includes incomplete messages during streaming, citations, reasoning traces, provider-specific state, etc.

**No strict types for native formats:** Provider-specific chunk and response formats are not standardized - each provider handles its own API format directly.

---

## 👤 You ##

Calling http or in any way initiating LLM api should be done by the provider plugin, of course, clearly separated from pure functions.

---

## Assistant · *Claude 4 Sonnet* ##

# AI Agent Platform - Modular Functional Architecture

## High-Level Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Core System                              │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Configuration Manager                        │  │
│  │  - Merges schemas from providers & features              │  │
│  │  - Validates configuration                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Plugin Orchestration System                    │  │
│  │  - Calls provider.init() during setup                    │  │
│  │  - Stores meta_state from initialization                 │  │
│  │  - Orchestrates transformation pipeline                  │  │
│  │  - Does NOT make API calls                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Processing Pipeline                          │  │
│  │  - Composes provider + feature transformations           │  │
│  │  - Manages conversation state (immutable messages)       │  │
│  │  - Maintains free metadata dict for any dynamic state    │  │
│  │  - Delegates I/O to provider plugins                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Message Transformation Pipeline                 │  │
│  │  - to_compatibility / from_compatibility                 │  │
│  │  - Applies common operations (trim, filter)              │  │
│  │  - Pure functional transformations                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │
        ┌─────────────────────┴──────────────────────┐
        │                                             │
        ▼                                             ▼
┌───────────────────┐                        ┌───────────────────┐
│  Provider Plugin  │                        │  Feature Plugin   │
│                   │                        │                   │
│ Pure Functions:   │◄───can_handle()────────│ Pure Functions:   │
│ - init()          │                        │ - Transforms      │
│ - can_handle()    │                        │ - Modifiers       │
│ - Conversions     │                        │                   │
│ - Processing      │                        │ All pure, no I/O  │
│                   │                        │                   │
│ I/O Functions:    │                        └───────────────────┘
│ - call_api()      │
│ - stream_api()    │
│                   │
└───────────────────┘
```

## Core Principles

### 1. **Clear Separation: Pure Functions vs I/O**

**Provider Plugin has TWO distinct parts:**

```
Provider Plugin
├── Pure Functions (no side effects)
│   ├── init() → meta_state
│   ├── can_handle(capability, meta_state) → bool
│   ├── to_native_messages(messages, meta_state) → native_messages
│   ├── from_native_messages(native_messages, meta_state) → messages
│   ├── build_request_body(native_messages, config, meta_state) → body
│   ├── process_chunk(state, native_chunk, meta_state) → new_state
│   ├── process_response(state, native_response, meta_state) → new_state
│   └── to_display_format(message, meta_state) → display_dict
│
└── I/O Functions (side effects - HTTP/API calls)
    ├── detect_capabilities(model_id, config) → capabilities
    ├── call_api(body, config) → response
    └── stream_api(body, config) → Iterator[chunk]
```

**Core System:**
- Orchestrates the flow
- Calls pure functions
- Calls I/O functions when needed
- Does NOT make HTTP requests itself
- Does NOT know about provider-specific APIs

### 2. **Provider Owns All API Communication**

```
Provider is responsible for:
- Authentication (API keys, tokens, etc.)
- Request formatting (headers, body structure)
- HTTP/HTTPS communication
- Streaming protocol (SSE, websockets, etc.)
- Retry logic and error handling
- Rate limiting
- Timeouts
- Provider-specific quirks

Core system just calls provider methods.
```

### 3. **Immutable Message Flow with Dynamic Metadata**

```
ConversationState:
  - messages: Tuple[Message, ...] (immutable)
  - metadata: Dict[str, Any] (free-form, stores any state)
    - incomplete_message (for streaming)
    - citations (from features)
    - reasoning_traces (from features)
    - provider_state (from provider)
    - feature_state (from features)
    - ... (anything)
```

### 4. **Capability-Based Feature Application**

Features query providers through callbacks:

```
Feature needs web_search capability
    ↓
Feature: can_handle_fn("web_search")
    ↓
Core → Provider.can_handle("web_search", meta_state)
    ↓
Provider: Returns bool (pure function)
    ↓
Feature: Proceeds or skips
```

### 5. **Provider Initialization**

```python
# Core calls during setup
meta_state = provider.init(model_id, config)

# If capability detection needed, provider does it:
if needs_detection:
    capabilities = provider.detect_capabilities(model_id, config)
    # Provider makes API call inside detect_capabilities()
    meta_state["capabilities"] = capabilities

# meta_state is stored by core and passed to pure functions
```

## Component Interfaces

### Provider Plugin Interface

```python
ProviderPlugin:
    # Identity
    .name: str
    
    # ========================================
    # PURE FUNCTIONS (no I/O, no side effects)
    # ========================================
    
    # Initialization (returns data, may need I/O call first)
    .init(model_id, config) → meta_state: Dict[str, Any]
        # - Builds initial meta_state
        # - May call detect_capabilities() if needed
        # - Returns free-form dict with capabilities and any data
    
    # Capability Queries
    .can_handle(capability_id, meta_state) → bool
        # - Pure function using meta_state from init()
    
    # Configuration
    .get_config_schema() → Dict
    
    # Message Conversion
    .to_native_messages(messages, meta_state) → native_messages
    .from_native_messages(native_messages, meta_state) → messages
    
    # Request Building
    .build_request_body(native_messages, config, meta_state) → body
    
    # Response Processing
    .process_chunk(conversation_state, native_chunk, meta_state) 
        → new_conversation_state
        
    .process_response(conversation_state, native_response, meta_state)
        → new_conversation_state
    
    # Display
    .to_display_format(message, meta_state) → display_dict
    
    # ========================================
    # I/O FUNCTIONS (side effects, HTTP calls)
    # ========================================
    
    # Capability Detection (makes API call if needed)
    .detect_capabilities(model_id, config) → Dict[str, Any]
        # - Makes HTTP request to provider API
        # - Detects model capabilities
        # - Returns capability information
        # - Called during init() if needed
    
    # API Communication
    .call_api(request_body, config, meta_state) → response
        # - Makes HTTP request to LLM API
        # - Handles authentication
        # - Handles provider-specific networking
        # - Returns native response
    
    .stream_api(request_body, config, meta_state) → Iterator[native_chunk]
        # - Makes streaming HTTP request
        # - Handles SSE/websocket protocol
        # - Yields native chunks as they arrive
        # - Handles connection management
```

### Feature Plugin Interface

```python
FeaturePlugin:
    # Identity
    .name: str
    
    # Configuration
    .get_config_schema() → Dict
    .get_ui_elements() → List[UIElement]
    
    # ========================================
    # ALL PURE FUNCTIONS
    # (Features never do I/O)
    # ========================================
    
    # Transformation Functions Return Functions
    # Each returns Optional[TransformFunction]
    
    .get_request_modifier(can_handle_fn, config, meta_state) 
        → Optional[body → body]
        
    .get_chunk_processor(can_handle_fn, config, meta_state)
        → Optional[(state, chunk) → state]
        
    .get_to_compatibility_transform(can_handle_fn, config, meta_state)
        → Optional[message → message]
        
    .get_from_compatibility_transform(can_handle_fn, config, meta_state)
        → Optional[message → message]
        
    .get_display_modifier(can_handle_fn, config, meta_state)
        → Optional[(display, message) → display]
```

## Data Structures

```python
Message (immutable):
    - role: str
    - content: str
    - metadata: Dict[str, Any]  # Free-form

ConversationState (immutable):
    - messages: Tuple[Message, ...]
    - metadata: Dict[str, Any]  # Free-form dynamic state

Config (immutable):
    - values: Dict[str, Any]
```

## Request Flow Architecture

### Phase 1: System Initialization

```
1. Core loads provider and feature plugins
2. User provides configuration (provider, model, keys, etc.)
3. Core validates configuration against merged schema
4. Core calls provider.init(model_id, config):
   
   Inside provider.init():
   - Provider checks if capabilities need detection
   - If yes: provider calls its own detect_capabilities()
   - Provider.detect_capabilities() makes HTTP request
   - Provider builds meta_state with capabilities
   - Returns meta_state to core
   
5. Core stores meta_state
6. Core creates can_handle_fn = lambda cap: provider.can_handle(cap, meta_state)
```

### Phase 2: Feature Initialization

```
For each feature:
1. Feature calls can_handle_fn to check applicability
2. Feature returns transformation functions (all pure):
   - request_modifier = feature.get_request_modifier(...)
   - chunk_processor = feature.get_chunk_processor(...)
   - to_compat = feature.get_to_compatibility_transform(...)
   - from_compat = feature.get_from_compatibility_transform(...)
   - display_modifier = feature.get_display_modifier(...)
3. Core stores these functions for pipeline
```

### Phase 3: Request Preparation

```
User message arrives
    ↓
Add to ConversationState.messages (immutable)
    ↓
Apply transformations (all pure functions):

messages
→ Apply to_compat transforms from features
→ Apply common operations (trim_by_tokens, filter, etc.)
→ Apply from_compat transforms from features (reverse order)
→ Provider.to_native_messages(messages, meta_state)
→ Provider.build_request_body(native_messages, config, meta_state)
→ Apply request_modifiers from features
    ↓
Final request body ready for API
```

### Phase 4: API Call (Provider Responsibility)

```
Core orchestrates, Provider executes:

if streaming:
    chunk_iterator = provider.stream_api(request_body, config, meta_state)
    # Provider makes streaming HTTP request
    # Provider handles SSE/websocket
    # Provider yields chunks
    
    for native_chunk in chunk_iterator:
        # Continue to Phase 5
        
else:
    native_response = provider.call_api(request_body, config, meta_state)
    # Provider makes HTTP request
    # Provider handles response
    # Provider returns complete response
    
    # Continue to Phase 5
```

**Key Point:** The provider plugin contains the actual HTTP client code. Core just calls provider methods.

### Phase 5: Response Processing

```
For each native chunk/response:
    ↓
Provider.process_chunk(state, native_chunk, meta_state)  [pure function]
    → Returns new state with updated metadata
    ↓
Apply chunk_processors from applicable features  [pure functions]
    → Each updates state.metadata with feature-specific data
    ↓
Check state.metadata for completed messages
    ↓
If tool calls detected → Loop back to Phase 3
If complete → Continue
```

### Phase 6: Display Formatting

```
For each message:
    ↓
display = Provider.to_display_format(message, meta_state)  [pure]
    ↓
Apply display_modifiers from applicable features  [pure]
    → Each enhances display dict
    ↓
Return to UI
```

## Example: Provider with I/O Separation

*Note: This is a conceptual example. Real implementation may differ.*

```python
class OpenAIProvider:
    name = "openai"
    
    # ========================================
    # PURE FUNCTIONS
    # ========================================
    
    def init(self, model_id, config):
        """
        Initialize provider - may call I/O functions
        Returns meta_state dict
        """
        # Static capabilities
        capabilities = self._get_static_capabilities(model_id)
        
        # Detect if unknown model
        if model_id not in self._known_models:
            # Call I/O function to detect
            detected = self.detect_capabilities(model_id, config)
            if detected:
                capabilities.extend(detected.get("capabilities", []))
        
        # Return free-form meta_state
        return {
            "model_id": model_id,
            "capabilities": capabilities,
            "context_window": self._get_context_window(model_id),
            "api_version": "v1",
            # ... any other data
        }
    
    def can_handle(self, capability_id, meta_state):
        """Pure function - check capability"""
        return capability_id in meta_state.get("capabilities", [])
    
    def get_config_schema(self):
        """Pure function - return schema"""
        return {
            "api_key": {"type": "string", "required": True},
            "model": {"type": "string", "required": True},
            "base_url": {"type": "string", "default": "https://api.openai.com/v1"},
            "timeout": {"type": "number", "default": 30}
        }
    
    def to_native_messages(self, messages, meta_state):
        """Pure function - convert to OpenAI format"""
        native = []
        for msg in messages:
            native_msg = {
                "role": msg.role,
                "content": msg.content
            }
            if "tool_calls" in msg.metadata:
                native_msg["tool_calls"] = msg.metadata["tool_calls"]
            if "tool_call_id" in msg.metadata:
                native_msg["tool_call_id"] = msg.metadata["tool_call_id"]
            native.append(native_msg)
        return native
    
    def build_request_body(self, native_messages, config, meta_state):
        """Pure function - build request"""
        return {
            "model": meta_state["model_id"],
            "messages": native_messages,
            "stream": config.get("stream", False)
        }
    
    def process_chunk(self, state, native_chunk, meta_state):
        """Pure function - process chunk"""
        delta = native_chunk.get("choices", [{}])[0].get("delta", {})
        
        incomplete = state.metadata.get("incomplete_message", {
            "role": "assistant", "content": "", "tool_calls": {}
        })
        
        # Accumulate content
        if "content" in delta and delta["content"]:
            incomplete["content"] += delta["content"]
        
        # Check if complete
        finish_reason = native_chunk.get("choices", [{}])[0].get("finish_reason")
        
        if finish_reason:
            # Create completed message
            new_message = Message(
                role="assistant",
                content=incomplete["content"],
                metadata={}
            )
            
            return ConversationState(
                messages=state.messages + (new_message,),
                metadata={k: v for k, v in state.metadata.items() 
                         if k != "incomplete_message"}
            )
        else:
            return ConversationState(
                messages=state.messages,
                metadata={**state.metadata, "incomplete_message": incomplete}
            )
    
    # ========================================
    # I/O FUNCTIONS
    # ========================================
    
    def detect_capabilities(self, model_id, config):
        """
        I/O function - makes HTTP request to detect capabilities
        """
        import requests
        
        api_key = config.get("api_key")
        base_url = config.get("base_url", "https://api.openai.com/v1")
        
        try:
            response = requests.get(
                f"{base_url}/models/{model_id}",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                timeout=config.get("timeout", 30)
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse capabilities from API response
                capabilities = ["text_generation", "streaming"]
                
                if "gpt-4" in model_id:
                    capabilities.extend(["tool_calling", "json_mode"])
                
                if data.get("capabilities", {}).get("vision"):
                    capabilities.append("vision")
                
                return {
                    "capabilities": capabilities,
                    "model_data": data
                }
                
        except Exception as e:
            print(f"Failed to detect capabilities: {e}")
        
        return None
    
    def call_api(self, request_body, config, meta_state):
        """
        I/O function - makes HTTP request to OpenAI API
        Returns complete response
        """
        import requests
        
        api_key = config.get("api_key")
        base_url = config.get("base_url", "https://api.openai.com/v1")
        timeout = config.get("timeout", 30)
        
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=request_body,
            timeout=timeout
        )
        
        response.raise_for_status()
        return response.json()
    
    def stream_api(self, request_body, config, meta_state):
        """
        I/O function - makes streaming HTTP request
        Yields native chunks as they arrive
        """
        import requests
        import json
        
        api_key = config.get("api_key")
        base_url = config.get("base_url", "https://api.openai.com/v1")
        timeout = config.get("timeout", 30)
        
        # Ensure streaming is enabled
        request_body = {**request_body, "stream": True}
        
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=request_body,
            stream=True,
            timeout=timeout
        )
        
        response.raise_for_status()
        
        # Parse SSE stream
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    try:
                        chunk = json.loads(data)
                        yield chunk  # Yield native OpenAI chunk
                    except json.JSONDecodeError:
                        continue
    
    # ========================================
    # HELPER FUNCTIONS (pure)
    # ========================================
    
    def _get_static_capabilities(self, model_id):
        """Pure helper - return known capabilities"""
        model_caps = {
            "gpt-4o": [
                "text_generation", "streaming", "tool_calling",
                "vision", "audio_input", "audio_output"
            ],
            "gpt-4-search": [
                "text_generation", "streaming", "tool_calling",
                "web_search", "openai_search_protocol", "citations"
            ],
        }
        return model_caps.get(model_id, ["text_generation", "streaming"])
    
    def _get_context_window(self, model_id):
        """Pure helper - return context window size"""
        windows = {
            "gpt-4": 8192,
            "gpt-4-turbo": 128000,
            "gpt-4o": 128000,
        }
        return windows.get(model_id, 4096)
```

## Example: Core Orchestration

*Note: This is a conceptual example. Real implementation may differ.*

```python
class AgentCore:
    """
    Core orchestrator - does NOT make HTTP requests
    Delegates I/O to provider plugins
    """
    
    def __init__(self):
        self.providers = {}
        self.features = {}
    
    def register_provider(self, provider):
        self.providers[provider.name] = provider
    
    def register_feature(self, feature):
        self.features[feature.name] = feature
    
    def create_session(self, config):
        """
        Initialize a session
        Core orchestrates, provider does I/O
        """
        provider_name = config.get("provider")
        model_id = config.get("model")
        
        provider = self.providers[provider_name]
        
        # Provider handles its own initialization (may include API calls)
        meta_state = provider.init(model_id, config)
        
        # Create capability callback
        can_handle_fn = lambda cap: provider.can_handle(cap, meta_state)
        
        # Initialize features (all pure)
        feature_transforms = {}
        for feature_name, feature in self.features.items():
            if config.get(f"{feature_name}_enabled"):
                transforms = {
                    "request_modifier": feature.get_request_modifier(
                        can_handle_fn, config, meta_state
                    ),
                    "chunk_processor": feature.get_chunk_processor(
                        can_handle_fn, config, meta_state
                    ),
                    # ... other transforms
                }
                feature_transforms[feature_name] = transforms
        
        return Session(
            provider=provider,
            config=config,
            meta_state=meta_state,
            feature_transforms=feature_transforms
        )


class Session:
    """
    Active session - orchestrates flow
    Does NOT make HTTP requests
    """
    
    def __init__(self, provider, config, meta_state, feature_transforms):
        self.provider = provider
        self.config = config
        self.meta_state = meta_state
        self.feature_transforms = feature_transforms
        self.conversation = ConversationState(messages=(), metadata={})
    
    def send_message(self, user_message):
        """
        Send a message (non-streaming)
        Orchestrates flow, provider handles I/O
        """
        # Add user message
        msg = Message(role="user", content=user_message, metadata={})
        self.conversation = ConversationState(
            messages=self.conversation.messages + (msg,),
            metadata=self.conversation.metadata
        )
        
        # Prepare request (all pure functions)
        native_messages = self.provider.to_native_messages(
            self.conversation.messages,
            self.meta_state
        )
        
        body = self.provider.build_request_body(
            native_messages,
            self.config,
            self.meta_state
        )
        
        # Apply feature modifiers (pure)
        for transforms in self.feature_transforms.values():
            modifier = transforms.get("request_modifier")
            if modifier:
                body = modifier(body)
        
        # Provider makes API call (I/O)
        native_response = self.provider.call_api(
            body,
            self.config,
            self.meta_state
        )
        
        # Process response (pure)
        self.conversation = self.provider.process_response(
            self.conversation,
            native_response,
            self.meta_state
        )
        
        # Return last message
        return self.conversation.messages[-1]
    
    def send_message_stream(self, user_message):
        """
        Send a message (streaming)
        Yields content as it arrives
        """
        # Add user message
        msg = Message(role="user", content=user_message, metadata={})
        self.conversation = ConversationState(
            messages=self.conversation.messages + (msg,),
            metadata=self.conversation.metadata
        )
        
        # Prepare request (pure)
        native_messages = self.provider.to_native_messages(
            self.conversation.messages,
            self.meta_state
        )
        
        body = self.provider.build_request_body(
            native_messages,
            self.config,
            self.meta_state
        )
        
        # Apply feature modifiers (pure)
        for transforms in self.feature_transforms.values():
            modifier = transforms.get("request_modifier")
            if modifier:
                body = modifier(body)
        
        # Provider streams API (I/O - returns iterator)
        chunk_iterator = self.provider.stream_api(
            body,
            self.config,
            self.meta_state
        )
        
        # Process chunks as they arrive
        for native_chunk in chunk_iterator:
            # Process chunk (pure)
            prev_state = self.conversation
            self.conversation = self.provider.process_chunk(
                self.conversation,
                native_chunk,
                self.meta_state
            )
            
            # Apply feature processors (pure)
            for transforms in self.feature_transforms.values():
                processor = transforms.get("chunk_processor")
                if processor:
                    self.conversation = processor(
                        self.conversation,
                        native_chunk
                    )
            
            # Yield content delta
            incomplete = self.conversation.metadata.get("incomplete_message", {})
            if incomplete:
                content = incomplete.get("content", "")
                prev_incomplete = prev_state.metadata.get("incomplete_message", {})
                prev_content = prev_incomplete.get("content", "")
                
                if len(content) > len(prev_content):
                    delta = content[len(prev_content):]
                    yield delta
```

## Core System Responsibilities

**Core orchestrates but does NOT make HTTP requests:**

- Plugin registration and loading
- Configuration schema merging and validation
- Calling `provider.init()` to get meta_state
- Creating capability query callbacks
- Collecting transformation functions from features
- Orchestrating the transformation pipeline
- Calling `provider.call_api()` or `provider.stream_api()`
- Managing conversation state (immutable updates)
- Applying pure transformation functions

**Core does NOT:**
- Make HTTP/HTTPS requests
- Understand provider API formats
- Handle authentication or networking
- Know about SSE, websockets, or streaming protocols

## Provider Plugin Responsibilities

**Pure Functions:**
- Initialize meta_state
- Check capabilities
- Convert message formats
- Build request bodies
- Process responses/chunks
- Format for display

**I/O Functions:**
- Make HTTP/HTTPS requests to LLM APIs
- Handle authentication (API keys, tokens, etc.)
- Implement streaming protocols (SSE, websockets)
- Handle retries, timeouts, rate limiting
- Detect capabilities via API calls
- Manage connections

## Feature Plugin Responsibilities

**All Pure Functions (no I/O):**
- Define configuration requirements
- Check capabilities via callback
- Return transformation functions
- Transform messages, requests, displays
- Work across multiple providers

## Benefits of This Architecture

1. **Clear I/O Separation**: Provider owns all networking, features are pure
2. **Provider Autonomy**: Each provider handles its own API specifics
3. **Minimal Core**: Core orchestrates without understanding provider details
4. **Pure Functional Flow**: All transformations except API calls are pure
5. **Testability**: Pure functions easy to test, I/O isolated in providers
6. **Flexibility**: Providers can implement any networking strategy
7. **No Core Changes**: Adding providers with different APIs needs no core changes
8. **Dynamic Metadata**: Free-form dict stores any needed state
9. **Composability**: Pure functions compose naturally
10. **Extensibility**: Add providers/features without coupling

## Implementation Notes

**These are rough conceptual examples. Real implementation will differ based on:**

- Specific language features and idioms
- HTTP client library choices (requests, httpx, aiohttp, etc.)
- Async/await patterns vs synchronous
- Performance requirements
- Error handling strategies  
- Retry and backoff policies
- Connection pooling
- Streaming protocol implementations
- Type system constraints

**Key architectural point:** Provider plugins contain actual HTTP client code. Core system never makes API requests - it only calls provider methods and orchestrates the flow of pure transformations.

---

## 👤 You ##

I want the core to be developed in both python and javascript, and at the same time I want it to support plugins in both languages. Given the API specifics what are ways to support plugins in different languages? Any obstacles?

---

## Assistant · *Claude 4 Sonnet* ##

# Cross-Language Plugin Support - Architecture Considerations

## Fundamental Challenge

Your architecture requires:
- **Core in Python AND JavaScript** (two implementations)
- **Plugins potentially in either language**
- **High frequency calls** (pure functions called per message/chunk)
- **Low frequency calls** (I/O functions called per API request)
- **Complex data** (immutable state, nested structures)
- **Streaming** (iterators/generators)

## Approaches for Cross-Language Support

### Approach 1: Separate Native Ecosystems ⭐ Recommended

```
Python Core ←→ Python Plugins
JavaScript Core ←→ JavaScript Plugins

No cross-language calls
```

**Pros:**
- Maximum performance (no serialization overhead)
- Native idioms (generators, async/await, type hints)
- Simple error handling
- No process overhead
- Natural for each ecosystem

**Cons:**
- Plugin developers must write plugins twice
- Feature parity challenges between languages
- Duplicate maintenance

**When to use:** This should be the **default mode**. Most plugins stay in their native language.

### Approach 2: Subprocess Protocol (Hybrid)

```
Python Core ←→ Python Plugin (native, fast)
           ←→ JS Plugin (subprocess, stdio JSON-RPC)

JavaScript Core ←→ JS Plugin (native, fast)
                ←→ Python Plugin (subprocess, stdio JSON-RPC)
```

**Architecture:**

```
┌─────────────────┐
│   Core (Py/JS)  │
└────────┬────────┘
         │
    ┌────┴─────┐
    │          │
    ▼          ▼
┌────────┐  ┌──────────────────┐
│Native  │  │ Plugin Adapter   │
│Plugin  │  │                  │
└────────┘  │ ┌──────────────┐ │
            │ │  Subprocess  │ │
            │ │  (stdin/out) │ │
            │ │              │ │
            │ │  ┌─────────┐ │ │
            │ │  │ Plugin  │ │ │
            │ │  │(other   │ │ │
            │ │  │language)│ │ │
            │ │  └─────────┘ │ │
            │ └──────────────┘ │
            └──────────────────┘
```

**Protocol: JSON-RPC over stdin/stdout**

```json
// Request
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "provider.can_handle",
  "params": {
    "capability_id": "web_search",
    "meta_state": {...}
  }
}

// Response
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": true
}
```

**Pros:**
- Language agnostic
- Simple protocol
- No network overhead
- Works with any language that can read stdin/write stdout
- Process isolation (plugin crash doesn't crash core)

**Cons:**
- Serialization overhead
- Process startup time
- Streaming more complex
- Can't share memory

**When to use:** When you need a specific plugin in the non-native language (e.g., Python core needs a JS-only plugin).

### Approach 3: HTTP/gRPC Microservices

```
Core (Py/JS) ←→ HTTP ←→ Plugin Service (any language)
```

**Pros:**
- True language independence
- Can run plugins remotely
- Easy horizontal scaling
- Standard protocols

**Cons:**
- High latency (network round-trip)
- Complex deployment
- Overkill for local use case
- State management challenges

**When to use:** Not recommended for local MVP. Consider for cloud/enterprise deployments.

### Approach 4: WebAssembly (Future)

```
Core (Py/JS) ←→ WASM Plugin
                   ↑
            (compiled from Rust, C++, etc.)
```

**Pros:**
- Near-native performance
- True sandboxing
- Works in Python (wasmer/wasmtime) and JS (native)

**Cons:**
- Plugins can't make HTTP requests directly (need host functions)
- Limited language support (mainly Rust, C++, AssemblyScript)
- Still immature for Python
- Complex build process

**When to use:** Consider for future if sandboxing/security becomes critical.

## Recommended Architecture: Hybrid Native + Subprocess

### Default: Native Plugins

**Python Core:**
```python
# Direct import, zero overhead
from plugins.openai_provider import OpenAIProvider

provider = OpenAIProvider()
meta_state = provider.init(model_id, config)  # Native call
```

**JavaScript Core:**
```javascript
// Direct import, zero overhead
import { OpenAIProvider } from './plugins/openai-provider.js';

const provider = new OpenAIProvider();
const metaState = await provider.init(modelId, config);  // Native call
```

### Optional: Cross-Language Bridge

**Core provides adapter for cross-language plugins:**

```python
# Python Core using JavaScript plugin via subprocess
from core.plugin_bridge import SubprocessPlugin

provider = SubprocessPlugin(
    command=['node', 'plugins/js-plugin.js'],
    protocol='json-rpc'
)

# Looks like native plugin to core
meta_state = provider.init(model_id, config)  # Serialized call via subprocess
```

```javascript
// JavaScript Core using Python plugin via subprocess
import { SubprocessPlugin } from './core/plugin-bridge.js';

const provider = new SubprocessPlugin({
    command: ['python', 'plugins/py-plugin.py'],
    protocol: 'json-rpc'
});

// Looks like native plugin to core
const metaState = await provider.init(modelId, config);  // Serialized call
```

## Technical Implementation Details

### 1. Plugin Protocol Definition

Define plugin interface in language-agnostic format:

**`plugin-protocol.yaml`** (or JSON Schema)

```yaml
ProviderPlugin:
  methods:
    init:
      input:
        model_id: string
        config: object
      output:
        meta_state: object
    
    can_handle:
      input:
        capability_id: string
        meta_state: object
      output:
        result: boolean
    
    to_native_messages:
      input:
        messages: array[Message]
        meta_state: object
      output:
        native_messages: array[object]
    
    # ... etc.
```

### 2. Subprocess Plugin Adapter

**Python Implementation:**

```python
import json
import subprocess
from typing import Dict, Any, Iterator

class SubprocessPlugin:
    """
    Adapter that makes subprocess plugin look like native plugin
    """
    
    def __init__(self, command: list[str], protocol: str = 'json-rpc'):
        self.command = command
        self.process = None
        self.request_id = 0
        self._start_process()
    
    def _start_process(self):
        """Start plugin subprocess"""
        self.process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
    
    def _call(self, method: str, params: Dict[str, Any]) -> Any:
        """Make JSON-RPC call to subprocess"""
        self.request_id += 1
        
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params
        }
        
        # Send request
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        
        # Read response
        response_line = self.process.stdout.readline()
        response = json.loads(response_line)
        
        if "error" in response:
            raise Exception(f"Plugin error: {response['error']}")
        
        return response.get("result")
    
    # Implement plugin interface by delegating to subprocess
    
    def init(self, model_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        return self._call("init", {"model_id": model_id, "config": config})
    
    def can_handle(self, capability_id: str, meta_state: Dict[str, Any]) -> bool:
        return self._call("can_handle", {
            "capability_id": capability_id,
            "meta_state": meta_state
        })
    
    def to_native_messages(self, messages: tuple, meta_state: Dict[str, Any]) -> list:
        # Serialize messages to dict
        serialized = [
            {"role": m.role, "content": m.content, "metadata": m.metadata}
            for m in messages
        ]
        return self._call("to_native_messages", {
            "messages": serialized,
            "meta_state": meta_state
        })
    
    def stream_api(self, body: Dict, config: Dict, meta_state: Dict) -> Iterator:
        """
        Streaming is more complex - need to handle multiple responses
        """
        self.request_id += 1
        
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "stream_api",
            "params": {"body": body, "config": config, "meta_state": meta_state}
        }
        
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        
        # Read multiple responses for streaming
        while True:
            line = self.process.stdout.readline()
            if not line:
                break
            
            response = json.loads(line)
            
            if response.get("id") != self.request_id:
                continue
            
            if "result" in response:
                if response["result"].get("done"):
                    break
                yield response["result"].get("chunk")
    
    def __del__(self):
        """Cleanup subprocess"""
        if self.process:
            self.process.terminate()
            self.process.wait()
```

**JavaScript Implementation:**

```javascript
import { spawn } from 'child_process';
import { createInterface } from 'readline';

class SubprocessPlugin {
  constructor({ command, protocol = 'json-rpc' }) {
    this.command = command;
    this.process = null;
    this.requestId = 0;
    this.pendingRequests = new Map();
    this._startProcess();
  }
  
  _startProcess() {
    const [cmd, ...args] = this.command;
    this.process = spawn(cmd, args, {
      stdio: ['pipe', 'pipe', 'pipe']
    });
    
    // Setup response handler
    const readline = createInterface({
      input: this.process.stdout
    });
    
    readline.on('line', (line) => {
      const response = JSON.parse(line);
      const { id, result, error } = response;
      
      const pending = this.pendingRequests.get(id);
      if (pending) {
        if (error) {
          pending.reject(new Error(error.message));
        } else {
          pending.resolve(result);
        }
        this.pendingRequests.delete(id);
      }
    });
  }
  
  async _call(method, params) {
    this.requestId++;
    const id = this.requestId;
    
    const request = {
      jsonrpc: '2.0',
      id,
      method,
      params
    };
    
    return new Promise((resolve, reject) => {
      this.pendingRequests.set(id, { resolve, reject });
      this.process.stdin.write(JSON.stringify(request) + '\n');
    });
  }
  
  // Implement plugin interface
  
  async init(modelId, config) {
    return this._call('init', { model_id: modelId, config });
  }
  
  async canHandle(capabilityId, metaState) {
    return this._call('can_handle', {
      capability_id: capabilityId,
      meta_state: metaState
    });
  }
  
  async toNativeMessages(messages, metaState) {
    const serialized = messages.map(m => ({
      role: m.role,
      content: m.content,
      metadata: m.metadata
    }));
    
    return this._call('to_native_messages', {
      messages: serialized,
      meta_state: metaState
    });
  }
  
  async* streamApi(body, config, metaState) {
    // Streaming implementation
    this.requestId++;
    const id = this.requestId;
    
    const request = {
      jsonrpc: '2.0',
      id,
      method: 'stream_api',
      params: { body, config, meta_state: metaState }
    };
    
    this.process.stdin.write(JSON.stringify(request) + '\n');
    
    // Yield chunks as they arrive
    const readline = createInterface({ input: this.process.stdout });
    
    for await (const line of readline) {
      const response = JSON.parse(line);
      if (response.id === id) {
        if (response.result?.done) break;
        if (response.result?.chunk) {
          yield response.result.chunk;
        }
      }
    }
  }
  
  destroy() {
    if (this.process) {
      this.process.kill();
    }
  }
}
```

### 3. Plugin Executable (Subprocess Side)

**Python plugin as subprocess:**

```python
#!/usr/bin/env python3
"""
Plugin that runs as subprocess
Reads JSON-RPC from stdin, writes to stdout
"""

import sys
import json
from actual_plugin import OpenAIProvider

class PluginServer:
    def __init__(self, plugin):
        self.plugin = plugin
    
    def handle_request(self, request):
        """Handle single JSON-RPC request"""
        method = request["method"]
        params = request["params"]
        
        try:
            # Dispatch to plugin method
            if method == "init":
                result = self.plugin.init(params["model_id"], params["config"])
            elif method == "can_handle":
                result = self.plugin.can_handle(
                    params["capability_id"],
                    params["meta_state"]
                )
            elif method == "to_native_messages":
                # Deserialize messages
                messages = params["messages"]  # Dict format
                result = self.plugin.to_native_messages(messages, params["meta_state"])
            elif method == "stream_api":
                # Handle streaming
                for chunk in self.plugin.stream_api(
                    params["body"],
                    params["config"],
                    params["meta_state"]
                ):
                    response = {
                        "jsonrpc": "2.0",
                        "id": request["id"],
                        "result": {"chunk": chunk, "done": False}
                    }
                    print(json.dumps(response), flush=True)
                
                # Final done message
                response = {
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "result": {"done": True}
                }
                return response
            else:
                raise Exception(f"Unknown method: {method}")
            
            return {
                "jsonrpc": "2.0",
                "id": request["id"],
                "result": result
            }
        
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request["id"],
                "error": {
                    "code": -1,
                    "message": str(e)
                }
            }
    
    def run(self):
        """Main loop - read stdin, write stdout"""
        for line in sys.stdin:
            request = json.loads(line)
            response = self.handle_request(request)
            print(json.dumps(response), flush=True)


if __name__ == "__main__":
    plugin = OpenAIProvider()
    server = PluginServer(plugin)
    server.run()
```

**JavaScript plugin as subprocess:**

```javascript
#!/usr/bin/env node
/**
 * Plugin that runs as subprocess
 * Reads JSON-RPC from stdin, writes to stdout
 */

import { createInterface } from 'readline';
import { OpenAIProvider } from './actual-plugin.js';

class PluginServer {
  constructor(plugin) {
    this.plugin = plugin;
  }
  
  async handleRequest(request) {
    const { method, params } = request;
    
    try {
      let result;
      
      switch (method) {
        case 'init':
          result = await this.plugin.init(params.model_id, params.config);
          break;
        
        case 'can_handle':
          result = this.plugin.canHandle(
            params.capability_id,
            params.meta_state
          );
          break;
        
        case 'to_native_messages':
          result = this.plugin.toNativeMessages(
            params.messages,
            params.meta_state
          );
          break;
        
        case 'stream_api':
          // Handle streaming
          for await (const chunk of this.plugin.streamApi(
            params.body,
            params.config,
            params.meta_state
          )) {
            console.log(JSON.stringify({
              jsonrpc: '2.0',
              id: request.id,
              result: { chunk, done: false }
            }));
          }
          
          return {
            jsonrpc: '2.0',
            id: request.id,
            result: { done: true }
          };
        
        default:
          throw new Error(`Unknown method: ${method}`);
      }
      
      return {
        jsonrpc: '2.0',
        id: request.id,
        result
      };
      
    } catch (error) {
      return {
        jsonrpc: '2.0',
        id: request.id,
        error: {
          code: -1,
          message: error.message
        }
      };
    }
  }
  
  async run() {
    const readline = createInterface({
      input: process.stdin,
      output: process.stdout,
      terminal: false
    });
    
    for await (const line of readline) {
      const request = JSON.parse(line);
      const response = await this.handleRequest(request);
      console.log(JSON.stringify(response));
    }
  }
}

const plugin = new OpenAIProvider();
const server = new PluginServer(plugin);
server.run();
```

## Obstacles and Solutions

### Obstacle 1: Performance Overhead

**Problem:** Serializing every function call across process boundary is slow.

**Solutions:**

1. **Keep hot path native:**
   ```
   Pure functions (called frequently) → Native plugins preferred
   I/O functions (called rarely) → Subprocess acceptable
   ```

2. **Batch operations:**
   ```python
   # Instead of multiple calls
   result1 = plugin.process_chunk(state, chunk1, meta)
   result2 = plugin.process_chunk(state, chunk2, meta)
   
   # Batch if subprocess
   results = plugin.process_chunks_batch(state, [chunk1, chunk2], meta)
   ```

3. **Cache capability checks:**
   ```python
   # Check once, store result
   can_search = plugin.can_handle("web_search", meta_state)
   
   # Use cached result in hot loop
   if can_search:
       # ...
   ```

### Obstacle 2: Streaming Complexity

**Problem:** Generators/iterators don't serialize well.

**Solutions:**

1. **Protocol-level streaming:**
   ```json
   // Multiple responses with same request ID
   {"jsonrpc": "2.0", "id": 1, "result": {"chunk": {...}, "done": false}}
   {"jsonrpc": "2.0", "id": 1, "result": {"chunk": {...}, "done": false}}
   {"jsonrpc": "2.0", "id": 1, "result": {"done": true}}
   ```

2. **Keep streaming in same language:**
   ```
   If core needs streaming → prefer native plugin
   If occasional streaming → subprocess acceptable with protocol
   ```

### Obstacle 3: State Serialization

**Problem:** Immutable data structures, complex nested objects, metadata dict.

**Solutions:**

1. **JSON-serializable state only:**
   ```python
   # Good
   meta_state = {
       "capabilities": ["search", "vision"],
       "model_info": {"context": 128000}
   }
   
   # Bad - not serializable
   meta_state = {
       "connection_pool": ConnectionPool(),  # Can't serialize
       "callback": lambda x: x + 1  # Can't serialize
   }
   ```

2. **Subprocess plugins can't have rich state:**
   - Must use primitive types (strings, numbers, dicts, lists)
   - No functions, no class instances
   - This is actually fine for our design since meta_state should be data

### Obstacle 4: Error Handling

**Problem:** Python exceptions vs JavaScript errors, stack traces lost.

**Solutions:**

1. **Structured errors:**
   ```json
   {
     "error": {
       "code": "CAPABILITY_NOT_FOUND",
       "message": "Model doesn't support web_search",
       "details": {
         "model": "gpt-3.5-turbo",
         "requested_capability": "web_search"
       }
     }
   }
   ```

2. **Error logging in subprocess:**
   ```python
   # Plugin logs to stderr (core can capture)
   import sys
   sys.stderr.write(f"Error in plugin: {error}\n")
   ```

### Obstacle 5: Plugin Installation & Discovery

**Problem:** Python plugins use pip, JavaScript plugins use npm.

**Solutions:**

1. **Package conventions:**
   ```
   Python plugins: agent-plugin-{name}
   npm install -g agent-plugin-{name}
   
   JavaScript plugins: @agent-plugin/{name}
   pip install agent-plugin-{name}
   ```

2. **Plugin manifest:**
   ```json
   // plugin.json in each plugin
   {
     "name": "openai-provider",
     "version": "1.0.0",
     "language": "python",
     "executable": "python -m openai_provider.server",
     "capabilities": ["text_generation", "streaming", "tool_calling"]
   }
   ```

3. **Core plugin discovery:**
   ```python
   # Core scans for plugins
   def discover_plugins():
       # Look in standard locations
       paths = [
           "~/.agent-plugins",
           "/usr/local/lib/agent-plugins",
           "./plugins"
       ]
       
       for path in paths:
           for plugin_dir in Path(path).iterdir():
               manifest = plugin_dir / "plugin.json"
               if manifest.exists():
                   yield load_plugin(manifest)
   ```

### Obstacle 6: Async/Await Differences

**Problem:** Python uses `async/await`, JavaScript uses `async/await` (similar but different), subprocess is synchronous protocol.

**Solutions:**

1. **Async subprocess adapter:**
   ```python
   # Python async version
   import asyncio
   
   class AsyncSubprocessPlugin:
       async def init(self, model_id, config):
           # Non-blocking subprocess communication
           return await self._call_async("init", {
               "model_id": model_id,
               "config": config
           })
   ```

2. **Both cores support async plugins:**
   ```python
   # Python core
   if asyncio.iscoroutinefunction(provider.init):
       meta_state = await provider.init(model_id, config)
   else:
       meta_state = provider.init(model_id, config)
   ```

## Recommended Implementation Strategy

### Phase 1: Native Only (MVP)

```
Python Core → Python Plugins
JavaScript Core → JavaScript Plugins

No cross-language support yet
```

**Benefits:**
- Fastest development
- Best performance
- Natural idioms
- Easy debugging

**Plugin developers write once for their preferred language.**

### Phase 2: Subprocess Bridge (Optional)

```
Python Core → Python Plugins (native)
           → JavaScript Plugins (subprocess, optional)

JavaScript Core → JavaScript Plugins (native)
                → Python Plugins (subprocess, optional)
```

**Benefits:**
- Flexibility for users who need specific plugins
- Plugin reuse when needed
- Still performant for native case

**Provide:**
- `SubprocessPlugin` adapter in both cores
- Plugin server template for both languages
- Documentation for cross-language plugins

### Phase 3: Plugin Registry (Future)

```
Central registry:
- openai-provider (Python, JavaScript)
- anthropic-provider (Python, JavaScript)
- web-search-feature (JavaScript only)
- custom-provider (Python only)

Core auto-selects:
- Native plugin if available
- Subprocess plugin if needed
- Downloads and installs automatically
```

## Example Configuration

**User's config (language-agnostic):**

```yaml
# config.yaml
provider: openai
model: gpt-4o
api_key: sk-...

features:
  web_search:
    enabled: true
    max_results: 5
  
  reasoning_traces:
    enabled: true

# Core handles plugin loading
plugin_preference: native  # or "any" to allow subprocess
```

**Core loads appropriate plugins:**

```python
# Python core
config = load_config("config.yaml")

# Try native first
try:
    provider = load_native_plugin("openai", "provider")
except ImportError:
    # Fall back to subprocess if configured
    if config.plugin_preference == "any":
        provider = SubprocessPlugin(
            command=["node", "plugins/openai-provider.js"]
        )
    else:
        raise Exception("OpenAI provider not found in native plugins")
```

## Conclusion

**Recommended Architecture:**

1. **Primary: Native plugins** (same language as core)
   - Best performance
   - Natural idioms
   - Easy development

2. **Secondary: Subprocess plugins** (cross-language when needed)
   - Use JSON-RPC over stdin/stdout
   - Acceptable for I/O-heavy operations
   - Slower but flexible

3. **Not recommended: Network-based plugins**
   - Too much overhead for local use
   - Consider for enterprise/cloud only

**Key principle:** Make native the default, cross-language the exception. Most users will use native plugins. Cross-language support is for special cases where a plugin only exists in one language.

---

## 👤 You ##

Ok, I think we should 1. Create more specialized protocols, for example provider extension that must be written in the same language than the provider plugin itself, this may add streaming processing that may have to be performant. Other plugin types may only add to the final message processing (called only once per turn). 2. In chunk processing, in case the provider is in different language than the core, the provider should stream only partial message (e.g. single word or token at once) while keeping the accumulation of chunks and their processing internal (but it will yet be called by the app, but by a wrapper written in the same language than the plugin). This means in addition to accumulation at the protocol level (actually involving the wrapper), the process would stream partial message chunks that will then be processed by an other part of the application (e.g. streamed to the frontend via websocket as json messages and then joined there to show partial messages). At the end of streaming, partial messages will be discarded and replaced by final messages - this is the time when other plugins can make their processing and add things like citations.
Please rethink and list the protocols in question, and also mention differnt layers of the application and which layer calls what during a request processing. Write the protocols and process in a compact way, so that we can easily work from it and apply modifications until perfect.

---

## Assistant · *Claude 4 Sonnet* ##

# AI Agent Platform - Specialized Protocols & Layers

## Plugin Types & Language Requirements

```
1. PROVIDER PLUGIN (I/O + Processing)
   Language: Any (Python or JavaScript)
   Performance: Critical for streaming
   Cross-language: Use wrapper pattern
   
2. PROVIDER EXTENSION (Streaming Enhancement)
   Language: MUST match provider
   Performance: Critical (per-chunk processing)
   Cross-language: NOT supported
   
3. MESSAGE TRANSFORM PLUGIN (Pre/Post Processing)
   Language: Any
   Performance: Non-critical (once per request)
   Cross-language: Supported
   
4. FINAL MESSAGE PROCESSOR (Post-Completion)
   Language: Any
   Performance: Non-critical (once per turn)
   Cross-language: Supported
   
5. DISPLAY FORMATTER (UI Rendering)
   Language: Any
   Performance: Non-critical (once per display)
   Cross-language: Supported
```

## Application Layers

```
┌─────────────────────────────────────────┐
│  1. FRONTEND LAYER                      │
│  - Renders UI                           │
│  - Receives streamed tokens via WS      │
│  - Accumulates partial → replaced final │
└─────────────────────────────────────────┘
                  ↕ WebSocket/JSON
┌─────────────────────────────────────────┐
│  2. APPLICATION LAYER                   │
│  - Session management                   │
│  - WebSocket server                     │
│  - Calls Core API                       │
└─────────────────────────────────────────┘
                  ↕ Function calls
┌─────────────────────────────────────────┐
│  3. CORE LAYER                          │
│  - Plugin orchestration                 │
│  - Pipeline composition                 │
│  - State management                     │
└─────────────────────────────────────────┘
                  ↕ Plugin interface
┌──────────────────┬──────────────────────┐
│  4. PROVIDER     │  5. PLUGIN LAYER     │
│     LAYER        │                      │
│  ┌──────────┐    │  - Message Transform │
│  │ Provider │    │  - Final Processor   │
│  │          │    │  - Display Formatter │
│  │ ┌──────┐ │    │                      │
│  │ │ Ext  │ │    │                      │
│  │ └──────┘ │    │                      │
│  └──────────┘    │                      │
└──────────────────┴──────────────────────┘
```

## Request Processing Flow

### Non-Streaming Request

```
1. Frontend → Application: user_message
2. Application → Core: send_message(message)
3. Core → Message Transform Plugins: transform messages
4. Core → Provider: call_api(body, config, meta_state)
5. Provider → LLM API: HTTP request
6. Provider ← LLM API: complete response
7. Provider → Core: final_message + metadata
8. Core → Final Message Processors: process(message)
9. Core → Application: final_message (with citations, etc.)
10. Application → Frontend: display final message
```

### Streaming Request (Provider in Same Language as Core)

```
1. Frontend → Application: user_message
2. Application → Core: send_message_stream(message)
3. Core → Message Transform Plugins: transform messages
4. Core → Provider: stream_api(body, config, meta_state)

5. FOR EACH CHUNK FROM API:
   a. Provider receives native_chunk from API
   b. Provider → Provider Extension: process_chunk(chunk)
   c. Provider Extension: accumulates/processes
   d. Provider → Core: yield partial_message {content: "token"}
   e. Core → Application: yield partial_message
   f. Application → Frontend: WS send partial_message
   g. Frontend: append to display

6. ON COMPLETION:
   a. Provider → Provider Extension: finalize()
   b. Provider Extension → Provider: metadata (citations, etc.)
   c. Provider → Core: final_message (complete with metadata)
   d. Core → Final Message Processors: process(final_message)
   e. Core → Application: final_message (enhanced)
   f. Application → Frontend: replace_with_final(final_message)
   g. Frontend: discard partials, show final
```

### Streaming Request (Provider in Different Language - Subprocess)

```
1-3. [Same as above]

4. Core → Provider Wrapper (same language as Core)
5. Provider Wrapper → Provider Plugin (subprocess, different language)

6. PROVIDER PLUGIN (subprocess) INTERNAL:
   a. Makes API call
   b. FOR EACH native_chunk from API:
      - Calls provider extensions (same language)
      - Accumulates chunks internally
      - Extracts token/word
      - Sends partial_message to wrapper via JSON-RPC
   
7. PROVIDER WRAPPER (Core language):
   FOR EACH partial_message from subprocess:
   a. Receives {"type": "partial", "content": "token"}
   b. Core → Application: yield partial_message
   c. Application → Frontend: WS send
   d. Frontend: append to display

8. ON COMPLETION:
   a. Provider Plugin (subprocess) finalizes with extensions
   b. Sends {"type": "final", "message": {...}, "metadata": {...}}
   c. Provider Wrapper → Core: final_message
   d. Core → Final Message Processors: process(final_message)
   e. Core → Application: final_message (enhanced)
   f. Application → Frontend: replace_with_final
```

## Protocol Definitions

### 1. Provider Plugin Protocol

```yaml
ProviderPlugin:
  language: python | javascript
  category: provider
  
  pure_functions:
    init(model_id, config) → meta_state
    can_handle(capability_id, meta_state) → bool
    get_config_schema() → dict
    to_native_messages(messages, meta_state) → native_messages
    from_native_messages(native_messages, meta_state) → messages
    build_request_body(native_messages, config, meta_state) → body
    to_display_format(message, meta_state) → display_dict
  
  io_functions:
    detect_capabilities(model_id, config) → capabilities
    call_api(body, config, meta_state) → response
    stream_api(body, config, meta_state) → Iterator[partial_message | final_message]
      # Returns:
      # - partial_message: {type: "partial", content: str}
      # - final_message: {type: "final", message: Message, metadata: dict}
  
  extensions:
    register_extension(extension: ProviderExtension)
```

### 2. Provider Extension Protocol

```yaml
ProviderExtension:
  language: MUST match provider language
  category: provider_extension
  
  lifecycle:
    init(meta_state) → extension_state
    
  streaming:
    process_chunk(native_chunk, extension_state) → extension_state
      # Called per chunk by provider
      # Accumulates/processes streaming data
      # Returns updated state
    
    extract_partial(extension_state) → Optional[str]
      # Called by provider to get token/word for streaming
      # Returns None if no new partial available
    
    finalize(extension_state) → metadata
      # Called on completion
      # Returns metadata to add to final message
      # Example: citations, reasoning traces, etc.
```

### 3. Message Transform Plugin Protocol

```yaml
MessageTransformPlugin:
  language: python | javascript
  category: message_transform
  cross_language: supported
  
  functions:
    get_to_compatibility_transform(can_handle_fn, config, meta_state)
      → Optional[messages → messages]
    
    get_from_compatibility_transform(can_handle_fn, config, meta_state)
      → Optional[messages → messages]
    
    is_applicable(can_handle_fn, config) → bool
```

### 4. Final Message Processor Protocol

```yaml
FinalMessageProcessor:
  language: python | javascript
  category: final_processor
  cross_language: supported
  performance: non_critical (called once per turn)
  
  functions:
    is_applicable(can_handle_fn, config, meta_state) → bool
    
    process_message(message, conversation_state, meta_state)
      → message
      # Called after streaming completes
      # Can add citations, enhance content, etc.
      # Example: citation formatter, content filter, etc.
```

### 5. Display Formatter Protocol

```yaml
DisplayFormatter:
  language: python | javascript
  category: display_formatter
  cross_language: supported
  performance: non_critical (called once per display)
  
  functions:
    is_applicable(can_handle_fn, config, meta_state) → bool
    
    format_message(message, display_context, meta_state)
      → display_dict
      # Transforms message for UI rendering
      # Adds UI-specific formatting, metadata
```

## Streaming Message Protocol (Subprocess)

### Provider → Wrapper (JSON-RPC over stdio)

```json
// PARTIAL MESSAGE (streamed continuously)
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "type": "partial",
    "content": "Hello",
    "metadata": {
      "token_count": 1,
      "extension_data": {}
    }
  }
}

// FINAL MESSAGE (sent once at completion)
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "type": "final",
    "message": {
      "role": "assistant",
      "content": "Hello, how can I help you?",
      "metadata": {
        "citations": [...],
        "reasoning_traces": {...},
        "token_count": 8
      }
    },
    "done": true
  }
}
```

### Application → Frontend (WebSocket)

```json
// PARTIAL MESSAGE (streamed)
{
  "type": "stream.partial",
  "request_id": "req-123",
  "content": "Hello",
  "cumulative_content": "Hello"
}

// FINAL MESSAGE (replaces partials)
{
  "type": "stream.final",
  "request_id": "req-123",
  "message": {
    "role": "assistant",
    "content": "Hello, how can I help you?",
    "citations": [...],
    "metadata": {...}
  }
}
```

## Example: Provider with Extension (Same Language)

```python
# Provider Plugin
class OpenAIProvider:
    def __init__(self):
        self.extensions = []
    
    def register_extension(self, extension):
        self.extensions.append(extension)
    
    async def stream_api(self, body, config, meta_state):
        """Streams partial messages, then final"""
        # Initialize extensions
        ext_states = [ext.init(meta_state) for ext in self.extensions]
        
        # Make API call
        async for native_chunk in self._call_openai_streaming(body, config):
            # Process with extensions
            for i, ext in enumerate(self.extensions):
                ext_states[i] = ext.process_chunk(native_chunk, ext_states[i])
            
            # Extract partial for streaming (token/word)
            for ext_state in ext_states:
                partial = ext.extract_partial(ext_state)
                if partial:
                    yield {
                        "type": "partial",
                        "content": partial
                    }
        
        # Finalize - get metadata from extensions
        final_metadata = {}
        for i, ext in enumerate(self.extensions):
            ext_metadata = ext.finalize(ext_states[i])
            final_metadata.update(ext_metadata)
        
        # Build final message from accumulated state
        final_message = self._build_final_message(ext_states, final_metadata)
        
        yield {
            "type": "final",
            "message": final_message,
            "done": True
        }
```

```python
# Provider Extension (same language)
class CitationExtension:
    """Extracts citations during streaming"""
    
    def init(self, meta_state):
        return {
            "accumulated_content": "",
            "citations": [],
            "partial_buffer": ""
        }
    
    def process_chunk(self, native_chunk, state):
        """Process each chunk"""
        delta = native_chunk.get("choices", [{}])[0].get("delta", {})
        
        # Accumulate content
        if "content" in delta:
            state["accumulated_content"] += delta["content"]
            state["partial_buffer"] += delta["content"]
        
        # Extract citations from chunk metadata
        if "citations" in native_chunk:
            state["citations"].extend(native_chunk["citations"])
        
        return state
    
    def extract_partial(self, state):
        """Extract token/word for streaming"""
        # Return accumulated buffer and clear
        if state["partial_buffer"]:
            partial = state["partial_buffer"]
            state["partial_buffer"] = ""
            return partial
        return None
    
    def finalize(self, state):
        """Return metadata for final message"""
        return {
            "citations": state["citations"],
            "content_length": len(state["accumulated_content"])
        }
```

## Example: Final Message Processor (Cross-Language OK)

```python
# Citation Formatter Plugin
class CitationFormatterProcessor:
    category = "final_processor"
    language = "python"
    
    def is_applicable(self, can_handle_fn, config, meta_state):
        return config.get("format_citations", False)
    
    def process_message(self, message, conversation_state, meta_state):
        """Process message after streaming completes"""
        if "citations" not in message.metadata:
            return message
        
        # Format citations
        citations = message.metadata["citations"]
        formatted_content = message.content
        
        # Add citation markers
        for i, citation in enumerate(citations, 1):
            formatted_content += f"\n[{i}] {citation['url']}"
        
        # Return enhanced message
        return Message(
            role=message.role,
            content=formatted_content,
            metadata={
                **message.metadata,
                "formatted_citations": True
            }
        )
```

## Core Orchestration (Compact)

```python
class Core:
    def __init__(self):
        self.providers = {}
        self.message_transforms = []
        self.final_processors = []
        self.display_formatters = []
    
    async def send_message_stream(self, user_message, config):
        """Stream message processing"""
        # 1. Transform messages
        messages = self._apply_transforms(user_message, config)
        
        # 2. Provider streams (partials + final)
        provider = self.providers[config["provider"]]
        body = provider.build_request_body(messages, config, meta_state)
        
        async for item in provider.stream_api(body, config, meta_state):
            if item["type"] == "partial":
                # Stream partial immediately
                yield {"type": "partial", "content": item["content"]}
            
            elif item["type"] == "final":
                # 3. Process final message
                final_message = item["message"]
                
                for processor in self.final_processors:
                    if processor.is_applicable(can_handle_fn, config, meta_state):
                        final_message = processor.process_message(
                            final_message, 
                            conversation_state,
                            meta_state
                        )
                
                # 4. Format for display
                display = provider.to_display_format(final_message, meta_state)
                for formatter in self.display_formatters:
                    if formatter.is_applicable(can_handle_fn, config, meta_state):
                        display = formatter.format_message(
                            final_message,
                            display_context,
                            meta_state
                        )
                
                yield {
                    "type": "final",
                    "message": final_message,
                    "display": display
                }
```

## Summary: Who Calls What

```
STREAMING FLOW:

Frontend
  ↓ user input
Application Layer: send_message_stream()
  ↓ call
Core Layer: orchestrate_stream()
  ↓ transform
Message Transform Plugins: to_compat → trim → from_compat
  ↓ build request
Provider: build_request_body()
  ↓ stream
Provider: stream_api()
  ├→ FOR EACH CHUNK:
  │   ├→ Provider Extensions (same language): process_chunk()
  │   ├→ Provider Extensions: extract_partial()
  │   └→ yield partial_message
  └→ ON COMPLETE:
      ├→ Provider Extensions: finalize()
      ├→ yield final_message
      └→ [done]
Core Layer: receives stream
  ├→ FOR EACH partial: yield to Application
  └→ FOR final:
      ├→ Final Message Processors: process_message()
      ├→ Display Formatters: format_message()
      └→ yield to Application
Application Layer: receives stream
  ├→ FOR EACH partial: WebSocket send
  └→ FOR final: WebSocket send (replaces partials)
Frontend
  ├→ partial: append to display
  └→ final: replace with formatted message
```

## Performance Characteristics

```
HOT PATH (per-chunk, must be fast):
- Provider.stream_api()
- Provider Extensions.process_chunk()
- Provider Extensions.extract_partial()
→ MUST be same language as provider

COLD PATH (once per turn, can be slower):
- Message Transform Plugins
- Final Message Processors
- Display Formatters
→ CAN be cross-language (subprocess acceptable)
```

## Cross-Language Strategy

```
NATIVE: Provider (Python) + Extensions (Python)
  → Direct calls, maximum performance

SUBPROCESS: Provider (Python subprocess) + Extensions (Python)
  → Wrapped by Core (JavaScript)
  → Provider handles streaming internally
  → Streams partials via JSON-RPC
  → Returns final with metadata from extensions
```

This architecture separates performance-critical streaming (keep in same language) from final processing (can be cross-language), while maintaining clean protocols at each layer.

---

## 👤 You ##

Few things to correct:
Model id is part of the config
Instead of meta state, extension state, capabilities and such different objects, each plugin should have a single state object that can be updated upon init and after soecific actions (e.g. UI interaction like switching boolean UI element - e.g. Enable web search). Only init will receive the config, and from then, the state object is provided (config should be added to the state object to access).
Let's have provider extension, feature plugin and tool support, each should have config, state, UI elements for frontend config. The difference is the availability of chunk processing functions.
The plugins should have two extra layers, a plugin wrapper in the same language than the plugin, that should directly call the methods, and keep the plugin's state, and the plugin adapter should provide a communication protocol between the application and the plugin. For plugins in the same language, the adapter will be passthrough adapter.
Please provide the modification of the architecture. Keep it compact.

---

## Assistant · *Claude 4 Sonnet* ##

# AI Agent Platform - Revised Architecture

## Plugin Types

```
1. PROVIDER PLUGIN (Base I/O)
   - API communication, message conversion
   - Has: config, state, chunk_processing
   - Language: Any
   
2. PROVIDER EXTENSION (Streaming Enhancement)
   - Extends provider's chunk processing
   - Has: config, state, chunk_processing, UI elements
   - Language: MUST match provider
   
3. FEATURE PLUGIN (Message/Request Transform)
   - Transforms messages, modifies requests
   - Has: config, state, UI elements, NO chunk_processing
   - Language: Any
   
4. TOOL PLUGIN (Tool Definition & Execution)
   - Defines tools, executes them
   - Has: config, state, UI elements, NO chunk_processing
   - Language: Any
```

## Two-Layer Plugin Architecture

```
┌─────────────────────────────────────────┐
│  CORE (Python or JavaScript)            │
└─────────────┬───────────────────────────┘
              │
┌─────────────┴───────────────────────────┐
│  PLUGIN ADAPTER (Core Language)         │
│  - Protocol translation                 │
│  - Passthrough (same language)          │
│  - Subprocess bridge (different)        │
└─────────────┬───────────────────────────┘
              │
┌─────────────┴───────────────────────────┐
│  PLUGIN WRAPPER (Plugin Language)       │
│  - Holds plugin state                   │
│  - Direct method calls to plugin        │
│  - State management                     │
└─────────────┬───────────────────────────┘
              │
┌─────────────┴───────────────────────────┐
│  PLUGIN (Plugin Language)               │  
│  - Pure logic, stateless methods        │
│  - Receives state, returns new state    │
└─────────────────────────────────────────┘
```

## Plugin State Object

```yaml
PluginState:
  config:            # Original config + any updates
    model: str
    api_key: str
    enabled: bool
    max_results: int
    ... (plugin-specific)
  
  capabilities: list[str]  # Detected/declared capabilities
  
  runtime_state:     # Plugin's working state
    ... (any plugin-specific data)
  
  ui_state:          # Current UI settings
    ... (reflects UI element values)
```

## Plugin Protocols

### Base Plugin Interface

```yaml
BasePlugin:
  # Schema & UI
  get_config_schema() → dict
  get_ui_elements() → list[UIElement]
  
  # Lifecycle
  init(config) → state
    # Called once, returns initial state with config embedded
  
  update_state(state, updates) → state
    # Called when UI changes or config updates
  
  # Capability
  can_handle(capability_id, state) → bool
```

### 1. Provider Plugin

```yaml
ProviderPlugin extends BasePlugin:
  # Pure functions
  to_native_messages(messages, state) → native_messages
  from_native_messages(native_messages, state) → messages
  build_request_body(messages, state) → body
  
  process_chunk(native_chunk, state) → (partial_content, new_state)
    # Returns: (text_to_stream, updated_state)
  
  finalize(state) → (final_message, metadata)
    # Called after streaming completes
  
  to_display_format(message, state) → display_dict
  
  # I/O functions
  detect_capabilities(config) → capabilities
  call_api(body, state) → response
  stream_api(body, state) → Iterator[native_chunk]
```

### 2. Provider Extension Plugin

```yaml
ProviderExtensionPlugin extends BasePlugin:
  # Must declare target provider
  target_provider: str
  
  # Chunk processing (hot path)
  process_chunk(native_chunk, provider_state, extension_state) 
    → (partial_content, new_extension_state)
    # Called per chunk by provider wrapper
    # Returns: (text_to_stream, updated_state)
  
  enhance_final_message(message, metadata, state) 
    → (enhanced_message, enhanced_metadata)
    # Called before final message sent
```

### 3. Feature Plugin

```yaml
FeaturePlugin extends BasePlugin:
  # Request/Message transforms
  modify_request_body(body, state) → body
  
  transform_messages(messages, state, direction: "to_compat" | "from_compat")
    → messages
  
  process_final_message(message, conversation_state, state)
    → message
    # Called after streaming completes
  
  format_display(display, message, state) → display
```

### 4. Tool Plugin

```yaml
ToolPlugin extends BasePlugin:
  # Tool definition
  get_tool_schemas(state) → list[ToolSchema]
  
  # Execution
  execute_tool(tool_name, arguments, state) → result
    # Can make external API calls
  
  format_tool_result(result, state) → formatted_result
```

## Plugin Wrapper (Holds State)

```python
# Python example
class PluginWrapper:
    """Wrapper in same language as plugin, manages state"""
    
    def __init__(self, plugin_instance, config):
        self.plugin = plugin_instance
        self.state = plugin_instance.init(config)
    
    def update_state(self, updates):
        """Update state (e.g., UI change)"""
        self.state = self.plugin.update_state(self.state, updates)
    
    def get_state(self):
        """Access current state"""
        return self.state
    
    # Delegate all methods, passing state
    
    def can_handle(self, capability_id):
        return self.plugin.can_handle(capability_id, self.state)
    
    def process_chunk(self, native_chunk):
        partial, new_state = self.plugin.process_chunk(native_chunk, self.state)
        self.state = new_state
        return partial
    
    def finalize(self):
        message, metadata = self.plugin.finalize(self.state)
        return message, metadata
    
    # ... other methods
```

## Plugin Adapter (Protocol Bridge)

### Passthrough Adapter (Same Language)

```python
class PassthroughAdapter:
    """For plugins in same language as core"""
    
    def __init__(self, plugin_wrapper):
        self.wrapper = plugin_wrapper
    
    # Direct delegation
    def can_handle(self, capability_id):
        return self.wrapper.can_handle(capability_id)
    
    def process_chunk(self, native_chunk):
        return self.wrapper.process_chunk(native_chunk)
    
    async def stream_api(self, body):
        async for chunk in self.wrapper.stream_api(body):
            yield chunk
```

### Subprocess Adapter (Different Language)

```python
class SubprocessAdapter:
    """For plugins in different language than core"""
    
    def __init__(self, command):
        self.command = command
        self.process = self._start_subprocess()
    
    def _start_subprocess(self):
        """Starts subprocess with plugin wrapper"""
        # Subprocess runs plugin wrapper which manages state
        return subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True
        )
    
    def can_handle(self, capability_id):
        """RPC call to subprocess"""
        return self._call("can_handle", {"capability_id": capability_id})
    
    def process_chunk(self, native_chunk):
        """RPC call to subprocess"""
        return self._call("process_chunk", {"native_chunk": native_chunk})
    
    def update_state(self, updates):
        """Update plugin state via RPC"""
        return self._call("update_state", {"updates": updates})
    
    async def stream_api(self, body):
        """Streaming RPC"""
        # Subprocess wrapper handles state internally
        async for response in self._stream_call("stream_api", {"body": body}):
            if response["type"] == "partial":
                yield response["content"]
            elif response["type"] == "final":
                yield response
```

## Revised Request Flow

### Streaming Flow

```
1. Frontend: user message + UI state
   ↓
2. Application: send_message_stream(message, ui_updates)
   ↓
3. Core: Update plugin states from UI
   FOR EACH plugin adapter:
     adapter.update_state(ui_updates[plugin.name])
   ↓
4. Core: Transform messages
   FOR EACH feature plugin adapter:
     IF adapter.can_handle("message_transform"):
       messages = adapter.transform_messages(messages, "to_compat")
   ↓
5. Core: Build request
   provider_adapter.build_request_body(messages)
   FOR EACH feature plugin adapter:
     body = adapter.modify_request_body(body)
   ↓
6. Core: Stream from provider
   FOR EACH chunk FROM provider_adapter.stream_api(body):
     ├→ Provider Adapter → Provider Wrapper
     │    └→ Provider Wrapper: process_chunk() [updates state]
     │         ├→ Call provider extensions
     │         └→ Return partial
     ├→ IF partial: yield to Application
     │    └→ Application → Frontend: stream partial
     └→ IF final:
         ├→ Provider Adapter: finalize() [with extensions]
         ├→ Core: Process with feature plugins
         │    FOR EACH feature adapter:
         │      message = adapter.process_final_message(message)
         ├→ Core: Format display
         │    display = provider_adapter.to_display_format(message)
         │    FOR EACH feature adapter:
         │      display = adapter.format_display(display, message)
         └→ yield final to Application
              └→ Application → Frontend: replace partials
```

## Example: Provider with Extension (Same Language)

```python
# Provider Plugin (stateless methods)
class OpenAIProvider:
    def get_config_schema(self):
        return {
            "model": {"type": "string", "required": True},
            "api_key": {"type": "string", "required": True}
        }
    
    def init(self, config):
        """Initialize state with config"""
        capabilities = self._detect_capabilities(config)
        return {
            "config": config,
            "capabilities": capabilities,
            "runtime_state": {
                "request_count": 0
            }
        }
    
    def process_chunk(self, native_chunk, state):
        """Process chunk, return partial and new state"""
        delta = native_chunk.get("choices", [{}])[0].get("delta", {})
        partial = delta.get("content", "")
        
        # Update state
        new_state = {
            **state,
            "runtime_state": {
                **state["runtime_state"],
                "last_chunk": native_chunk
            }
        }
        
        return partial, new_state
    
    async def stream_api(self, body, state):
        """I/O function - streams from API"""
        async for chunk in self._call_openai(body, state["config"]):
            yield chunk


# Provider Extension Plugin
class CitationExtension:
    target_provider = "openai"
    
    def get_config_schema(self):
        return {
            "extract_citations": {"type": "boolean", "default": True}
        }
    
    def get_ui_elements(self):
        return [
            {
                "type": "checkbox",
                "key": "extract_citations",
                "label": "Extract Citations"
            }
        ]
    
    def init(self, config):
        return {
            "config": config,
            "runtime_state": {
                "citations": [],
                "content_buffer": ""
            }
        }
    
    def process_chunk(self, native_chunk, provider_state, extension_state):
        """Process each chunk"""
        if not extension_state["config"]["extract_citations"]:
            return "", extension_state
        
        # Extract citations from chunk
        citations = native_chunk.get("citations", [])
        
        new_state = {
            **extension_state,
            "runtime_state": {
                **extension_state["runtime_state"],
                "citations": extension_state["runtime_state"]["citations"] + citations
            }
        }
        
        return "", new_state  # No partial content from extension
    
    def enhance_final_message(self, message, metadata, state):
        """Add citations to final message"""
        enhanced_metadata = {
            **metadata,
            "citations": state["runtime_state"]["citations"]
        }
        return message, enhanced_metadata


# Provider Wrapper (holds state)
class ProviderWrapperWithExtensions:
    def __init__(self, provider, extensions, config):
        self.provider = provider
        self.extensions = extensions
        
        # Initialize states
        self.provider_state = provider.init(config)
        self.extension_states = {
            ext: ext.init(config) for ext in extensions
        }
    
    def update_state(self, updates):
        """Update from UI changes"""
        # Update provider state
        self.provider_state = self.provider.update_state(
            self.provider_state, 
            updates
        )
        
        # Update extension states
        for ext in self.extensions:
            self.extension_states[ext] = ext.update_state(
                self.extension_states[ext],
                updates
            )
    
    async def stream_with_extensions(self, body):
        """Stream with extension processing"""
        async for native_chunk in self.provider.stream_api(body, self.provider_state):
            # Provider processes chunk
            partial, new_provider_state = self.provider.process_chunk(
                native_chunk,
                self.provider_state
            )
            self.provider_state = new_provider_state
            
            # Extensions process chunk
            for ext in self.extensions:
                ext_partial, new_ext_state = ext.process_chunk(
                    native_chunk,
                    self.provider_state,
                    self.extension_states[ext]
                )
                self.extension_states[ext] = new_ext_state
                partial += ext_partial
            
            # Yield partial
            if partial:
                yield {"type": "partial", "content": partial}
        
        # Finalize
        message, metadata = self.provider.finalize(self.provider_state)
        
        # Extensions enhance final message
        for ext in self.extensions:
            message, metadata = ext.enhance_final_message(
                message,
                metadata,
                self.extension_states[ext]
            )
        
        yield {"type": "final", "message": message, "metadata": metadata}
```

## Example: Feature Plugin (Cross-Language OK)

```python
class WebSearchFeature:
    def get_config_schema(self):
        return {
            "web_search_enabled": {"type": "boolean", "default": False},
            "max_results": {"type": "integer", "default": 5}
        }
    
    def get_ui_elements(self):
        return [
            {
                "type": "checkbox",
                "key": "web_search_enabled",
                "label": "Enable Web Search"
            },
            {
                "type": "number",
                "key": "max_results",
                "label": "Max Results",
                "condition": {"web_search_enabled": True}
            }
        ]
    
    def init(self, config):
        return {
            "config": config,
            "capabilities": [],  # Will be checked against provider
            "ui_state": {
                "web_search_enabled": config.get("web_search_enabled", False)
            }
        }
    
    def update_state(self, state, updates):
        """Update when UI changes"""
        new_config = {**state["config"], **updates}
        return {
            **state,
            "config": new_config,
            "ui_state": {**state["ui_state"], **updates}
        }
    
    def can_handle(self, capability_id, state):
        """Check if applicable"""
        return (
            state["ui_state"]["web_search_enabled"] and
            capability_id == "web_search"
        )
    
    def modify_request_body(self, body, state):
        """Add search parameters"""
        if not state["ui_state"]["web_search_enabled"]:
            return body
        
        return {
            **body,
            "search": {
                "enabled": True,
                "max_results": state["config"]["max_results"]
            }
        }
    
    def process_final_message(self, message, conversation_state, state):
        """Process after streaming completes"""
        if "citations" in message.metadata:
            # Format citations
            formatted = self._format_citations(
                message,
                state["config"]["max_results"]
            )
            return formatted
        return message
```

## State Update Flow (UI Interaction)

```
1. Frontend: User toggles "Enable Web Search"
   ↓
2. Frontend → Application: update_config({web_search_enabled: true})
   ↓
3. Application → Core: update_plugin_states(updates)
   ↓
4. Core: FOR EACH plugin adapter:
   adapter.update_state(updates)
   ↓
5. Adapter → Wrapper: update_state(updates)
   ↓
6. Wrapper: Updates plugin state
   new_state = plugin.update_state(current_state, updates)
   ↓
7. Next request uses updated state
```

## Core Plugin Management (Compact)

```python
class Core:
    def __init__(self):
        self.provider_adapter = None
        self.feature_adapters = []
        self.tool_adapters = []
    
    def register_provider(self, plugin, config):
        """Register provider with extensions"""
        # Create wrapper
        wrapper = ProviderWrapperWithExtensions(
            plugin.provider,
            plugin.extensions,
            config
        )
        
        # Create adapter (passthrough or subprocess)
        if is_same_language(plugin, self):
            self.provider_adapter = PassthroughAdapter(wrapper)
        else:
            self.provider_adapter = SubprocessAdapter(wrapper.command)
    
    def register_feature(self, plugin, config):
        """Register feature plugin"""
        wrapper = PluginWrapper(plugin, config)
        
        if is_same_language(plugin, self):
            adapter = PassthroughAdapter(wrapper)
        else:
            adapter = SubprocessAdapter(wrapper.command)
        
        self.feature_adapters.append(adapter)
    
    def update_plugin_states(self, updates):
        """Update all plugin states from UI"""
        self.provider_adapter.update_state(updates)
        for adapter in self.feature_adapters:
            adapter.update_state(updates)
        for adapter in self.tool_adapters:
            adapter.update_state(updates)
    
    async def send_message_stream(self, message, ui_updates=None):
        """Stream message with current plugin states"""
        # Update states if UI changed
        if ui_updates:
            self.update_plugin_states(ui_updates)
        
        # Transform messages
        messages = self._transform_messages([message])
        
        # Build request
        body = self.provider_adapter.build_request_body(messages)
        for adapter in self.feature_adapters:
            body = adapter.modify_request_body(body)
        
        # Stream
        async for item in self.provider_adapter.stream_api(body):
            if item["type"] == "partial":
                yield item
            elif item["type"] == "final":
                # Process final
                message = item["message"]
                for adapter in self.feature_adapters:
                    message = adapter.process_final_message(message)
                
                yield {"type": "final", "message": message}
```

## Summary

**Key Changes:**
1. **Single state object** per plugin (includes config, capabilities, runtime state)
2. **Model in config** (not separate parameter)
3. **Two-layer architecture**: Wrapper (holds state) + Adapter (protocol)
4. **Three plugin types**: Provider Extension, Feature, Tool
5. **State updates** from UI interactions
6. **Passthrough adapter** for same-language (zero overhead)
7. **Subprocess adapter** for cross-language (state managed in subprocess)

**Performance:**
- Same language: Direct calls through passthrough adapter
- Different language: State kept in subprocess, minimal RPC calls


# 135 — Background Process Management (Application Layer)

Short description: Implement application-level background process management including shell registry, streaming output, UI toggle commands, and process lifecycle control.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On: `tasks/20260315-gemini-qwen-grok-tool-packages/100-shell-tools.md` (Tier 1 background support)

## Status

POSTPONED - Tier 1 background support (schema param, early return with PID) implemented in task 100. This task covers Tier 2 application-layer features.

## Requirements checklist

- [ ] Background shell registry in application layer
- [ ] Streaming output subscription after tool returns
- [ ] UI toggle commands (Ctrl+B, /shells)
- [ ] Process lifecycle management (kill/restart)
- [ ] Terminal app integration
- [ ] HTTP API endpoints for background shell management

## Goal

Add full background process management capabilities at the application layer, enabling users to:
1. View output from background processes after they've started
2. Toggle visibility of background shell panel
3. Kill or restart background processes
4. See status of all running background processes

This is the Tier 2 implementation postponed from task 100.

## Background

Task 100 implemented Tier 1 background support at the plugin level:
- `is_background` schema parameter
- Early return with PID
- Initial output capture
- No timeout for background processes

This task adds the rich UX features that require application-layer support.

## Key source references

### Gemini CLI (reference implementation)

- Background shell registry:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/cli/src/ui/hooks/shellCommandProcessor.ts` (`registerBackgroundShell`, `dismissBackgroundShell`)
- Shell reducer (state management):
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/cli/src/ui/hooks/shellReducer.ts`
- UI toggle:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/cli/src/ui/commands/shellsCommand.ts`
- Background shell manager:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/cli/src/ui/hooks/useBackgroundShellManager.ts`

### Key patterns from Gemini CLI

**State shape:**
```typescript
interface ShellState {
  activeShellPtyId: number | null;
  backgroundShells: Map<number, BackgroundShell>;
  isBackgroundShellVisible: boolean;
  lastShellOutputTime: number | null;
}

interface BackgroundShell {
  pid: number;
  command: string;
  output: string;
  isBinary: boolean;
  binaryBytesReceived: number;
  status: 'running' | 'exited';
}
```

**Actions:**
- `REGISTER_SHELL` - Add new background shell to registry
- `DISMISS_SHELL` - Remove from registry
- `UPDATE_SHELL_OUTPUT` - Append new output
- `TOGGLE_VISIBILITY` - Show/hide background panel
- `SET_ACTIVE_PTY` - Focus specific shell

**UI integration:**
- `Ctrl+B` toggles background shell panel visibility
- `/shells` command shows background shells list
- Output streams to registered shell entries

## Proposed implementation

### 1. Application-layer state

**File:** `core/python/agent_app/background_shells.py`

```python
from dataclasses import dataclass, field
from typing import Dict, Optional, Callable
from enum import Enum

class ShellStatus(Enum):
    RUNNING = "running"
    EXITED = "exited"

@dataclass
class BackgroundShell:
    pid: int
    command: str
    output: str = ""
    status: ShellStatus = ShellStatus.RUNNING
    is_binary: bool = False
    binary_bytes_received: int = 0

class BackgroundShellRegistry:
    def __init__(self):
        self._shells: Dict[int, BackgroundShell] = {}
        self._listeners: list[Callable[[int, BackgroundShell], None]] = []
    
    def register(self, pid: int, command: str, initial_output: str = "") -> BackgroundShell:
        shell = BackgroundShell(pid=pid, command=command, output=initial_output)
        self._shells[pid] = shell
        self._notify_listeners(pid, shell)
        return shell
    
    def dismiss(self, pid: int) -> bool:
        if pid in self._shells:
            del self._shells[pid]
            return True
        return False
    
    def append_output(self, pid: int, output: str) -> None:
        if pid in self._shells:
            self._shells[pid].output += output
            self._notify_listeners(pid, self._shells[pid])
    
    def mark_exited(self, pid: int, exit_code: int) -> None:
        if pid in self._shells:
            self._shells[pid].status = ShellStatus.EXITED
            self._shells[pid].exit_code = exit_code
            self._notify_listeners(pid, self._shells[pid])
    
    def get_all(self) -> Dict[int, BackgroundShell]:
        return self._shells.copy()
    
    def subscribe(self, listener: Callable[[int, BackgroundShell], None]) -> None:
        self._listeners.append(listener)
    
    def _notify_listeners(self, pid: int, shell: BackgroundShell) -> None:
        for listener in self._listeners:
            listener(pid, shell)
```

### 2. Tool-to-registry integration

**Modify shell engine to support streaming to registry:**

```python
# In shell_engine.py

def run_shell_command(
    command: str,
    *,
    is_background: bool = False,
    output_callback: Optional[Callable[[str], None]] = None,
    # ... other params
) -> dict:
    
    if is_background:
        # Capture initial output
        initial_output = capture_available_output(process)
        
        # Start background streaming thread if callback provided
        if output_callback:
            start_background_streamer(process, output_callback)
        
        return {
            "background": True,
            "pid": process.pid,
            "output": initial_output,
            # ...
        }
```

### 3. Terminal app integration

**File:** `application/python/agent_terminal_app/background_ui.py`

```python
from typing import Optional
from agent_app.background_shells import BackgroundShellRegistry

class BackgroundShellUI:
    def __init__(self, registry: BackgroundShellRegistry):
        self.registry = registry
        self._visible = False
        self._active_pid: Optional[int] = None
        
        # Subscribe to registry updates
        self.registry.subscribe(self._on_shell_update)
    
    def toggle_visibility(self) -> None:
        self._visible = not self._visible
        # Trigger UI refresh
    
    def show(self) -> None:
        self._visible = True
    
    def hide(self) -> None:
        self._visible = False
    
    def set_active(self, pid: Optional[int]) -> None:
        self._active_pid = pid
    
    def kill_shell(self, pid: int) -> bool:
        # Send SIGTERM to process
        import signal
        import os
        try:
            os.kill(pid, signal.SIGTERM)
            return True
        except ProcessLookupError:
            return False
    
    def _on_shell_update(self, pid: int, shell: BackgroundShell) -> None:
        if self._visible:
            # Trigger UI refresh to show new output
            pass
```

### 4. Terminal commands

**Add commands to terminal.py:**

```python
# /shells command - list background shells
# /kill <pid> command - kill a background shell
# /bg or Ctrl+B - toggle background panel
```

### 5. HTTP API endpoints

**File:** `application/python/agent_terminal_app/server.py` additions:

```python
@app.get("/api/background-shells")
async def list_background_shells():
    """List all background shells."""
    pass

@app.get("/api/background-shells/{pid}")
async def get_background_shell(pid: int):
    """Get output and status of a specific background shell."""
    pass

@app.delete("/api/background-shells/{pid}")
async def kill_background_shell(pid: int):
    """Kill a background shell."""
    pass

@app.post("/api/background-shells/toggle")
async def toggle_background_visibility():
    """Toggle visibility of background shell panel."""
    pass
```

### 6. Mobile app integration

The mobile app (`mobile/crystal-lattice-control-rn`) would need:
- New screen/tab for background shells
- WebSocket subscription for output streaming
- Kill/restart controls

## Test plan

### Registry tests

1. Register shell → appears in registry
2. Dismiss shell → removed from registry
3. Append output → output accumulates
4. Mark exited → status changes

### UI tests

1. Toggle visibility → panel shows/hides
2. Kill shell → process terminated
3. Output updates → UI refreshes

### Integration tests

1. Start background shell via tool → registered correctly
2. Output streams → appears in registry
3. Kill via UI → process terminated

## Deliverables

1. `core/python/agent_app/background_shells.py` - registry implementation
2. `application/python/agent_terminal_app/background_ui.py` - UI integration
3. Terminal commands (`/shells`, `/kill`, `/bg`)
4. HTTP API endpoints
5. Tests for all components

## Open questions

1. **Process lifecycle:** Should we auto-cleanup exited processes? After how long?
2. **Output limits:** Should we limit stored output per shell? Truncate old output?
3. **Mobile support:** Full feature parity or simplified view-only?
4. **Persistence:** Should background shells survive app restart?

## Completion notes

(To be filled during implementation)
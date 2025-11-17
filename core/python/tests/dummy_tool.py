"""
Dummy tool plugin for testing purposes.

This plugin provides a simple calculator tool.
Follows the state-based plugin protocol.
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class DummyCalculator:
    """
    Dummy calculator tool plugin (stateless with state parameter).
    All methods are static and take state as parameter.
    """
    
    name: str = "dummy_calculator"
    version: str = "1.0.0"
    
    @staticmethod
    def get_config_schema() -> Dict[str, Any]:
        """Return configuration schema."""
        return {}
    
    @staticmethod
    def get_ui_elements() -> List[Dict[str, Any]]:
        """Return UI elements."""
        return []
    
    @staticmethod
    def init(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize tool state.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Initial state dictionary
        """
        return {
            "config": config,
            "capabilities": [],
            "runtime_state": {},
            "ui_state": {}
        }
    
    @staticmethod
    def update_state(state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update tool state (pure function).
        
        Args:
            state: Current state
            updates: Dictionary of updates
            
        Returns:
            New state
        """
        return {
            **state,
            "config": {**state["config"], **updates}
        }
    
    @staticmethod
    def get_tool_schemas(state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return tool schemas."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "add",
                    "description": "Add two numbers",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number", "description": "First number"},
                            "b": {"type": "number", "description": "Second number"}
                        },
                        "required": ["a", "b"]
                    }
                }
            }
        ]
    
    @staticmethod
    def execute_tool(
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tool."""
        if tool_name == "add":
            a = arguments.get("a", 0)
            b = arguments.get("b", 0)
            return {
                "success": True,
                "result": a + b
            }
        
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}"
        }
    
    @staticmethod
    def format_tool_result(result: Dict[str, Any], state: Dict[str, Any]) -> str:
        """Format tool result."""
        if result["success"]:
            return f"Result: {result['result']}"
        else:
            return f"Error: {result['error']}"

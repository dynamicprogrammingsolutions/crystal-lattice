"""Utility functions for agent_core."""

import os
import sys
import json
from typing import Any, Callable, List, Tuple, Dict
from functools import reduce
import structlog
from structlog.types import EventDict, WrappedLogger


def pipeline(*fixed_params: Any) -> Callable:
    """Create a pipeline that applies transformations with fixed parameters.

    This helper enables functional-style pipe transformations where multiple
    plugins sequentially transform data. Fixed parameters are passed to all
    transforms, while transformed values flow through the pipeline.

    Args:
        *fixed_params: Parameters passed to all transforms but not modified.

    Returns:
        Function that takes (transforms, *initial_values) and returns transformed values.

    Example:
        pipe = pipeline(config, extra_context)
        result = pipe([plugin.transform for plugin in plugins], initial_value)

        pipe = pipeline()
        val1, val2 = pipe([fn1, fn2, fn3], init1, init2)
    """

    def apply_transforms(transforms: List[Callable], *initial_transformed: Any) -> Any:
        num_values = len(initial_transformed)
        if num_values == 0:
            raise ValueError("Pipeline requires at least one initial value")

        if not transforms:
            if num_values == 1:
                return initial_transformed[0]
            return initial_transformed

        def reducer(transformed: Tuple[Any, ...], transform: Callable) -> Tuple[Any, ...]:
            result = transform(*fixed_params, *transformed)
            return result if isinstance(result, tuple) else (result,)

        initial: Tuple[Any, ...] = (
            initial_transformed if num_values > 1 else (initial_transformed[0],)
        )
        result: Tuple[Any, ...] = reduce(reducer, transforms, initial)

        return result[0] if len(result) == 1 else result

    return apply_transforms


def format_log_data(data: Any, max_length: int = 500) -> str:
    """Format data for logging with truncation.
    
    Args:
        data: Data to format (dict, list, str, etc.)
        max_length: Maximum string length before truncation
        
    Returns:
        Formatted string representation of the data
    """
    if data is None:
        return "None"
    
    try:
        # Try to pretty-print as JSON
        formatted = json.dumps(data, indent=2, ensure_ascii=False)
        if len(formatted) > max_length:
            # Truncate and add ellipsis
            return formatted[:max_length] + "... (truncated)"
        return formatted
    except (TypeError, ValueError):
        # Fallback to repr for non-JSON-serializable objects
        formatted = repr(data)
        if len(formatted) > max_length:
            return formatted[:max_length] + "... (truncated)"
        return formatted


def get_nested_value(data: Dict[str, Any], path: str) -> Any:
    """Get nested value from dict using dot notation.
    
    Args:
        data: Dictionary to search
        path: Dot-separated path (e.g., "chunk.reasoning")
        
    Returns:
        Value at path or None if not found
    """
    parts = path.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
            if current is None:
                return None
        else:
            return None
    return current


def parse_filter_expression(expr: str) -> Tuple[str, str]:
    """Parse filter expression like 'chunk.reasoning:nonempty'.
    
    Args:
        expr: Filter expression
        
    Returns:
        Tuple of (field_path, condition)
    """
    if ":" in expr:
        field, condition = expr.split(":", 1)
        return field.strip(), condition.strip()
    return expr.strip(), "exists"


def check_filter_condition(value: Any, condition: str) -> bool:
    """Check if value matches filter condition.
    
    Args:
        value: Value to check
        condition: Condition type (exists, nonempty, equals:val, contains:val)
        
    Returns:
        True if condition matches
    """
    if condition == "exists":
        return value is not None
    elif condition == "nonempty":
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (list, dict)):
            return bool(value)
        return True
    elif condition.startswith("equals:"):
        expected = condition[7:]
        return str(value) == expected
    elif condition.startswith("contains:"):
        substring = condition[9:]
        return substring in str(value)
    return False


class ScopeFilterProcessor:
    """Processor to filter logs by scope."""
    
    def __init__(self, scope_filter: str):
        self.scope_filter = scope_filter.lower()
    
    def __call__(
        self, logger: WrappedLogger, method_name: str, event_dict: EventDict
    ) -> EventDict:
        if not self.scope_filter:
            return event_dict
        
        scope = event_dict.get("scope", "")
        if self.scope_filter not in scope.lower():
            raise structlog.DropEvent
        
        return event_dict


class CustomFilterProcessor:
    """Processor to filter logs by custom expressions."""
    
    def __init__(self, filter_expressions: List[str]):
        self.filters = [parse_filter_expression(expr) for expr in filter_expressions]
    
    def __call__(
        self, logger: WrappedLogger, method_name: str, event_dict: EventDict
    ) -> EventDict:
        if not self.filters:
            return event_dict
        
        # All filters must match (AND logic)
        for field_path, condition in self.filters:
            value = get_nested_value(event_dict, field_path)
            if not check_filter_condition(value, condition):
                raise structlog.DropEvent
        
        return event_dict


class DataFormatterProcessor:
    """Processor to format structured data in event_dict."""
    
    def __init__(self, show_data: bool, data_fields: List[str]):
        self.show_data = show_data
        self.data_fields = data_fields
    
    def __call__(
        self, logger: WrappedLogger, method_name: str, event_dict: EventDict
    ) -> EventDict:
        if not self.show_data:
            # Remove data fields from output
            for field in self.data_fields:
                event_dict.pop(field, None)
        
        return event_dict


def console_renderer(show_data: bool) -> Callable:
    """Create a custom console renderer.
    
    Args:
        show_data: Whether to show full data fields
        
    Returns:
        Renderer function
    """
    def render(logger: WrappedLogger, name: str, event_dict: EventDict) -> str:
        # Extract standard fields
        timestamp = event_dict.pop("timestamp", "")
        level = event_dict.pop("level", "info").upper()
        scope = event_dict.pop("scope", "default")
        event = event_dict.pop("event", "")
        
        # Color codes
        colors = {
            "DEBUG": "\033[36m",    # Cyan
            "INFO": "\033[32m",     # Green
            "WARNING": "\033[33m",  # Yellow
            "ERROR": "\033[31m",    # Red
            "CRITICAL": "\033[35m", # Magenta
        }
        reset = "\033[0m"
        dim = "\033[2m"
        
        level_color = colors.get(level, "")
        
        # Format base line
        output = f"\033[32m{timestamp}\033[0m | {level_color}{level: <8}{reset} | \033[36m{scope: <12}\033[0m | {level_color}{event}{reset}\n"
        
        # Add data fields if enabled
        if show_data and event_dict:
            for key, value in event_dict.items():
                if isinstance(value, (dict, list)):
                    formatted = format_log_data(value)
                    output += f"  {dim}{key}={formatted}{reset}\n"
                else:
                    output += f"  {dim}{key}={value}{reset}\n"
        
        return output
    
    return render


def configure_logging() -> None:
    """Configure logging based on environment variables.
    
    Environment variables:
        LOG_LEVEL: Set log level (DEBUG, INFO, WARNING, ERROR). Default: INFO
        LOG_SCOPE: Filter logs by scope/module (e.g., "core", "provider"). Default: all
        LOG_DATA: Show full data in logs (true/false). Default: false
        LOG_FILTER: Custom filter expressions (comma-separated). Examples:
            - "chunk.reasoning:nonempty" - Only logs where chunk.reasoning exists and is non-empty
            - "chunk:exists,message:contains:processing" - Multiple filters (AND logic)
    
    Examples:
        LOG_LEVEL=DEBUG python script.py
        LOG_LEVEL=DEBUG LOG_SCOPE=provider python script.py
        LOG_LEVEL=DEBUG LOG_DATA=true python script.py
        LOG_LEVEL=DEBUG LOG_FILTER="chunk.reasoning:nonempty" python script.py
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_scope = os.getenv("LOG_SCOPE", "").lower()
    log_data = os.getenv("LOG_DATA", "false").lower() in ("true", "1", "yes")
    log_filter = os.getenv("LOG_FILTER", "")
    
    # Parse filter expressions
    filter_expressions = [f.strip() for f in log_filter.split(",") if f.strip()]
    
    # Data fields that should be formatted/hidden based on LOG_DATA
    data_fields = ["chunk", "partials", "finals", "core_partials", "messages", 
                   "native_messages", "final_native", "final_core"]
    
    # Build processor chain
    processors: List[Any] = [
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="%H:%M:%S.%f", utc=False),
    ]
    
    # Add scope filter if specified
    if log_scope:
        processors.append(ScopeFilterProcessor(log_scope))
    
    # Add custom filters if specified
    if filter_expressions:
        processors.append(CustomFilterProcessor(filter_expressions))
    
    # Add data formatter
    processors.append(DataFormatterProcessor(log_data, data_fields))
    
    # Add console renderer
    processors.append(console_renderer(log_data))
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(structlog.stdlib.logging, log_level, structlog.stdlib.logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


_logging_configured = False


def get_logger(scope: str):
    """Get a logger instance bound to a specific scope.
    
    Args:
        scope: Scope identifier (e.g., "core", "provider", "extension")
        
    Returns:
        Logger instance bound to the specified scope.
    """
    global _logging_configured
    if not _logging_configured:
        configure_logging()
        _logging_configured = True
    return structlog.get_logger().bind(scope=scope)

"""Utility functions for agent_core."""

import os
import sys
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


def make_scope_filter(scope_filter: str) -> Callable:
    """Create a processor to filter logs by scope field.
    
    Args:
        scope_filter: Scope substring to filter by
        
    Returns:
        Processor function
    """
    scope_lower = scope_filter.lower()
    
    def filter_by_scope(
        logger: WrappedLogger, method_name: str, event_dict: EventDict
    ) -> EventDict:
        if not scope_filter:
            return event_dict
        
        scope = event_dict.get("scope", "")
        if scope_lower not in scope.lower():
            raise structlog.DropEvent
        
        return event_dict
    
    return filter_by_scope


def make_field_filter(filter_expressions: List[str]) -> Callable:
    """Create a processor to filter logs by custom field expressions.
    
    Args:
        filter_expressions: List of filter expressions (field:condition)
        
    Returns:
        Processor function
    """
    filters = [parse_filter_expression(expr) for expr in filter_expressions]
    
    def filter_by_field(
        logger: WrappedLogger, method_name: str, event_dict: EventDict
    ) -> EventDict:
        if not filters:
            return event_dict
        
        # All filters must match (AND logic)
        for field_path, condition in filters:
            value = get_nested_value(event_dict, field_path)
            if not check_filter_condition(value, condition):
                raise structlog.DropEvent
        
        return event_dict
    
    return filter_by_field


def make_data_dropper(drop_fields: List[str]) -> Callable:
    """Create a processor to drop data fields.
    
    Args:
        drop_fields: List of field names to drop
        
    Returns:
        Processor function
    """
    def drop_data_fields(
        logger: WrappedLogger, method_name: str, event_dict: EventDict
    ) -> EventDict:
        for field in drop_fields:
            event_dict.pop(field, None)
        return event_dict
    
    return drop_data_fields


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
    log_scope = os.getenv("LOG_SCOPE", "")
    log_data = os.getenv("LOG_DATA", "false").lower() in ("true", "1", "yes")
    log_filter = os.getenv("LOG_FILTER", "")
    
    # Parse filter expressions
    filter_expressions = [f.strip() for f in log_filter.split(",") if f.strip()]
    
    # Data fields that should be hidden when LOG_DATA=false
    data_fields = ["chunk", "partials", "finals", "core_partials", "messages", 
                   "native_messages", "final_native", "final_core"]
    
    # Build processor chain using structlog's built-in processors where possible
    processors: List[Any] = [
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="%H:%M:%S.%f", utc=False),
    ]
    
    # Add scope filter if specified
    if log_scope:
        processors.append(make_scope_filter(log_scope))
    
    # Add custom field filters if specified
    if filter_expressions:
        processors.append(make_field_filter(filter_expressions))
    
    # Drop data fields if LOG_DATA is false
    if not log_data:
        processors.append(make_data_dropper(data_fields))
    
    # Use structlog's built-in ConsoleRenderer for colored output
    processors.append(
        structlog.dev.ConsoleRenderer(
            colors=True,
            pad_event_to=30,
        )
    )
    
    # Map log level string to structlog level
    level_map = {
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50,
    }
    min_level = level_map.get(log_level, 20)
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(min_level),
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

"""Utility functions for agent_core."""

import os
import sys
import logging
from typing import Any, Callable, List, Tuple, Dict, Optional
from functools import reduce
import structlog
from structlog.types import EventDict, WrappedLogger
from structlog.processors import CallsiteParameterAdder, CallsiteParameter
from jsonpath_ng import parse as jsonpath_parse

# Repository root (used for relative paths in logging)
REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)


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
    """Get nested value from dict using dot notation or JSONPath.
    
    Supports both simple dot notation and JSONPath expressions:
    - Simple: "chunk.reasoning" 
    - Array index: "messages[0].content"
    - JSONPath: "$.messages[?(@.role=='user')]"
    
    Args:
        data: Dictionary to search
        path: Dot-separated path or JSONPath expression
        
    Returns:
        Value at path or None if not found. For JSONPath queries returning
        multiple matches, returns the first match.
    """
    # If path contains brackets, use JSONPath
    if '[' in path:
        try:
            # Ensure path starts with $ for JSONPath
            jsonpath_expr = path if path.startswith('$') else f'$.{path}'
            jsonpath = jsonpath_parse(jsonpath_expr)
            matches = jsonpath.find(data)
            if matches:
                return matches[0].value
            return None
        except Exception:
            # Fall back to dot notation if JSONPath parsing fails
            pass
    
    # Simple dot notation
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


def make_logger_filter(logger_filter: str) -> Callable:
    """Create a processor to filter logs by logger name.
    
    Args:
        logger_filter: Logger name substring to filter by
        
    Returns:
        Processor function
    """
    filter_lower = logger_filter.lower()
    
    def filter_by_logger(
        logger: WrappedLogger, method_name: str, event_dict: EventDict
    ) -> EventDict:
        if not logger_filter:
            return event_dict
        
        # Logger name is added by add_logger_name processor
        logger_name = event_dict.get("logger", "")
        if filter_lower not in logger_name.lower():
            raise structlog.DropEvent
        
        return event_dict
    
    return filter_by_logger


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


def make_data_filter(allowed_fields: List[str]) -> Callable:
    """Create a processor to filter data fields (whitelist approach).
    
    Args:
        allowed_fields: List of field names to keep. If empty, drop all extra fields.
                       If None, keep all fields (no filtering).
        
    Returns:
        Processor function
    """
    # Standard fields that should always be preserved
    standard_fields = {"event", "timestamp", "level", "logger"}
    
    def filter_data_fields(
        logger: WrappedLogger, method_name: str, event_dict: EventDict
    ) -> EventDict:
        if allowed_fields is None:
            # No filtering - keep everything
            return event_dict
        
        # Whitelist: keep only standard fields + allowed fields
        allowed_set = standard_fields | set(allowed_fields)
        keys_to_drop = [k for k in event_dict.keys() if k not in allowed_set]
        
        for key in keys_to_drop:
            event_dict.pop(key)
        
        return event_dict
    
    return filter_data_fields


def make_position_processor() -> Callable:
    """Create a processor that adds 'pos' field as "file:line" when enabled.
    
    Uses structlog's CallsiteParameterAdder to capture pathname and lineno and
    then formats them into a compact "file:line" string stored in the "pos"
    field of the event_dict.
    """
    callsite_adder = CallsiteParameterAdder(
        additional_ignores=[__name__],
        parameters=[CallsiteParameter.PATHNAME, CallsiteParameter.LINENO],
    )
    
    def add_position(
        logger: WrappedLogger, method_name: str, event_dict: EventDict
    ) -> EventDict:
        event_dict = callsite_adder(logger, method_name, event_dict)
        pathname = event_dict.get("pathname")
        lineno = event_dict.get("lineno")
        if pathname and lineno:
            # Compute path relative to repository root for stable, concise output
            try:
                rel_path = os.path.relpath(str(pathname), REPO_ROOT)
            except Exception:
                rel_path = os.path.basename(str(pathname))
            event_dict["pos"] = f"{rel_path}:{lineno}"
        # Drop raw callsite details to avoid noisy output
        event_dict.pop("pathname", None)
        event_dict.pop("lineno", None)
        return event_dict
    
    return add_position


def configure_logging(
    *,
    colors: Optional[bool] = None,
    log_file_path: Optional[str] = None,
) -> None:
    """Configure logging based on environment variables and optional overrides.
    
    Environment variables:
        LOG_LEVEL: Set log level (DEBUG, INFO, WARNING, ERROR). Default: INFO
        LOG_SCOPE: Filter logs by logger name (e.g., "core", "provider"). Default: all
        LOG_DATA: Comma-separated list of data fields to show. Default: show all
            - Not set: Show all data fields (no filtering)
            - "": Drop all extra fields (only show standard fields)
            - "chunk,partials": Only show chunk and partials fields
        LOG_FILTER: Custom filter expressions (comma-separated). Examples:
            - "chunk.reasoning:nonempty" - Only logs where chunk.reasoning exists and is non-empty
            - "chunk:exists,message:contains:processing" - Multiple filters (AND logic)
        LOG_POS: When set to a truthy value, include source position as
            "file:line" in the "pos" field (e.g., "provider.py:354").
        LOG_COLORS: When set, enable or disable ANSI colors in the
            console renderer. Truthy values: 1,true,yes,y,on. Falsy
            values: 0,false,no,n,off.
        LOG_FILE: When set, path to a log file where structlog output is
            written instead of stdout (overridden by ``log_file_path``).
    
    Keyword arguments allow applications to override defaults:
        colors: When True/False, force enabling or disabling ANSI colors in
            the ConsoleRenderer. When None (default), colors are enabled.
        log_file_path: Optional path to a log file. When provided, takes
            precedence over the LOG_FILE environment variable.
    
    Examples:
        LOG_LEVEL=DEBUG python script.py
        LOG_LEVEL=DEBUG LOG_SCOPE=provider python script.py
        LOG_LEVEL=DEBUG LOG_DATA="chunk,partials" python script.py
        LOG_LEVEL=DEBUG LOG_DATA="" python script.py  # Drop all extra fields
        LOG_LEVEL=DEBUG LOG_FILTER="chunk.reasoning:nonempty" python script.py
        LOG_LEVEL=DEBUG LOG_POS=true python script.py  # Include file:line
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_scope = os.getenv("LOG_SCOPE", "")
    log_data_env = os.getenv("LOG_DATA")
    log_filter = os.getenv("LOG_FILTER", "")
    log_pos_env = os.getenv("LOG_POS", "")
    log_colors_env = os.getenv("LOG_COLORS")
    env_log_file = os.getenv("LOG_FILE")


    # CLI or application-provided path takes precedence over environment.
    if log_file_path is None:
        log_file_path = env_log_file
    
    # Parse LOG_DATA
    # - None (not set): Show all fields (no filtering)
    # - Empty string "": Drop all extra fields
    # - "field1,field2": Only show these fields
    if log_data_env is None:
        allowed_fields = None  # Show everything
    elif log_data_env.strip() == "":
        allowed_fields = []  # Drop all extra fields
    else:
        allowed_fields = [f.strip() for f in log_data_env.split(",") if f.strip()]
    
    # Parse filter expressions
    filter_expressions = [f.strip() for f in log_filter.split(",") if f.strip()]
    
    # Build processor chain starting with structlog defaults
    processors: List[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
    ]
    
    # Add logger name filter if specified
    if log_scope:
        processors.append(make_logger_filter(log_scope))
    
    # Add custom field filters if specified
    if filter_expressions:
        processors.append(make_field_filter(filter_expressions))
    
    # Apply data field filtering (whitelist approach)
    # None = show all, [] = drop all extra, ['chunk'] = only show chunk
    if allowed_fields is not None:
        processors.append(make_data_filter(allowed_fields))

    # Add source position (file:line) when LOG_POS is truthy
    if log_pos_env.lower() in ("1", "true", "yes", "y", "on"):
        processors.append(make_position_processor())
    
    # Decide whether to use ANSI colors in the ConsoleRenderer.
    # Precedence: explicit ``colors`` arg > LOG_COLORS > default True.
    if colors is not None:
        use_colors = bool(colors)
    else:
        env_val = (log_colors_env or "").strip().lower()
        if env_val in ("1", "true", "yes", "y", "on"):
            use_colors = True
        elif env_val in ("0", "false", "no", "n", "off"):
            use_colors = False
        else:
            use_colors = True

    # Use structlog's built-in ConsoleRenderer for (optionally colored) output
    processors.append(
        structlog.dev.ConsoleRenderer(
            colors=use_colors,
            pad_event_to=30,
        )
    )
    
    # Convert log level string to logging constant
    min_level = getattr(logging, log_level, logging.INFO)
    
    # Determine output stream (stdout by default, optional log file)
    log_stream = sys.stdout
    if log_file_path:
        try:
            base_dir = os.path.dirname(log_file_path) or "."
            os.makedirs(base_dir, exist_ok=True)
            log_stream = open(log_file_path, "a", encoding="utf-8")
        except Exception:
            # Fall back to stdout on any file error
            log_stream = sys.stdout

    print("Configuring logging")

    # Configure structlog (preserving defaults where possible)
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(min_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=log_stream),
        cache_logger_on_first_use=False,
    )

    # Mark logging as configured so get_logger() does not reconfigure.
    global _logging_configured
    _logging_configured = True


_logging_configured = False


def get_logger(name: str):
    """Get a logger instance with a specific name.
    
    Args:
        name: Logger name (e.g., "core", "provider", "extension")
        
    Returns:
        Logger instance bound with the specified name.
    """
    global _logging_configured
    if not _logging_configured:
        configure_logging()
        _logging_configured = True
    return structlog.get_logger().bind(logger=name)

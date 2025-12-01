"""Utility functions for agent_core."""

import os
import sys
from typing import Any, Callable, List, Tuple
from functools import reduce
from loguru import logger


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


def format_log_data(data: Any, max_length: int = 200) -> str:
    """Format data for logging with truncation.
    
    Args:
        data: Data to format (dict, list, str, etc.)
        max_length: Maximum string length before truncation
        
    Returns:
        Formatted string representation of the data
    """
    import json
    
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


def configure_logging() -> None:
    """Configure logging based on environment variables.
    
    Environment variables:
        LOG_LEVEL: Set log level (DEBUG, INFO, WARNING, ERROR). Default: INFO
        LOG_SCOPE: Filter logs by scope/module (e.g., "core", "provider"). Default: all
        LOG_DATA: Show full data in logs (true/false). Default: false
    
    Examples:
        LOG_LEVEL=DEBUG python script.py
        LOG_LEVEL=DEBUG LOG_SCOPE=provider python script.py
        LOG_LEVEL=DEBUG LOG_DATA=true python script.py
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_scope = os.getenv("LOG_SCOPE", "").lower()
    log_data = os.getenv("LOG_DATA", "false").lower() in ("true", "1", "yes")
    
    logger.remove()
    
    def scope_filter(record):
        if not log_scope:
            return True
        module = record.get("extra", {}).get("scope", record.get("name", ""))
        return log_scope in module.lower()
    
    def sink_with_data(message):
        """Custom sink that adds extra data fields when LOG_DATA is enabled."""
        record = message.record
        
        # Write the base message
        sys.stderr.write(str(message))
        
        # Add extra data if LOG_DATA is enabled
        if log_data:
            extra_keys = [k for k in record["extra"].keys() if k != "scope"]
            if extra_keys:
                for key in extra_keys:
                    value = record["extra"][key]
                    # Format the value
                    if isinstance(value, (dict, list)):
                        formatted = format_log_data(value, max_length=500)
                        sys.stderr.write(f"  \033[2m{key}={formatted}\033[0m\n")
                    else:
                        sys.stderr.write(f"  \033[2m{key}={value}\033[0m\n")
    
    if log_data:
        logger.add(
            sink_with_data,
            level=log_level,
            filter=scope_filter,
            format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{extra[scope]: <12}</cyan> | <level>{message}</level>",
        )
    else:
        logger.add(
            sys.stderr,
            level=log_level,
            filter=scope_filter,
            format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{extra[scope]: <12}</cyan> | <level>{message}</level>",
        )


logger.configure(extra={"scope": "default"})
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
    return logger.bind(scope=scope)

"""Utility functions for agent_core."""

from typing import Any, Callable, List, Tuple
from functools import reduce


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

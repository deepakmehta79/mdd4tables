"""mdd4tables: Multi-Valued Decision Diagrams (MDD) for tabular data.

Build compressed MDDs from tables (each row is a path), query with partial inputs,
and rank completions using conditional probabilities.
"""

from .schema import DimensionType, Schema, DimensionSpec
from .config import BuildConfig, QueryConfig, OrderingConfig
from .mdd import MDD
from .builder import Builder
from .ordering import propose_order, evaluate_order

__all__ = [
    "DimensionType", "Schema", "DimensionSpec",
    "BuildConfig", "QueryConfig", "OrderingConfig",
    "MDD", "Builder",
    "propose_order", "evaluate_order",
]

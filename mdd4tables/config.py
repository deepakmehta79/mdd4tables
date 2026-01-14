from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass(frozen=True)
class OrderingConfig:
    strategy: str = "heuristic"  # fixed|heuristic|search
    # search knobs
    time_budget_s: float = 2.0
    max_evals: int = 100
    beam_width: int = 8
    objective: str = "nodes_plus_arcs"  # nodes|arcs|nodes_plus_arcs
    seed: int = 0

@dataclass(frozen=True)
class BuildConfig:
    ordering: str = "heuristic"  # fixed|heuristic|search
    ordering_config: OrderingConfig = OrderingConfig()
    # Compilation method: trie (build trie then reduce) or slice (incremental slice-based)
    compilation_method: str = "trie"  # trie|slice
    # Compression / merging (only applies to trie method)
    enable_reduction: bool = True
    # Smoothing for probability queries
    laplace_alpha: float = 0.1
    # For numeric binning if a DimensionSpec doesn't specify
    default_numeric_bins: Optional[Dict] = None

@dataclass(frozen=True)
class QueryConfig:
    laplace_alpha: float = 0.1
    # weight for hybrid distance/prob scoring (higher prefers probability)
    lambda_logprob: float = 1.0

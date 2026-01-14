from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import pandas as pd

from .mdd import Node
from .schema import Schema

def _slice_signature(df: pd.DataFrame, remaining_dims: List[str]) -> Tuple:
    """Hashable signature of a slice π_P(σ_R(CB)).

    Slice is represented as the sorted set of tuples of the remaining dimensions.
    This follows Nicholson, Bridge, and Wilson (2006), Algorithm 1.
    """
    if not remaining_dims:
        return ("<EMPTY_PROJECTION>",)
    proj = df[remaining_dims].drop_duplicates()
    tuples = [tuple(r) for r in proj.itertuples(index=False, name=None)]
    tuples.sort()
    return tuple(tuples)

@dataclass
class SliceCompiler:
    """Slice-based incremental compiler (Nicholson–Bridge–Wilson 2006, Algorithm 1)."""
    schema: Schema
    dim_names: List[str]

    def compile(self, df: pd.DataFrame) -> Tuple[List[Node], int, int]:
        working = df[self.dim_names].copy()

        nodes: List[Node] = []
        root = 0
        nodes.append(Node(layer=0, edges={}, edge_counts={}, reach_count=0, terminal_count=0))

        # layer -> {slice_signature: node_id}
        slice_index: List[Dict[Tuple, int]] = [dict() for _ in range(len(self.dim_names) + 1)]
        slice_index[0][("<SOURCE>",)] = root

        for _, row in working.iterrows():
            current = root
            nodes[current].reach_count += 1
            prefix: Dict[str, Any] = {}

            for i, dim in enumerate(self.dim_names):
                v = row[dim]
                prefix[dim] = v
                remaining = self.dim_names[i+1:]
                n = nodes[current]

                if v in n.edges:
                    n.edge_counts[v] = n.edge_counts.get(v, 0) + 1
                    current = n.edges[v]
                    nodes[current].reach_count += 1
                    continue

                # slice := π_P(σ_R(CB))
                mask = pd.Series(True, index=working.index)
                for k, val in prefix.items():
                    mask &= (working[k] == val)
                selected = working.loc[mask]
                sig = _slice_signature(selected, remaining)

                nxt_layer = i + 1
                if sig in slice_index[nxt_layer]:
                    next_id = slice_index[nxt_layer][sig]
                else:
                    next_id = len(nodes)
                    nodes.append(Node(layer=nxt_layer, edges={}, edge_counts={}, reach_count=0, terminal_count=0))
                    slice_index[nxt_layer][sig] = next_id

                n.edges[v] = next_id
                n.edge_counts[v] = n.edge_counts.get(v, 0) + 1
                current = next_id
                nodes[current].reach_count += 1

            nodes[current].terminal_count += 1

        terminal_layer = len(self.dim_names)
        return nodes, root, terminal_layer

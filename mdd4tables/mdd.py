from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Iterable
import math
import heapq

@dataclass(frozen=True)
class Arc:
    label: Any
    child: int
    count: int

@dataclass
class Node:
    layer: int
    # label -> child_id
    edges: Dict[Any, int]
    # label -> count along this outgoing arc
    edge_counts: Dict[Any, int]
    # how many traces reach this node
    reach_count: int = 0
    terminal_count: int = 0  # number of traces terminating here

    def __repr__(self) -> str:
        return (f"Node(layer={self.layer}, edges={len(self.edges)}, "
                f"reach={self.reach_count}, terminal={self.terminal_count})")

@dataclass(frozen=True)
class QueryResult:
    path: Dict[str, Any]
    score: float
    details: Dict[str, Any]

class MDD:
    """Compressed Multi-Valued Decision Diagram."""

    def __init__(self, dim_names: List[str], nodes: List[Node], root: int, terminal_layer: int,
                 laplace_alpha: float = 0.1, bin_models: Optional[Dict[str, Any]] = None):
        self.dim_names = dim_names
        self.nodes = nodes
        self.root = root
        self.terminal_layer = terminal_layer
        self.laplace_alpha = laplace_alpha
        self.bin_models = bin_models or {}

    def __repr__(self) -> str:
        size = self.size()
        return f"MDD(dims={self.dim_names}, nodes={size['nodes']}, arcs={size['arcs']})"

    # ------------------------
    # Validation helpers
    # ------------------------
    def _validate_k(self, k: int, name: str = "k") -> None:
        if not isinstance(k, int) or k < 1:
            raise ValueError(f"{name} must be a positive integer, got {k}")

    def _validate_partial(self, partial: Dict[str, Any]) -> None:
        if not isinstance(partial, dict):
            raise TypeError(f"partial must be a dict, got {type(partial).__name__}")
        unknown = set(partial.keys()) - set(self.dim_names)
        if unknown:
            raise ValueError(f"Unknown dimensions in partial: {unknown}")

    # ------------------------
    # Basic traversal utilities
    # ------------------------
    def _children(self, node_id: int) -> Iterable[Tuple[Any, int, int]]:
        n = self.nodes[node_id]
        for lab, ch in n.edges.items():
            yield lab, ch, n.edge_counts.get(lab, 0)

    def size(self) -> Dict[str, int]:
        arcs = sum(len(n.edges) for n in self.nodes)
        return {"nodes": len(self.nodes), "arcs": arcs, "layers": self.terminal_layer}

    # ------------------------
    # Exact existence
    # ------------------------
    def exists(self, x: Dict[str, Any]) -> bool:
        """Check if an exact path exists in the MDD.

        Args:
            x: Dict mapping dimension names to values.

        Returns:
            True if the path exists, False otherwise.
        """
        nid = self.root
        for layer, dim in enumerate(self.dim_names):
            if dim not in x:
                return False
            v = x[dim]
            n = self.nodes[nid]
            if v not in n.edges:
                return False
            nid = n.edges[v]
        return self.nodes[nid].terminal_count > 0

    # ------------------------
    # Count matching paths
    # ------------------------
    def count(self, pattern: Optional[Dict[str, Any]] = None) -> int:
        """Count paths matching a pattern (without enumerating them).

        Args:
            pattern: Dict with dimension constraints (None = wildcard).
                     If None, counts all paths.

        Returns:
            Number of matching paths.
        """
        if pattern is None:
            pattern = {}
        self._validate_partial(pattern)

        def _count_dfs(nid: int, layer: int) -> int:
            if layer == self.terminal_layer:
                return self.nodes[nid].terminal_count
            dim = self.dim_names[layer]
            n = self.nodes[nid]
            want = pattern.get(dim, None)
            total = 0
            if want is None:
                for lab, ch in n.edges.items():
                    total += _count_dfs(ch, layer + 1)
            else:
                if want in n.edges:
                    total = _count_dfs(n.edges[want], layer + 1)
            return total

        return _count_dfs(self.root, 0)

    # ------------------------
    # Pattern match with wildcards (brute DFS)
    # ------------------------
    def match(self, pattern: Dict[str, Any], limit: int = 1000) -> List[Dict[str, Any]]:
        """Find all paths matching a pattern.

        Args:
            pattern: Dict with dimension constraints (missing dims = wildcard).
            limit: Maximum number of results to return.

        Returns:
            List of matching paths as dicts.
        """
        self._validate_partial(pattern)
        if limit < 1:
            raise ValueError(f"limit must be positive, got {limit}")

        out: List[Dict[str, Any]] = []

        def dfs(nid: int, layer: int, acc: Dict[str, Any]) -> None:
            if len(out) >= limit:
                return
            if layer == self.terminal_layer:
                if self.nodes[nid].terminal_count > 0:
                    out.append(dict(acc))
                return
            dim = self.dim_names[layer]
            want = pattern.get(dim, None)
            n = self.nodes[nid]
            if want is None:
                for lab, ch in n.edges.items():
                    acc[dim] = lab
                    dfs(ch, layer+1, acc)
                acc.pop(dim, None)
            else:
                if want in n.edges:
                    acc[dim] = want
                    dfs(n.edges[want], layer+1, acc)
                    acc.pop(dim, None)

        dfs(self.root, 0, {})
        return out

    # ------------------------
    # Conditional probability helpers
    # ------------------------
    def _cond_prob(self, nid: int, label: Any) -> float:
        n = self.nodes[nid]
        total = float(sum(n.edge_counts.values()))
        k = float(len(n.edge_counts))
        alpha = float(self.laplace_alpha)
        num = float(n.edge_counts.get(label, 0))
        return (num + alpha) / (total + alpha * max(k, 1.0))

    # ------------------------
    # Completion: top-k by MAP (beam search)
    # ------------------------
    def complete(self, partial: Dict[str, Any], k: int = 5, beam: int = 25) -> List[QueryResult]:
        """Find top-k completions ranked by conditional probability.

        Args:
            partial: Dict with known dimension values (missing = to be completed).
            k: Number of top results to return.
            beam: Beam width for search (higher = more thorough but slower).

        Returns:
            List of QueryResult with path, score (log-probability), and details.
        """
        self._validate_partial(partial)
        self._validate_k(k)
        if beam < 1:
            raise ValueError(f"beam must be positive, got {beam}")

        # beam items: (neg_logprob, nid, layer, path_dict)
        start = (0.0, self.root, 0, {})
        beam_list = [start]

        for layer in range(self.terminal_layer):
            dim = self.dim_names[layer]
            new_beam = []
            for neglogp, nid, _, path in beam_list:
                n = self.nodes[nid]
                fixed = partial.get(dim, None)
                if fixed is not None:
                    if fixed in n.edges:
                        p = self._cond_prob(nid, fixed)
                        nd = n.edges[fixed]
                        npth = dict(path); npth[dim] = fixed
                        new_beam.append((neglogp - math.log(max(p, 1e-15)), nd, layer+1, npth))
                    # else: dead end
                else:
                    for lab, nd in n.edges.items():
                        p = self._cond_prob(nid, lab)
                        npth = dict(path); npth[dim] = lab
                        new_beam.append((neglogp - math.log(max(p, 1e-15)), nd, layer+1, npth))
            new_beam.sort(key=lambda t: t[0])
            beam_list = new_beam[:beam]

            if not beam_list:
                break

        # finalize
        beam_list.sort(key=lambda t: t[0])
        results: List[QueryResult] = []
        for neglogp, nid, layer, path in beam_list:
            if layer == self.terminal_layer and self.nodes[nid].terminal_count > 0:
                results.append(QueryResult(path=path, score=-neglogp, details={"logprob": -neglogp}))
                if len(results) >= k:
                    break
        return results

    # ------------------------
    # Nearest: A* over layered DAG with per-dimension distance
    # (distance model is passed in via dist_fn[dim](want, candidate)->cost)
    # ------------------------
    def nearest(self, partial: Dict[str, Any], dist_fns: Dict[str, Any], k: int = 5) -> List[QueryResult]:
        """Find k-nearest paths using A* search with custom distance functions.

        Args:
            partial: Dict with target dimension values.
            dist_fns: Dict mapping dimension names to distance functions (a, b) -> float.
            k: Number of results to return.

        Returns:
            List of QueryResult with path, score (negative distance), and details.
        """
        self._validate_partial(partial)
        self._validate_k(k)

        # State: (f, g, counter, -logp, nid, layer, path)
        # f = g + h; h is 0 (admissible but weak)
        # counter ensures unique comparison for heapq tiebreaking
        pq = []
        counter = 0
        heapq.heappush(pq, (0.0, 0.0, counter, 0.0, self.root, 0, {}))
        counter += 1
        results: List[QueryResult] = []
        seen = set()

        while pq and len(results) < k:
            f, g, _, neglogp, nid, layer, path = heapq.heappop(pq)
            key = (nid, layer, tuple(sorted(path.items())))
            if key in seen:
                continue
            seen.add(key)

            if layer == self.terminal_layer:
                if self.nodes[nid].terminal_count > 0:
                    score = -g  # distance-only score (negative cost)
                    results.append(QueryResult(path=path, score=score, details={"distance": g, "logprob": -neglogp}))
                continue

            dim = self.dim_names[layer]
            want = partial.get(dim, None)
            n = self.nodes[nid]
            for lab, nd in n.edges.items():
                step = 0.0
                if want is not None:
                    fn = dist_fns.get(dim)
                    step = float(fn(want, lab)) if fn else (0.0 if want == lab else 1.0)
                # prob term is tracked for hybrid usage by caller if desired
                p = self._cond_prob(nid, lab)
                nneglogp = neglogp - math.log(max(p, 1e-15))
                npth = dict(path); npth[dim] = lab
                ng = g + step
                heapq.heappush(pq, (ng, ng, counter, nneglogp, nd, layer+1, npth))
                counter += 1

        return results

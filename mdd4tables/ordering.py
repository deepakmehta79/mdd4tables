from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd

from .schema import Schema, DimensionType
from .config import OrderingConfig

@dataclass
class OrderEval:
    order: List[str]
    est_score: float
    diagnostics: Dict[str, float]

def _entropy(s: pd.Series) -> float:
    vc = s.value_counts(dropna=False)
    p = (vc / vc.sum()).to_numpy(dtype=float)
    return float(-(p * np.log2(np.clip(p, 1e-12, 1.0))).sum())

def propose_order(df: pd.DataFrame, schema: Schema, cfg: OrderingConfig) -> OrderEval:
    """Heuristic proposal: combine entropy + effective cardinality.

    Intuition: dimensions with lower branching and/or higher repetition can reduce fragmentation.
    We sort by (entropy, cardinality) ascending by default.
    """
    cols = schema.names()
    diag = {}
    scores = []
    for c in cols:
        s = df[c]
        ent = _entropy(s.astype("object"))
        card = float(s.nunique(dropna=False))
        # numeric: use binned-cardinality proxy via quantiles if not already binned
        if schema.get(c).dtype == DimensionType.NUMERIC:
            # proxy: sqrt(card) to avoid over-penalizing
            card = float(np.sqrt(max(card, 1.0)))
        sc = ent + 0.05 * card
        scores.append((sc, c))
        diag[f"entropy:{c}"] = ent
        diag[f"card:{c}"] = float(s.nunique(dropna=False))
    scores.sort()
    order = [c for _, c in scores]
    return OrderEval(order=order, est_score=float(sum(sc for sc,_ in scores)), diagnostics=diag)

def evaluate_order(df: pd.DataFrame, order: List[str]) -> Dict[str, float]:
    """Lightweight evaluation proxy: sum of prefix distinct counts."""
    prefix = []
    total = 0.0
    for c in order:
        prefix.append(c)
        total += float(df[prefix].drop_duplicates().shape[0])
    return {"prefix_distinct_sum": total}

def search_order(df: pd.DataFrame, schema: Schema, cfg: OrderingConfig) -> OrderEval:
    """Budgeted randomized local search using the proxy objective.

    Terminates when either max_evals or time_budget_s is exceeded.
    """
    import time

    rng = np.random.default_rng(cfg.seed)
    cols = schema.names()
    best = cols[:]
    best_score = evaluate_order(df, best)["prefix_distinct_sum"]
    evals = 1
    start_time = time.time()

    while evals < cfg.max_evals:
        # Check time budget
        if (time.time() - start_time) >= cfg.time_budget_s:
            break

        cand = best[:]
        i, j = rng.integers(0, len(cols), size=2)
        cand[i], cand[j] = cand[j], cand[i]
        sc = evaluate_order(df, cand)["prefix_distinct_sum"]
        evals += 1
        if sc < best_score:
            best, best_score = cand, sc

    elapsed = time.time() - start_time
    diag = {"prefix_distinct_sum": float(best_score), "evals": float(evals), "elapsed_s": elapsed}
    return OrderEval(order=best, est_score=float(best_score), diagnostics=diag)

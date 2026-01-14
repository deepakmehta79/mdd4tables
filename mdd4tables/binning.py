from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

# Default token for missing values
DEFAULT_MISSING_TOKEN = "__MISSING__"

@dataclass
class BinModel:
    edges: np.ndarray  # length k+1
    strategy: str
    k: int
    missing_token: Any = DEFAULT_MISSING_TOKEN

    def transform_one(self, x: Any) -> str:
        if x is None or (isinstance(x, float) and np.isnan(x)):
            return self.missing_token
        # right-inclusive last bin
        idx = np.searchsorted(self.edges, x, side="right") - 1
        idx = int(np.clip(idx, 0, len(self.edges)-2))
        lo, hi = self.edges[idx], self.edges[idx+1]
        return f"[{lo:.6g},{hi:.6g})" if idx < len(self.edges)-2 else f"[{lo:.6g},{hi:.6g}]"

    def transform(self, s: pd.Series) -> pd.Series:
        return s.apply(self.transform_one)

def fit_binner(values: pd.Series, bins_cfg: Dict[str, Any],
               missing_token: Any = DEFAULT_MISSING_TOKEN) -> BinModel:
    strat = bins_cfg.get("strategy", "quantile")
    k = int(bins_cfg.get("k", 10))
    x = values.to_numpy()
    x = x[~np.isnan(x)] if x.dtype.kind in ("f","i") else x
    if len(x) == 0:
        # fallback
        edges = np.array([0.0, 1.0])
        return BinModel(edges=edges, strategy=strat, k=1, missing_token=missing_token)

    if strat == "fixed_width":
        lo, hi = float(np.min(x)), float(np.max(x))
        if lo == hi:
            edges = np.array([lo, hi+1e-9])
        else:
            edges = np.linspace(lo, hi, k+1)
    elif strat == "quantile":
        qs = np.linspace(0, 1, k+1)
        edges = np.quantile(x, qs)
        # ensure strictly increasing
        edges = np.unique(edges)
        if len(edges) < 2:
            edges = np.array([float(np.min(x)), float(np.max(x))+1e-9])
    else:
        raise ValueError(f"Unknown binning strategy: {strat}")

    # pad if unique quantiles reduced k
    if len(edges) == 2:
        return BinModel(edges=np.array(edges, dtype=float), strategy=strat, k=1,
                        missing_token=missing_token)
    return BinModel(edges=np.array(edges, dtype=float), strategy=strat, k=len(edges)-1,
                    missing_token=missing_token)

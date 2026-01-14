from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional

class DimensionType(str, Enum):
    CATEGORICAL = "categorical"
    ORDINAL = "ordinal"
    NUMERIC = "numeric"
    MIXED = "mixed"

@dataclass(frozen=True)
class DimensionSpec:
    name: str
    dtype: DimensionType
    # For numeric: binning config (strategy, k, edges...). For ordinal: rank mapping optional.
    bins: Optional[Dict[str, Any]] = None
    rank_map: Optional[Dict[Any, int]] = None
    # Missing handling: token to insert when missing during build
    missing_token: Any = "__MISSING__"

@dataclass
class Schema:
    dims: List[DimensionSpec]
    name_to_index: Dict[str, int] = field(init=False)

    def __post_init__(self) -> None:
        self.name_to_index = {d.name: i for i, d in enumerate(self.dims)}

    def names(self) -> List[str]:
        return [d.name for d in self.dims]

    def get(self, name: str) -> DimensionSpec:
        return self.dims[self.name_to_index[name]]

    def subset(self, ordered_names: List[str]) -> "Schema":
        return Schema([self.get(n) for n in ordered_names])

    def validate(self, cols: Iterable[str]) -> None:
        cols = list(cols)
        missing = [d.name for d in self.dims if d.name not in cols]
        if missing:
            raise ValueError(f"Input missing required columns: {missing}")

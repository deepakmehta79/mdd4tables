# mdd4tables

Build **Multi-Valued Decision Diagrams (MDDs)** from tabular data where:
- each row is a root→terminal path
- each column is a layer
- each distinct value / numeric bin is an arc label

Supports:
- compression via bottom-up merging (canonical reduction)
- arc/node counts and **conditional probabilities**
- partial-input completion + nearest-path search
- dimension ordering heuristics + budgeted search

## Quickstart

```python
import pandas as pd
from mdd4tables import Schema, DimensionSpec, DimensionType, BuildConfig, Builder

df = pd.DataFrame({
    "region": ["EU","EU","US","US"],
    "priority": [1,2,1,3],
    "qty": [10.1, 9.7, 5.0, 4.9],
})

schema = Schema([
    DimensionSpec("region", DimensionType.CATEGORICAL),
    DimensionSpec("priority", DimensionType.ORDINAL),
    DimensionSpec("qty", DimensionType.NUMERIC, bins={"strategy":"quantile", "k": 3}),
])

cfg = BuildConfig(ordering="heuristic")
mdd = Builder(schema, cfg).fit(df)

# partial completion with conditional probability ranking
out = mdd.complete({"region":"EU"}, k=3)
for r in out:
    print(r.path, r.score, r.details)
```

## Install (editable)

```bash
pip install -e .
```

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**mdd4tables** is a Python library that builds **Multi-Valued Decision Diagrams (MDDs)** from tabular data. Each row in a table becomes a root→terminal path through the MDD, each column is a layer, and each distinct value (or numeric bin) is an arc label. The library compresses structures via bottom-up merging and supports querying with conditional probabilities.

## Development Commands

### Installation
```bash
pip install -e .
```

### Running Tests
```bash
python -m pytest tests/
```

Run a single test file:
```bash
python -m pytest tests/test_basic.py
```

Run a specific test:
```bash
python -m pytest tests/test_basic.py::test_build_and_exists
```

### Running Examples
```bash
python examples/demo.py
```

### Optional Dependencies

For visualization support:
```bash
pip install -e ".[viz]"
```

For development tools (pytest, ruff):
```bash
pip install -e ".[dev]"
```

## Core Architecture

### Data Flow: Table → MDD → Query

1. **Schema Definition** (`schema.py`): Define dimensions with types (categorical, ordinal, numeric, mixed)
2. **Builder** (`builder.py`): Constructs the MDD from a DataFrame
3. **MDD** (`mdd.py`): The compressed decision diagram structure with query methods

### Key Components

#### Schema Layer (`schema.py`)
- `DimensionSpec`: Defines each column with:
  - `dtype`: CATEGORICAL, ORDINAL, NUMERIC, or MIXED
  - `bins`: Binning config for numeric dimensions (strategy, k, edges)
  - `rank_map`: Optional rank mapping for ordinals
  - `missing_token`: Token for missing values (default: `"__MISSING__"`)
- `Schema`: Container for dimension specs with validation and subsetting

#### Builder (`builder.py`)
- **Dimension Ordering**: Critical for MDD size
  - `"fixed"`: User-provided order
  - `"heuristic"`: Entropy + cardinality heuristic (default)
  - `"search"`: Randomized local search within budget
- **Compilation Methods**: Two algorithms for building MDDs
  - `"trie"` (default): Build full trie, then reduce bottom-up
  - `"slice"`: Incremental slice-based compilation (Nicholson-Bridge-Wilson 2006)
- **Construction Process**:
  1. Decide dimension order (via `ordering.py`)
  2. Fit binning models for numeric dimensions (`binning.py`)
  3. Build MDD using selected compilation method:
     - **Trie method**: Build trie by inserting rows as paths, then optionally reduce
     - **Slice method**: Incrementally build reduced MDD using slice signatures
- **Reduction Algorithm** (`_reduce` - only for trie method):
  - Process layers bottom-up
  - Signature: `(layer, terminal_count, sorted_labeled_edges)`
  - Nodes with identical signatures are merged
  - Maintains arc counts and reach counts through aggregation

#### MDD Structure (`mdd.py`)
- **Node**: Contains `layer`, `edges` (label→child_id), `edge_counts`, `reach_count`, `terminal_count`
- **Arc**: Labeled edge with count
- Stores dimension order, bin models, and Laplace smoothing parameter

#### Binning (`binning.py`)
- `BinModel`: Converts numeric values to interval strings like `"[0.0,5.0)"`
- Strategies:
  - `"fixed_width"`: Equal-width bins
  - `"quantile"`: Equal-frequency bins (default)
- Missing values map to `"__MISSING__"`

#### Ordering (`ordering.py`)
- **Heuristic** (`propose_order`): Sort by entropy + 0.05×cardinality (ascending)
- **Search** (`search_order`): Randomized swap search minimizing prefix-distinct-sum
- **Evaluation** (`evaluate_order`): Sum of distinct counts for each prefix

### Query Methods

All implemented in `mdd.py`:

- **`exists(x)`**: Check if exact path exists
- **`match(pattern, limit)`**: DFS pattern matching with wildcards
- **`complete(partial, k, beam)`**: Top-k completions via beam search, ranked by conditional probability (MAP)
- **`nearest(partial, dist_fns, k)`**: k-nearest paths using A* with per-dimension distance functions

#### Conditional Probabilities
- Each node computes: `P(label | prefix) = (count(label) + α) / (total + α*k)`
- Laplace smoothing controlled by `laplace_alpha` (default 0.1)
- Completion score: negative log-probability (lower = more likely)

### Configuration (`config.py`)

- `BuildConfig`:
  - `ordering`: "fixed" | "heuristic" | "search"
  - `compilation_method`: "trie" | "slice" (default: "trie")
  - `enable_reduction`: Enable/disable compression (only for trie method, default: True)
  - `laplace_alpha`: Smoothing for probabilities
  - `default_numeric_bins`: Fallback binning config

- `OrderingConfig`: Budget controls for search (time_budget_s, max_evals, beam_width)
- `QueryConfig`: Runtime query parameters

## Important Patterns

### Typical Workflow
```python
# 1. Define schema
schema = Schema([
    DimensionSpec("cat_col", DimensionType.CATEGORICAL),
    DimensionSpec("ord_col", DimensionType.ORDINAL),
    DimensionSpec("num_col", DimensionType.NUMERIC, bins={"strategy":"quantile", "k":5}),
])

# 2. Build MDD (default: trie method with reduction)
cfg = BuildConfig(ordering="heuristic", compilation_method="trie", enable_reduction=True)
mdd = Builder(schema, cfg).fit(df)

# Or use slice method (automatically reduced)
cfg_slice = BuildConfig(ordering="heuristic", compilation_method="slice")
mdd_slice = Builder(schema, cfg_slice).fit(df)

# 3. Query
results = mdd.complete({"cat_col": "value"}, k=5)
```

### Distance Functions for Nearest
Custom distance functions are passed as `dist_fns` dict:
```python
def ordinal_dist(a, b): return abs(int(a) - int(b))
dist_fns = {"priority": ordinal_dist}
results = mdd.nearest(partial, dist_fns=dist_fns, k=3)
```

### Binning Strategies
Numeric columns must specify binning:
```python
# Quantile binning (recommended)
DimensionSpec("price", DimensionType.NUMERIC, bins={"strategy":"quantile", "k":10})

# Fixed-width binning
DimensionSpec("age", DimensionType.NUMERIC, bins={"strategy":"fixed_width", "k":5})
```

## Key Implementation Details

### Compilation Methods Comparison

**Trie Method** (`compilation_method="trie"`):
- Traditional two-phase approach: build trie → reduce
- Build phase: Inserts each row as a complete path (builder.py:59-88)
- Reduction phase: Bottom-up merging of equivalent nodes (builder.py:90-175)
- Can disable reduction for debugging (`enable_reduction=False`)
- Pros: Simple, well-understood, flexible
- Cons: Higher memory usage during construction

**Slice Method** (`compilation_method="slice"`):
- Incremental compilation based on slice signatures (slice_compile.py)
- For each row, computes slice signature: projection of remaining dimensions
- Reuses nodes when slice signatures match (on-the-fly reduction)
- Implements Nicholson, Bridge, and Wilson (2006), Algorithm 1
- Pros: Memory-efficient, produces reduced MDD directly
- Cons: More computation per row (slice signature calculation)

Both methods produce identical reduced MDDs with same node/arc counts.

### Node Reduction (Trie Method)
- Signature includes terminal_count and all labeled outgoing edges (structural)
- Edge counts and reach counts are NOT in signature—they get aggregated
- Nodes at the same layer with identical signatures are merged
- After reduction, nodes are reordered by layer for stability
- Root node ID is updated through remapping

### Conditional Probability Calculation
- Uses Laplace (add-α) smoothing to avoid zero probabilities
- `_cond_prob(node_id, label)` computes P(label | reaching this node)
- Beam search in `complete()` maintains top-beam candidates by cumulative log-probability

### Query Result Format
`QueryResult` dataclass contains:
- `path`: Dict[str, Any] with all dimension values
- `score`: Float (interpretation depends on query type)
- `details`: Dict with breakdown (e.g., "logprob", "distance")

## Testing Notes

- Tests use small synthetic DataFrames
- `test_basic.py` covers basic build, exists, and complete operations
- When adding tests, verify both reduced and non-reduced modes
- Check that ordering strategies produce valid results (may differ in size)

## File Structure Summary

```
mdd4tables/
├── __init__.py       # Public API exports
├── schema.py         # DimensionType, DimensionSpec, Schema
├── config.py         # BuildConfig, QueryConfig, OrderingConfig
├── builder.py        # Builder class with fit() and _reduce()
├── slice_compile.py  # SliceCompiler for incremental compilation
├── mdd.py           # MDD class with query methods
├── binning.py        # BinModel, fit_binner()
├── ordering.py       # propose_order(), search_order(), evaluate_order()
└── viz.py           # Visualization utilities (optional)
```

## Performance Considerations

- **Dimension ordering** has the largest impact on MDD size
- Use `"heuristic"` ordering as default; `"search"` for critical applications
- **Compilation method**:
  - `"trie"` is faster for small datasets and when reduction is disabled
  - `"slice"` is more memory-efficient for large datasets
  - Both produce identical reduced MDDs
- Numeric binning: fewer bins = smaller MDD but less precision
- Reduction is essential for compression; disable only for debugging (trie method)
- Beam width in `complete()` trades off speed vs completeness (default: 25)
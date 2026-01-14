# MDD4Tables — Requirements (Multi‑Valued Decision Diagrams for Tables)

> Goal: Provide a production-grade Python library that **compresses tabular rows into a Multi‑Valued Decision Diagram (MDD)** and supports **fast retrieval, completion, and probabilistic ranking of paths** under partial information.

---

## 1) Scope and Core Concepts

### 1.1 Data-to-MDD Mapping
- **Input**: one or more tables (e.g., pandas DataFrame, Arrow Table, CSV/Parquet).
- **Row semantics**: **each row is a feasible path** from root to terminal.
- **Dimension semantics**: **each column (dimension) is a layer** in the MDD.
- **Value semantics**: each distinct value (or bucket/interval) is an **arc label** between consecutive layers.
- **Terminal semantics**: terminal nodes represent completion of a row; optionally store **row ids / counts / labels** at terminals.

### 1.2 Decision Traces (First-Class Concept)
- Treat every root→terminal path as a **Decision Trace**: an ordered sequence of decisions (dimension/value selections).
- The library must:
  - Extract and export decision traces (as sequences, JSON, or tabular format).
  - Attach metadata to traces (frequency, conditional probabilities, provenance, labels).
  - Support “trace analytics” (top traces, drift, rare traces, conditional likelihood).

---

## 2) MDD Construction Requirements

### 2.1 Builders & APIs
- Provide a `Builder` API that supports:
  - Building an MDD from a full table.
  - Incremental updates (append rows; optional delete support if feasible).
  - Building from multiple tables (union / concat; configurable keys).
- Provide a `Schema` layer describing each dimension:
  - `categorical`, `ordinal`, `numeric`, and `mixed`.
  - Missing value semantics (explicit token vs skip vs impute).

### 2.2 Canonical Reduction & Compression
- Must implement **node merging** to compress the structure:
  - Equivalent subgraphs are merged (isomorphism based on outgoing labeled arcs and child pointers).
  - Use hashing / canonical signatures per node to detect merges efficiently.
- Must maintain:
  - **Arc counts**: number of rows/traces that traverse each arc.
  - **Node counts**: number of rows/traces that reach each node.
  - Optional per-leaf counts and per-class counts (for classification extension).

### 2.3 Dimension Ordering (Size-Critical)
Because dimension order can dramatically change MDD size, the library must support **ordering strategies**:

#### 2.3.1 Fixed Order
- Accept user-provided order (list of columns).

#### 2.3.2 Heuristic Order (Default)
Provide built-in heuristics to propose a “good” order:
- **Entropy / cardinality heuristic** (e.g., place low-branching or high-merging potential dimensions early/late depending on objective).
- **Mutual information / correlation heuristic** (group dependent dimensions to maximize merging).
- **Prefix-stability heuristic** for trace completion (dimensions that reduce ambiguity earlier).
- Must output:
  - Chosen order, score, and diagnostics (estimated size impact per dimension).

#### 2.3.3 Search-Based Order (Optional but Supported)
- Provide a configurable search to improve ordering:
  - Greedy local search, beam search, or simulated annealing over permutations.
  - Objective: minimize MDD size (nodes+arcs) and/or maximize query performance.
- Must include budget controls:
  - max evaluations, time budget, beam width.
- Must return:
  - Best order found + summary statistics (size, build time, eval count).

---

## 3) Data Type Handling & Binning

### 3.1 Categorical
- Exact match arcs.
- Optional normalization (case folding, trimming) via preprocessing hooks.

### 3.2 Ordinal (Ranked / Priority-like)
- Preserve ordering semantics.
- Provide distance functions:
  - absolute rank difference, normalized rank distance, custom mapping.

### 3.3 Numeric
- Support representing numeric dimensions as:
  - **exact values** (only when cardinality is manageable), or
  - **interval arcs** via binning (recommended).
- Provide binning strategies:
  - fixed-width, quantile, k-means, Bayesian blocks (optional), user-defined cutpoints.
- Must support per-dimension configuration and global defaults.

### 3.4 Missing & Partial Values
- Explicit missing token as an arc, OR missing-as-wildcard during query, configurable per dimension.

---

## 4) Query Requirements (Phase 1)

### 4.1 Exact Queries
- `exists(x)`: does a fully specified vector/row exist as a trace?
- `count(x)`: how many rows match exactly (including duplicates)?
- `get_leaf_payload(x)`: retrieve metadata stored at terminal (row ids, labels, etc.).

### 4.2 Pattern / Wildcard Queries
- `match(pattern)`: return all traces matching a partial pattern with wildcards.
- Must support:
  - fixed values on some dimensions,
  - wildcards on others,
  - range predicates on numeric/ordinal (e.g., `priority <= 3`, `price in [a,b]`).

### 4.3 Completion Queries (Partial Input → Full Path)
Given partial input, return one or more completed paths:
- `complete(partial, k)`: return top-k completions.
- Must support multiple scoring policies (see 4.5).

### 4.4 Nearest / Shortest-Path Queries (Partial Input)
- `nearest(partial, k)`: return k closest traces under a **distance model**.
- Distance must be configurable per dimension type:
  - categorical: match=0, mismatch=1 (or user-defined costs)
  - ordinal: rank distance
  - numeric: absolute / normalized / z-score distance, or distance between bins
- Algorithmic requirement:
  - Provide an A* or Dijkstra-style search over the layered MDD with admissible heuristics where possible.

### 4.5 Probabilistic Ranking (Conditional Probability)
Queries must allow **conditional-probability–aware scoring** rather than independent frequencies.

- Maintain for each node:
  - outgoing arc counts → conditional probabilities:
    -  P(value | prefix) = count(prefix + value) / count(prefix)
- Provide ranking policies:
  - **MAP completion**: maximize product of conditional probabilities along the completion
  - **Log-score**: maximize sum of log conditionals (numerically stable)
  - **Hybrid distance + probability**: minimize `distance(partial, trace) - λ * logprob(trace | partial)`
- Must expose:
  - smoothing options (Laplace/add-α) for unseen transitions
  - backoff strategies (e.g., prefix shortening) when counts are sparse

### 4.6 Query Outputs
All query methods should return:
- the trace/path (values per dimension),
- score breakdown (distance components + probability components),
- provenance (counts, node/arc ids),
- optional explanation payload.

---

## 5) Explainability & Traceability

### 5.1 Explain “Why this path?”
For completion/nearest queries:
- Provide explanation object including:
  - matched vs imputed dimensions,
  - per-dimension distance contributions,
  - conditional-probability contributions (top arcs at each step),
  - alternative candidates and their deltas.

### 5.2 Export & Audit
- Export traces and the MDD structure:
  - JSON (nodes/arcs), GraphML/DOT, Parquet-friendly tabular exports.
- Deterministic builds:
  - same data + same config → same diagram and identifiers (optional stable hashing).

---

## 6) Visualization Requirements

### 6.1 Graph Rendering
- Provide:
  - static rendering (Matplotlib/Graphviz)
  - interactive rendering (Plotly or browser-based via HTML)
- Must support:
  - layer-by-layer layout,
  - arc labels (values/bins),
  - thickness/opacity proportional to counts or probabilities.

### 6.2 Visual Diagnostics
- Show:
  - node/arc counts heatmaps per layer,
  - most common traces,
  - rare branches,
  - “what changed” between two diagrams (diff view, optional).

---

## 7) Performance & Scalability

### 7.1 Complexity Targets
- Build time should scale near-linearly in number of rows for typical data, with controlled overhead from merging.
- Memory control:
  - compact node/arc storage (arrays, integer ids),
  - optional disk-backed / mmap persistence (stretch goal).

### 7.2 Large-Data Support
- Batch ingestion (chunked DataFrame/Arrow batches).
- Optional parallelism:
  - parallel signature computation / merging (where safe),
  - parallel evaluation for dimension-order search.

### 7.3 Caching & Indexing
- Cache node signatures.
- Optional auxiliary indexes for fast pattern queries (e.g., per-layer value→arc index).

---

## 8) Persistence & Interoperability

- Save/load diagrams:
  - binary (fast), plus JSON for portability.
- Interoperate with:
  - pandas, pyarrow, numpy
  - scikit-learn style transformers (Phase 2)
- Version metadata embedded in saved artifacts.

---

## 9) Phase 2: ML-Model Extension (Optional Roadmap)

### 9.1 Automatic Binning / Feature Pipeline
- Provide a `Binner`/`Discretizer`:
  - learns bins from training data per numeric dimension
  - stores bin edges and applies them consistently to new data.

### 9.2 MDD as a Classifier / Predictor
- Training:
  - build MDD from labeled data; store class counts at terminals or along nodes.
- Inference:
  - for an input vector, traverse via exact/binned arcs; if partial/missing, use nearest/complete with conditional probability.
- Output:
  - predicted class, top-k classes, calibrated probabilities (if feasible).
- Provide sklearn-compatible API:
  - `fit`, `predict`, `predict_proba`, `transform`.

---

## 10) Developer Experience

- Clean, typed Python API (`dataclasses`, `typing`).
- Clear config objects:
  - schema, ordering, binning, smoothing, distance metrics, query policies.
- Comprehensive tests:
  - correctness of reduction, determinism, probability math, nearest search, ordering heuristics.
- Documentation:
  - tutorials for “table → MDD”, “partial completion”, “nearest traces”, “visualization”.
- Benchmarks:
  - build scaling, query latency, ordering impact.

---

## 11) Non-Goals (Explicit)
- General-purpose constraint solving is **out of scope** for Phase 1.
- Continuous (unbinned) numeric decision diagrams are **out of scope** unless explicitly enabled for low-cardinality numeric dimensions.

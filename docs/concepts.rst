Core Concepts
=============

This page explains the fundamental concepts behind mdd4tables.

What is a Decision Diagram?
---------------------------

A **Decision Diagram** is a directed acyclic graph (DAG) that represents a function or dataset:

- **Nodes** represent decision points (one per dimension/variable)
- **Arcs** represent choices (values that a dimension can take)
- **Paths** from root to terminal represent complete records

Binary Decision Diagrams (BDDs)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A **BDD** is a decision diagram where each variable is binary (0 or 1). BDDs are widely used in:

- Hardware verification
- Boolean function optimization
- Symbolic model checking

Multi-Valued Decision Diagrams (MDDs)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

An **MDD** generalizes BDDs to support **multiple values** per dimension:

- Categorical: "Red", "Green", "Blue"
- Ordinal: 1, 2, 3, 4, 5
- Numeric (binned): "[0,10)", "[10,20)", "[20,30)"

This makes MDDs perfect for representing **tabular data**.

How mdd4tables Works
--------------------

1. **Input**: A pandas DataFrame where each row is a record
2. **Schema**: Define dimension types (categorical, ordinal, numeric)
3. **Build**: Convert rows into paths in a trie, then optionally reduce
4. **Query**: Use the compressed MDD for fast lookups

Building Process
^^^^^^^^^^^^^^^^

.. code-block:: text

   DataFrame          Trie (uncompressed)       MDD (compressed)
   ┌───────────────┐   ┌───┐                    ┌───┐
   │ A │ X │ 1 │   │   │ A │──X──1──●           │ A │──X──┐
   │ A │ X │ 2 │   │   │   │──X──2──●           │   │     ├──1──●
   │ A │ Y │ 1 │   │   │   │──Y──1──●           │   │──Y──┤
   │ B │ X │ 1 │   │   │ B │──X──1──●           │ B │──X──┘
   └───────────────┘   └───┘                    └───┘

   4 rows              7 nodes, 8 arcs          5 nodes, 6 arcs

The **reduction** step merges equivalent subtrees (nodes with identical outgoing edges).

Dimension Types
---------------

CATEGORICAL
^^^^^^^^^^^

Unordered discrete values with no inherent ranking.

.. code-block:: python

   DimensionSpec("country", DimensionType.CATEGORICAL)
   # Values: "USA", "UK", "Germany", "France"

ORDINAL
^^^^^^^

Discrete values with a natural ordering.

.. code-block:: python

   DimensionSpec("priority", DimensionType.ORDINAL)
   # Values: 1, 2, 3, 4, 5 (low to high)

NUMERIC
^^^^^^^

Continuous values that are automatically binned.

.. code-block:: python

   DimensionSpec("price", DimensionType.NUMERIC, bins={"strategy": "quantile", "k": 5})
   # Values: "[0,100)", "[100,250)", "[250,500)", ...

Binning strategies:

- **quantile**: Equal-frequency bins (default)
- **fixed_width**: Equal-width bins

Dimension Ordering
------------------

The order of dimensions significantly affects MDD size. Consider:

.. code-block:: text

   Order A→B→C: 10 nodes      Order C→B→A: 25 nodes
   ┌───┐                      ┌───┐
   │ A │──1──┐                │ C │──X──┐──┐──┐
   │   │──2──┼──B──C──●       │   │──Y──┤  │  │
   └───┘     │                └───┘     B  B  ...
             └──B──C──●

mdd4tables provides three ordering strategies:

**fixed**
   Use the order specified in the schema.

**heuristic** (default)
   Greedy algorithm based on entropy and cardinality. Fast and usually effective.

**search**
   Randomized local search with time budget. Better results but slower.

.. code-block:: python

   from mdd4tables import BuildConfig, OrderingConfig

   # Heuristic (fast, good)
   cfg = BuildConfig(ordering="heuristic")

   # Search (slower, better)
   cfg = BuildConfig(
       ordering="search",
       ordering_config=OrderingConfig(
           time_budget_s=5.0,
           max_evals=200,
           objective="nodes_plus_arcs"
       )
   )

Compilation Methods
-------------------

trie (default)
^^^^^^^^^^^^^^

1. Build an uncompressed trie (one path per row)
2. Bottom-up reduction to merge equivalent nodes

Pros: Simple, well-understood
Cons: Peak memory = full trie size

slice
^^^^^

Incremental bottom-up compilation (Nicholson-Bridge-Wilson 2006).

Pros: Lower peak memory, builds reduced MDD directly
Cons: Slightly more complex

.. code-block:: python

   # Trie method (default)
   cfg = BuildConfig(compilation_method="trie", enable_reduction=True)

   # Slice method
   cfg = BuildConfig(compilation_method="slice")

Probability Model
-----------------

Every arc in the MDD tracks how many times it was traversed during construction:

.. code-block:: text

   Node 0 (region)
     ├── "EU" (count: 150) ──→ Node 1
     ├── "US" (count: 200) ──→ Node 2
     └── "APAC" (count: 50) ──→ Node 3

This enables **conditional probability** queries:

.. math::

   P(\\text{product}=A | \\text{region}=EU) = \\frac{\\text{count}(EU \\rightarrow A) + \\alpha}{\\text{total}(EU) + \\alpha \\cdot k}

Where:

- α = Laplace smoothing parameter (default 0.1)
- k = number of distinct values at this node

Query Operations
----------------

exists(x)
^^^^^^^^^

Check if an exact path exists. O(d) where d = number of dimensions.

.. code-block:: python

   mdd.exists({"region": "EU", "product": "A", "priority": 1})  # True/False

count(pattern)
^^^^^^^^^^^^^^

Count matching paths without enumeration. Uses memoized DFS.

.. code-block:: python

   mdd.count({"region": "EU"})  # Count all EU paths
   mdd.count()  # Total paths

match(pattern)
^^^^^^^^^^^^^^

Find all paths matching a pattern (wildcards for missing dimensions).

.. code-block:: python

   paths = mdd.match({"region": "EU"}, limit=100)

complete(partial, k)
^^^^^^^^^^^^^^^^^^^^

Find top-k completions ranked by conditional probability using beam search.

.. code-block:: python

   results = mdd.complete({"region": "EU", "product": "A"}, k=5)
   for r in results:
       print(r.path, r.score)

nearest(partial, dist_fns, k)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A* search with custom distance functions per dimension.

.. code-block:: python

   dist_fns = {
       "price": lambda want, have: abs(want - have),
       "category": lambda want, have: 0 if want == have else 1,
   }
   results = mdd.nearest({"price": 100}, dist_fns, k=5)

Compression Analysis
--------------------

MDD compression depends on data redundancy:

.. code-block:: python

   mdd = Builder(schema).fit(df)
   size = mdd.size()

   print(f"Nodes: {size['nodes']}")
   print(f"Arcs: {size['arcs']}")
   print(f"Compression ratio: {len(df) / size['nodes']:.1f}x")

Typical compression ratios:

- High redundancy (e.g., config tables): 50-100x
- Medium redundancy (e.g., logs): 5-20x
- Low redundancy (e.g., unique IDs): 1-2x


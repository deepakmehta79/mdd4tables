Quickstart
==========

Installation
------------

Install from source (editable mode):

.. code-block:: bash

   pip install -e .

Or with visualization support:

.. code-block:: bash

   pip install -e ".[viz]"

Basic Usage
-----------

Here's a minimal example to get started:

.. code-block:: python

   import pandas as pd
   from mdd4tables import Schema, DimensionSpec, DimensionType, BuildConfig, Builder

   # Create sample data
   df = pd.DataFrame({
       "region": ["EU", "EU", "US", "US"],
       "priority": [1, 2, 1, 3],
       "qty": [10.1, 9.7, 5.0, 4.9],
   })

   # Define schema
   schema = Schema([
       DimensionSpec("region", DimensionType.CATEGORICAL),
       DimensionSpec("priority", DimensionType.ORDINAL),
       DimensionSpec("qty", DimensionType.NUMERIC, bins={"strategy": "quantile", "k": 3}),
   ])

   # Build MDD
   cfg = BuildConfig(ordering="heuristic")
   mdd = Builder(schema, cfg).fit(df)

   # Query: check if exact path exists
   print(mdd.exists({"region": "EU", "priority": 1, "qty": 10.1}))

   # Find top-k completions with conditional probability ranking
   results = mdd.complete({"region": "EU"}, k=3)
   for r in results:
       print(r.path, r.score, r.details)

Key Concepts
------------

Dimension Types
^^^^^^^^^^^^^^^

- **CATEGORICAL**: Unordered discrete values (e.g., country, color)
- **ORDINAL**: Ordered discrete values (e.g., priority levels)
- **NUMERIC**: Continuous values that get binned (e.g., price, quantity)

Build Configuration
^^^^^^^^^^^^^^^^^^^

- **ordering**: How to order dimensions ("fixed", "heuristic", "search")
- **compilation_method**: "trie" (build then reduce) or "slice" (incremental)
- **enable_reduction**: Whether to merge equivalent nodes
- **laplace_alpha**: Smoothing parameter for probability calculations

Querying the MDD
^^^^^^^^^^^^^^^^

- ``exists(x)``: Check if an exact path exists
- ``count(pattern)``: Count matching paths without enumeration
- ``match(pattern)``: Find all paths matching a pattern
- ``complete(partial, k)``: Top-k completions by conditional probability


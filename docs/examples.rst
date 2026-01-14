Examples
========

This section contains practical examples of using mdd4tables.

Basic MDD Construction
----------------------

.. code-block:: python

   import pandas as pd
   from mdd4tables import Schema, DimensionSpec, DimensionType, BuildConfig, Builder

   # Sample data
   df = pd.DataFrame({
       "region": ["EU", "EU", "US", "US", "APAC"],
       "product": ["A", "B", "A", "C", "A"],
       "priority": [1, 2, 1, 3, 2],
   })

   # Define schema with dimension types
   schema = Schema([
       DimensionSpec("region", DimensionType.CATEGORICAL),
       DimensionSpec("product", DimensionType.CATEGORICAL),
       DimensionSpec("priority", DimensionType.ORDINAL),
   ])

   # Build with heuristic ordering
   mdd = Builder(schema, BuildConfig(ordering="heuristic")).fit(df)

   print(mdd)  # MDD(dims=['region', 'product', 'priority'], nodes=..., arcs=...)
   print(mdd.size())  # {'nodes': ..., 'arcs': ..., 'layers': 3}

Numeric Binning
---------------

.. code-block:: python

   import pandas as pd
   from mdd4tables import Schema, DimensionSpec, DimensionType, BuildConfig, Builder

   df = pd.DataFrame({
       "category": ["A", "A", "B", "B", "C"],
       "amount": [100.5, 250.3, 50.0, 175.8, 300.0],
       "score": [0.1, 0.5, 0.3, 0.8, 0.9],
   })

   schema = Schema([
       DimensionSpec("category", DimensionType.CATEGORICAL),
       DimensionSpec("amount", DimensionType.NUMERIC, bins={"strategy": "quantile", "k": 5}),
       DimensionSpec("score", DimensionType.NUMERIC, bins={"strategy": "uniform", "k": 3}),
   ])

   mdd = Builder(schema).fit(df)

Querying Patterns
-----------------

.. code-block:: python

   # Check existence
   exists = mdd.exists({"region": "EU", "product": "A", "priority": 1})

   # Count matching paths
   count = mdd.count({"region": "EU"})  # All EU paths
   total = mdd.count()  # Total paths

   # Find matching paths
   matches = mdd.match({"region": "EU"}, limit=10)
   for path in matches:
       print(path)

Probability-Ranked Completion
-----------------------------

.. code-block:: python

   # Given partial input, find most likely completions
   results = mdd.complete({"region": "EU"}, k=5)

   for r in results:
       print(f"Path: {r.path}")
       print(f"Log-probability: {r.score:.4f}")
       print(f"Details: {r.details}")
       print()

Custom Dimension Ordering
-------------------------

.. code-block:: python

   from mdd4tables import OrderingConfig

   # Use search-based ordering
   cfg = BuildConfig(
       ordering="search",
       ordering_config=OrderingConfig(
           time_budget_s=5.0,
           max_evals=200,
           objective="nodes_plus_arcs"
       )
   )

   mdd = Builder(schema, cfg).fit(df)

   # Or specify exact order
   mdd = Builder(schema).fit(df, order=["priority", "region", "product"])

Slice-Based Compilation
-----------------------

.. code-block:: python

   # Use slice-based compilation (incremental, memory efficient)
   cfg = BuildConfig(compilation_method="slice")
   mdd = Builder(schema, cfg).fit(df)

Binary Decision Diagram (BDD)
-----------------------------

For Boolean functions, use binary dimensions:

.. code-block:: python

   import pandas as pd
   from mdd4tables import Schema, DimensionSpec, DimensionType, BuildConfig, Builder

   # Truth table for majority function: f(x,y,z) = 1 if at least 2 inputs are 1
   df = pd.DataFrame({
       "x": [0, 0, 0, 0, 1, 1, 1, 1],
       "y": [0, 0, 1, 1, 0, 0, 1, 1],
       "z": [0, 1, 0, 1, 0, 1, 0, 1],
       "f": [0, 0, 0, 1, 0, 1, 1, 1],
   })

   schema = Schema([
       DimensionSpec("x", DimensionType.CATEGORICAL),
       DimensionSpec("y", DimensionType.CATEGORICAL),
       DimensionSpec("z", DimensionType.CATEGORICAL),
       DimensionSpec("f", DimensionType.CATEGORICAL),
   ])

   bdd = Builder(schema, BuildConfig(enable_reduction=True)).fit(df)


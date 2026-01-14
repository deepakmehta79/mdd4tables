Examples
========

This page contains practical examples for common use cases.

Example 1: Product Configuration
--------------------------------

Compress and query a product configuration database:

.. code-block:: python

   import pandas as pd
   from mdd4tables import Schema, DimensionSpec, DimensionType, BuildConfig, Builder

   # Product configurations (many combinations, lots of redundancy)
   df = pd.DataFrame({
       "brand": ["Apple", "Apple", "Apple", "Samsung", "Samsung", "Google"] * 100,
       "model": ["Pro", "Pro", "Air", "Ultra", "Plus", "Pixel"] * 100,
       "storage": ["128GB", "256GB", "256GB", "256GB", "128GB", "128GB"] * 100,
       "color": ["Black", "Silver", "Gold", "Black", "White", "Black"] * 100,
       "price_tier": ["Premium", "Premium", "Mid", "Premium", "Mid", "Mid"] * 100,
   })

   print(f"Original rows: {len(df)}")

   schema = Schema([
       DimensionSpec("brand", DimensionType.CATEGORICAL),
       DimensionSpec("model", DimensionType.CATEGORICAL),
       DimensionSpec("storage", DimensionType.ORDINAL),
       DimensionSpec("color", DimensionType.CATEGORICAL),
       DimensionSpec("price_tier", DimensionType.ORDINAL),
   ])

   mdd = Builder(schema, BuildConfig(ordering="heuristic")).fit(df)

   print(f"MDD nodes: {mdd.size()['nodes']}")
   print(f"Compression: {len(df) / mdd.size()['nodes']:.1f}x")

   # Query: What configurations exist for Apple?
   apple_configs = mdd.match({"brand": "Apple"}, limit=50)
   print(f"\nApple configurations: {len(apple_configs)}")

Example 2: Boolean Function (BDD)
---------------------------------

Build a Binary Decision Diagram for a boolean function:

.. code-block:: python

   import pandas as pd
   from mdd4tables import Schema, DimensionSpec, DimensionType, BuildConfig, Builder

   # Truth table for majority function: f(x,y,z) = 1 if at least 2 inputs are 1
   rows = []
   for x in [0, 1]:
       for y in [0, 1]:
           for z in [0, 1]:
               f = 1 if (x + y + z) >= 2 else 0
               rows.append({"x": x, "y": y, "z": z, "f": f})

   df = pd.DataFrame(rows)
   print("Majority function truth table:")
   print(df)

   schema = Schema([
       DimensionSpec("x", DimensionType.ORDINAL),
       DimensionSpec("y", DimensionType.ORDINAL),
       DimensionSpec("z", DimensionType.ORDINAL),
       DimensionSpec("f", DimensionType.ORDINAL),
   ])

   # Use fixed ordering for canonical BDD
   mdd = Builder(schema, BuildConfig(ordering="fixed")).fit(
       df, order=["x", "y", "z", "f"]
   )

   print(f"\nBDD size: {mdd.size()}")

   # Verify: check some inputs
   print(f"\nf(1,1,0) = 1? {mdd.exists({'x': 1, 'y': 1, 'z': 0, 'f': 1})}")
   print(f"f(0,0,1) = 0? {mdd.exists({'x': 0, 'y': 0, 'z': 1, 'f': 0})}")

Example 3: Log Analysis with Numeric Binning
--------------------------------------------

Analyze server logs with automatic binning for response times:

.. code-block:: python

   import pandas as pd
   import numpy as np
   from mdd4tables import Schema, DimensionSpec, DimensionType, BuildConfig, Builder

   # Simulated server logs
   np.random.seed(42)
   n = 10000

   df = pd.DataFrame({
       "endpoint": np.random.choice(["/api/users", "/api/orders", "/api/products"], n),
       "method": np.random.choice(["GET", "POST", "PUT", "DELETE"], n, p=[0.6, 0.2, 0.15, 0.05]),
       "status": np.random.choice([200, 201, 400, 404, 500], n, p=[0.7, 0.1, 0.1, 0.05, 0.05]),
       "response_time_ms": np.random.exponential(100, n),  # Exponential distribution
       "user_type": np.random.choice(["free", "premium", "enterprise"], n, p=[0.6, 0.3, 0.1]),
   })

   print(f"Log entries: {len(df)}")
   print(f"Response time range: {df['response_time_ms'].min():.1f} - {df['response_time_ms'].max():.1f} ms")

   schema = Schema([
       DimensionSpec("endpoint", DimensionType.CATEGORICAL),
       DimensionSpec("method", DimensionType.CATEGORICAL),
       DimensionSpec("status", DimensionType.ORDINAL),
       DimensionSpec("response_time_ms", DimensionType.NUMERIC, bins={
           "strategy": "quantile",
           "k": 10  # 10 percentile bins
       }),
       DimensionSpec("user_type", DimensionType.ORDINAL),
   ])

   mdd = Builder(schema, BuildConfig(ordering="heuristic")).fit(df)

   print(f"\nMDD: {mdd.size()}")
   print(f"Compression: {len(df) / mdd.size()['nodes']:.1f}x")

   # Analysis queries
   print(f"\nError count (status >= 400): {mdd.count({'status': 400}) + mdd.count({'status': 404}) + mdd.count({'status': 500})}")

   # Most likely patterns for errors
   print("\nMost likely patterns for 500 errors:")
   results = mdd.complete({"status": 500}, k=3)
   for r in results:
       print(f"  {r.path}")

Example 4: Shipping Lane Configuration
--------------------------------------

Compress shipping lane configurations:

.. code-block:: python

   import pandas as pd
   from mdd4tables import Schema, DimensionSpec, DimensionType, BuildConfig, Builder

   # Shipping lane data
   df = pd.DataFrame({
       "origin_region": ["APAC", "APAC", "EMEA", "EMEA", "AMER", "AMER"] * 50,
       "dest_region": ["EMEA", "AMER", "AMER", "APAC", "EMEA", "APAC"] * 50,
       "mode": ["Air", "Ocean", "Air", "Ocean", "Air", "Ocean"] * 50,
       "carrier": ["FedEx", "Maersk", "DHL", "MSC", "UPS", "CMA"] * 50,
       "service_level": ["Express", "Standard", "Express", "Economy", "Express", "Standard"] * 50,
   })

   schema = Schema([
       DimensionSpec("origin_region", DimensionType.CATEGORICAL),
       DimensionSpec("dest_region", DimensionType.CATEGORICAL),
       DimensionSpec("mode", DimensionType.CATEGORICAL),
       DimensionSpec("carrier", DimensionType.CATEGORICAL),
       DimensionSpec("service_level", DimensionType.ORDINAL),
   ])

   # Compare trie vs slice compilation
   for method in ["trie", "slice"]:
       cfg = BuildConfig(ordering="heuristic", compilation_method=method)
       mdd = Builder(schema, cfg).fit(df)
       print(f"{method.upper()}: {mdd.size()}")

Example 5: Dimension Ordering Comparison
----------------------------------------

Compare different ordering strategies:

.. code-block:: python

   import pandas as pd
   from mdd4tables import (
       Schema, DimensionSpec, DimensionType,
       BuildConfig, OrderingConfig, Builder,
       propose_order, evaluate_order
   )

   # Data with varying cardinalities
   df = pd.DataFrame({
       "low_card": ["A", "B"] * 500,                    # 2 values
       "med_card": ["X", "Y", "Z", "W"] * 250,          # 4 values
       "high_card": [f"val_{i % 50}" for i in range(1000)],  # 50 values
   })

   schema = Schema([
       DimensionSpec("low_card", DimensionType.CATEGORICAL),
       DimensionSpec("med_card", DimensionType.CATEGORICAL),
       DimensionSpec("high_card", DimensionType.CATEGORICAL),
   ])

   # Fixed ordering (as defined)
   cfg_fixed = BuildConfig(ordering="fixed")
   mdd_fixed = Builder(schema, cfg_fixed).fit(df)
   print(f"Fixed order {mdd_fixed.dim_names}: {mdd_fixed.size()['nodes']} nodes")

   # Heuristic ordering
   cfg_heur = BuildConfig(ordering="heuristic")
   mdd_heur = Builder(schema, cfg_heur).fit(df)
   print(f"Heuristic order {mdd_heur.dim_names}: {mdd_heur.size()['nodes']} nodes")

   # Search-based ordering
   cfg_search = BuildConfig(
       ordering="search",
       ordering_config=OrderingConfig(time_budget_s=2.0, max_evals=50)
   )
   mdd_search = Builder(schema, cfg_search).fit(df)
   print(f"Search order {mdd_search.dim_names}: {mdd_search.size()['nodes']} nodes")

Example 6: Nearest Neighbor Search
----------------------------------

Find similar records using custom distance functions:

.. code-block:: python

   import pandas as pd
   from mdd4tables import Schema, DimensionSpec, DimensionType, BuildConfig, Builder

   df = pd.DataFrame({
       "category": ["Electronics", "Electronics", "Clothing", "Clothing", "Food"],
       "price": [100, 500, 50, 200, 10],
       "rating": [4.5, 4.8, 3.9, 4.2, 4.0],
   })

   schema = Schema([
       DimensionSpec("category", DimensionType.CATEGORICAL),
       DimensionSpec("price", DimensionType.NUMERIC, bins={"strategy": "quantile", "k": 3}),
       DimensionSpec("rating", DimensionType.NUMERIC, bins={"strategy": "quantile", "k": 3}),
   ])

   mdd = Builder(schema).fit(df)

   # Define distance functions
   dist_fns = {
       "category": lambda want, have: 0 if want == have else 1,
       "price": lambda want, have: 0,  # Ignore price in distance
       "rating": lambda want, have: 0,  # Ignore rating in distance
   }

   # Find nearest to Electronics
   results = mdd.nearest({"category": "Electronics"}, dist_fns, k=5)
   print("Products similar to Electronics:")
   for r in results:
       print(f"  {r.path} (distance: {-r.score:.2f})")

Example 7: Missing Value Handling
---------------------------------

Handle missing values with custom tokens:

.. code-block:: python

   import pandas as pd
   import numpy as np
   from mdd4tables import Schema, DimensionSpec, DimensionType, BuildConfig, Builder

   df = pd.DataFrame({
       "name": ["Alice", "Bob", None, "Diana"],
       "age": [25, np.nan, 35, 40],
       "city": ["NYC", "LA", "NYC", None],
   })

   print("Data with missing values:")
   print(df)

   schema = Schema([
       DimensionSpec("name", DimensionType.CATEGORICAL, missing_token="UNKNOWN_NAME"),
       DimensionSpec("age", DimensionType.NUMERIC,
                    bins={"strategy": "quantile", "k": 2},
                    missing_token="UNKNOWN_AGE"),
       DimensionSpec("city", DimensionType.CATEGORICAL, missing_token="UNKNOWN_CITY"),
   ])

   mdd = Builder(schema).fit(df)

   # Missing values are represented by the token
   print(f"\nMDD paths:")
   for path in mdd.match({}, limit=10):
       print(f"  {path}")

Example 8: Large-Scale Compression
----------------------------------

Demonstrate compression on larger datasets:

.. code-block:: python

   import pandas as pd
   import numpy as np
   from mdd4tables import Schema, DimensionSpec, DimensionType, BuildConfig, Builder

   # Generate synthetic data with patterns
   np.random.seed(42)
   n = 100000

   # Data with intentional patterns (good for compression)
   df = pd.DataFrame({
       "dim1": np.random.choice(["A", "B", "C"], n, p=[0.5, 0.3, 0.2]),
       "dim2": np.random.choice(["X", "Y"], n),
       "dim3": np.random.choice(["P", "Q", "R", "S"], n),
       "dim4": np.random.choice(list(range(10)), n),
       "dim5": np.random.choice(["foo", "bar", "baz"], n),
   })

   schema = Schema([
       DimensionSpec(f"dim{i}", DimensionType.CATEGORICAL)
       for i in range(1, 6)
   ])

   import time
   start = time.time()
   mdd = Builder(schema, BuildConfig(ordering="heuristic")).fit(df)
   elapsed = time.time() - start

   print(f"Rows: {len(df):,}")
   print(f"MDD nodes: {mdd.size()['nodes']:,}")
   print(f"MDD arcs: {mdd.size()['arcs']:,}")
   print(f"Compression ratio: {len(df) / mdd.size()['nodes']:.1f}x")
   print(f"Build time: {elapsed:.2f}s")


Quickstart Guide
================

This guide will get you up and running with mdd4tables in 5 minutes.

Installation
------------

**Basic installation:**

.. code-block:: bash

   pip install mdd4tables

**With visualization support:**

.. code-block:: bash

   pip install mdd4tables[viz]

**Development installation:**

.. code-block:: bash

   git clone https://github.com/mdd4tables/mdd4tables.git
   cd mdd4tables
   pip install -e ".[all]"

Step 1: Prepare Your Data
-------------------------

mdd4tables works with pandas DataFrames. Each row becomes a path in the MDD.

.. code-block:: python

   import pandas as pd

   # Example: Product configuration data
   df = pd.DataFrame({
       "region": ["EU", "EU", "EU", "US", "US", "APAC"],
       "product": ["Widget", "Widget", "Gadget", "Widget", "Gadget", "Widget"],
       "tier": ["Gold", "Silver", "Gold", "Gold", "Silver", "Bronze"],
       "price": [99.99, 79.99, 149.99, 89.99, 119.99, 69.99],
   })

   print(df)
   #   region product    tier   price
   # 0     EU  Widget    Gold   99.99
   # 1     EU  Widget  Silver   79.99
   # 2     EU  Gadget    Gold  149.99
   # 3     US  Widget    Gold   89.99
   # 4     US  Gadget  Silver  119.99
   # 5   APAC  Widget  Bronze   69.99

Step 2: Define the Schema
-------------------------

A schema tells mdd4tables how to interpret each column:

.. code-block:: python

   from mdd4tables import Schema, DimensionSpec, DimensionType

   schema = Schema([
       # Categorical: unordered discrete values
       DimensionSpec("region", DimensionType.CATEGORICAL),
       DimensionSpec("product", DimensionType.CATEGORICAL),

       # Ordinal: ordered discrete values
       DimensionSpec("tier", DimensionType.ORDINAL),

       # Numeric: continuous values (will be binned)
       DimensionSpec("price", DimensionType.NUMERIC, bins={
           "strategy": "quantile",  # or "fixed_width"
           "k": 3  # number of bins
       }),
   ])

Step 3: Build the MDD
---------------------

.. code-block:: python

   from mdd4tables import BuildConfig, Builder

   # Configure the build
   cfg = BuildConfig(
       ordering="heuristic",      # Auto-optimize dimension order
       compilation_method="trie", # "trie" or "slice"
       enable_reduction=True,     # Merge equivalent nodes
       laplace_alpha=0.1,         # Smoothing for probabilities
   )

   # Build!
   mdd = Builder(schema, cfg).fit(df)

   # Check the result
   print(mdd)
   # MDD(dims=['tier', 'product', 'region', 'price'], nodes=12, arcs=15)

   print(mdd.size())
   # {'nodes': 12, 'arcs': 15, 'layers': 4}

   print(f"Dimension order: {mdd.dim_names}")
   # Dimension order: ['tier', 'product', 'region', 'price']

Step 4: Query the MDD
---------------------

**Check if a path exists:**

.. code-block:: python

   # Exact match
   exists = mdd.exists({
       "region": "EU",
       "product": "Widget",
       "tier": "Gold",
       "price": 99.99  # Will be binned automatically
   })
   print(f"Path exists: {exists}")  # True

**Count matching paths:**

.. code-block:: python

   # Count all paths with region=EU
   count = mdd.count({"region": "EU"})
   print(f"EU paths: {count}")  # 3

   # Count all paths
   total = mdd.count()
   print(f"Total paths: {total}")  # 6

**Find matching paths:**

.. code-block:: python

   # Find all paths matching a pattern
   matches = mdd.match({"region": "EU"}, limit=10)
   for path in matches:
       print(path)
   # {'tier': 'Gold', 'product': 'Widget', 'region': 'EU', 'price': '[89.99,99.99]'}
   # {'tier': 'Silver', 'product': 'Widget', 'region': 'EU', 'price': '[69.99,79.99)'}
   # ...

**Find top-k completions by probability:**

.. code-block:: python

   # Given partial input, find most likely completions
   results = mdd.complete({"region": "EU"}, k=3)

   for r in results:
       print(f"Path: {r.path}")
       print(f"Log-probability: {r.score:.3f}")
       print()

Step 5: Visualize (Optional)
----------------------------

.. code-block:: python

   # Simple matplotlib visualization
   from mdd4tables.viz import draw
   draw(mdd)

   # Advanced interactive visualization
   from mdd4tables.viz_advanced import visualize_mdd

   # Hierarchical layout (static)
   visualize_mdd(mdd, method="hierarchical", save_path="mdd.png")

   # Interactive PyVis (opens in browser)
   visualize_mdd(mdd, method="pyvis", save_path="mdd.html")

Complete Example
----------------

Here's everything together:

.. code-block:: python

   import pandas as pd
   from mdd4tables import (
       Schema, DimensionSpec, DimensionType,
       BuildConfig, Builder
   )

   # 1. Data
   df = pd.DataFrame({
       "region": ["EU", "EU", "EU", "US", "US", "APAC"],
       "product": ["Widget", "Widget", "Gadget", "Widget", "Gadget", "Widget"],
       "tier": ["Gold", "Silver", "Gold", "Gold", "Silver", "Bronze"],
       "price": [99.99, 79.99, 149.99, 89.99, 119.99, 69.99],
   })

   # 2. Schema
   schema = Schema([
       DimensionSpec("region", DimensionType.CATEGORICAL),
       DimensionSpec("product", DimensionType.CATEGORICAL),
       DimensionSpec("tier", DimensionType.ORDINAL),
       DimensionSpec("price", DimensionType.NUMERIC, bins={"strategy": "quantile", "k": 3}),
   ])

   # 3. Build
   mdd = Builder(schema, BuildConfig(ordering="heuristic")).fit(df)
   print(f"Built MDD: {mdd.size()}")

   # 4. Query
   print(f"\nTotal records: {mdd.count()}")
   print(f"EU records: {mdd.count({'region': 'EU'})}")

   print("\nTop completions for region=US:")
   for r in mdd.complete({"region": "US"}, k=3):
       print(f"  {r.path} (score: {r.score:.2f})")

Next Steps
----------

- :doc:`concepts` - Understand how MDDs work
- :doc:`api/index` - Complete API reference
- :doc:`examples` - More detailed examples
- :doc:`visualization` - Visualization options


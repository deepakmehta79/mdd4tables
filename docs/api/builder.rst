Builder Module
==============

The Builder class constructs MDDs from DataFrames.

.. automodule:: mdd4tables.builder
   :members:
   :undoc-members:
   :show-inheritance:

Builder
-------

.. autoclass:: mdd4tables.builder.Builder
   :members:
   :undoc-members:
   :special-members: __init__

Usage Example
-------------

.. code-block:: python

   import pandas as pd
   from mdd4tables import Schema, DimensionSpec, DimensionType, BuildConfig, Builder

   df = pd.DataFrame({
       "region": ["EU", "EU", "US", "US"],
       "priority": [1, 2, 1, 3],
   })

   schema = Schema([
       DimensionSpec("region", DimensionType.CATEGORICAL),
       DimensionSpec("priority", DimensionType.ORDINAL),
   ])

   cfg = BuildConfig(ordering="heuristic", enable_reduction=True)
   mdd = Builder(schema, cfg).fit(df)


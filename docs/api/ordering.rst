Ordering Module
===============

Dimension ordering heuristics and search algorithms.

.. automodule:: mdd4tables.ordering
   :members:
   :undoc-members:
   :show-inheritance:

Functions
---------

propose_order
^^^^^^^^^^^^^

.. autofunction:: mdd4tables.ordering.propose_order

evaluate_order
^^^^^^^^^^^^^^

.. autofunction:: mdd4tables.ordering.evaluate_order

Ordering Strategies
-------------------

**fixed**
   Use dimensions in the order specified in the schema.

**heuristic**
   Use a greedy heuristic based on cardinality and entropy.

**search**
   Use budgeted search to find an optimal ordering.

Example
-------

.. code-block:: python

   from mdd4tables import propose_order, Schema, DimensionSpec, DimensionType
   import pandas as pd

   df = pd.DataFrame({
       "a": ["x", "y", "z"],
       "b": [1, 1, 2],
       "c": [10.0, 20.0, 30.0],
   })

   schema = Schema([
       DimensionSpec("a", DimensionType.CATEGORICAL),
       DimensionSpec("b", DimensionType.ORDINAL),
       DimensionSpec("c", DimensionType.NUMERIC),
   ])

   result = propose_order(df, schema)
   print(result.order)  # Suggested dimension ordering


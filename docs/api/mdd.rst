MDD Module
==========

The core MDD class and related data structures.

.. automodule:: mdd4tables.mdd
   :members:
   :undoc-members:
   :show-inheritance:

MDD Class
---------

.. autoclass:: mdd4tables.mdd.MDD
   :members:
   :undoc-members:
   :special-members: __init__, __repr__

The MDD class is the main data structure representing a compiled Multi-Valued Decision Diagram.

**Attributes:**

- ``dim_names`` (List[str]): Ordered list of dimension names
- ``nodes`` (List[Node]): All nodes in the diagram
- ``root`` (int): Index of the root node
- ``terminal_layer`` (int): Layer index of terminal nodes
- ``laplace_alpha`` (float): Smoothing parameter for probabilities
- ``bin_models`` (Dict): Binning models for numeric dimensions

QueryResult
-----------

.. autoclass:: mdd4tables.mdd.QueryResult
   :members:
   :undoc-members:

Result from ``complete()`` or ``nearest()`` queries.

**Attributes:**

- ``path`` (Dict[str, Any]): Complete path as dimension→value mapping
- ``score`` (float): Log-probability score (higher = more likely)
- ``details`` (Dict[str, Any]): Additional information (e.g., ``logprob``, ``distance``)

Node
----

.. autoclass:: mdd4tables.mdd.Node
   :members:
   :undoc-members:

Internal node representation.

**Attributes:**

- ``layer`` (int): Layer index (0 = root layer)
- ``edges`` (Dict[Any, int]): Mapping from arc label to child node index
- ``edge_counts`` (Dict[Any, int]): Traversal counts for each arc
- ``reach_count`` (int): Number of paths reaching this node
- ``terminal_count`` (int): Number of paths terminating here

Arc
---

.. autoclass:: mdd4tables.mdd.Arc
   :members:
   :undoc-members:

Immutable arc representation (used internally).

Query Methods
-------------

size()
^^^^^^

Get MDD statistics.

.. code-block:: python

   stats = mdd.size()
   print(f"Nodes: {stats['nodes']}")
   print(f"Arcs: {stats['arcs']}")
   print(f"Layers: {stats['layers']}")

exists(x)
^^^^^^^^^

Check if an exact path exists.

**Parameters:**

- ``x`` (Dict[str, Any]): Complete path specification

**Returns:** bool

.. code-block:: python

   if mdd.exists({"region": "EU", "product": "A", "tier": "Gold"}):
       print("Configuration exists!")

count(pattern)
^^^^^^^^^^^^^^

Count paths matching a pattern without enumeration.

**Parameters:**

- ``pattern`` (Dict[str, Any], optional): Dimension constraints. Missing dimensions are wildcards.

**Returns:** int

.. code-block:: python

   # Count all paths
   total = mdd.count()

   # Count paths with region=EU
   eu_count = mdd.count({"region": "EU"})

   # Count paths with region=EU AND product=A
   specific = mdd.count({"region": "EU", "product": "A"})

match(pattern, limit)
^^^^^^^^^^^^^^^^^^^^^

Find all paths matching a pattern.

**Parameters:**

- ``pattern`` (Dict[str, Any]): Dimension constraints
- ``limit`` (int): Maximum results (default 1000)

**Returns:** List[Dict[str, Any]]

.. code-block:: python

   # Find all EU configurations
   paths = mdd.match({"region": "EU"}, limit=100)
   for path in paths:
       print(path)

complete(partial, k, beam)
^^^^^^^^^^^^^^^^^^^^^^^^^^

Find top-k completions ranked by conditional probability.

Uses beam search for efficient exploration.

**Parameters:**

- ``partial`` (Dict[str, Any]): Known dimension values
- ``k`` (int): Number of results (default 5)
- ``beam`` (int): Beam width (default 25, higher = more thorough)

**Returns:** List[QueryResult]

.. code-block:: python

   # Find likely completions for partial input
   results = mdd.complete({"region": "EU"}, k=5)

   for r in results:
       print(f"Path: {r.path}")
       print(f"Log-prob: {r.score:.3f}")
       print(f"Probability: {math.exp(r.score):.4f}")
       print()

nearest(partial, dist_fns, k)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A* search with custom per-dimension distance functions.

**Parameters:**

- ``partial`` (Dict[str, Any]): Target values
- ``dist_fns`` (Dict[str, Callable]): Distance function per dimension
- ``k`` (int): Number of results

**Returns:** List[QueryResult]

.. code-block:: python

   # Define distance functions
   dist_fns = {
       "price": lambda want, have: abs(want - have) / 100,
       "category": lambda want, have: 0 if want == have else 1,
   }

   # Find nearest paths
   results = mdd.nearest({"price": 150, "category": "A"}, dist_fns, k=5)

   for r in results:
       print(f"Path: {r.path}")
       print(f"Distance: {r.details['distance']:.3f}")

Example Usage
-------------

.. code-block:: python

   import pandas as pd
   from mdd4tables import Schema, DimensionSpec, DimensionType, BuildConfig, Builder

   # Build MDD
   df = pd.DataFrame({
       "region": ["EU", "EU", "US", "US"],
       "product": ["A", "B", "A", "B"],
       "price": [100, 200, 150, 250],
   })

   schema = Schema([
       DimensionSpec("region", DimensionType.CATEGORICAL),
       DimensionSpec("product", DimensionType.CATEGORICAL),
       DimensionSpec("price", DimensionType.NUMERIC, bins={"strategy": "quantile", "k": 2}),
   ])

   mdd = Builder(schema).fit(df)

   # Query the MDD
   print(f"Total paths: {mdd.count()}")
   print(f"EU paths: {mdd.count({'region': 'EU'})}")

   # Find completions
   for r in mdd.complete({"region": "EU"}, k=2):
       print(r.path, r.score)


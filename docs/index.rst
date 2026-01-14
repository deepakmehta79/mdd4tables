mdd4tables Documentation
=========================

**mdd4tables** is a Python library for building **Multi-Valued Decision Diagrams (MDDs)** from tabular data.

.. image:: https://img.shields.io/badge/python-3.9+-blue.svg
   :target: https://www.python.org/downloads/

.. image:: https://img.shields.io/badge/license-MIT-green.svg
   :target: https://github.com/deepakmehta79/mdd4tables/blob/main/LICENSE

What is an MDD?
---------------

A **Multi-Valued Decision Diagram** is a compact graph representation of a dataset where:

- Each **row** becomes a root→terminal path
- Each **column** (dimension) becomes a layer
- Each **distinct value** (or numeric bin) becomes an arc label
- **Identical sub-structures** are merged to save space

MDDs are particularly useful for:

- **Data compression**: Reduce redundant patterns in tabular data
- **Fast querying**: Count, match, and complete partial records efficiently
- **Probabilistic inference**: Rank completions using conditional probabilities
- **Visualization**: Understand data structure through graph diagrams

Key Features
------------

🗜️ **Compression**
   Bottom-up canonical reduction merges equivalent nodes, often achieving 10-100x compression.

📊 **Conditional Probabilities**
   Every arc tracks traversal counts, enabling Laplace-smoothed probability queries.

🔍 **Partial-Input Completion**
   Given partial data, find the most likely completions using beam search.

🔄 **Dimension Ordering**
   Heuristic and search-based algorithms to minimize MDD size.

🎨 **Rich Visualization**
   Multiple backends: Matplotlib, Plotly (interactive), PyVis (physics-based), and Graphviz.

⚡ **Two Compilation Methods**
   - **Trie**: Build tree, then reduce (traditional)
   - **Slice**: Incremental bottom-up (memory efficient)

Quick Example
-------------

.. code-block:: python

   import pandas as pd
   from mdd4tables import Schema, DimensionSpec, DimensionType, BuildConfig, Builder

   # Sample data
   df = pd.DataFrame({
       "region": ["EU", "EU", "US", "US", "APAC"],
       "product": ["A", "B", "A", "A", "B"],
       "priority": [1, 2, 1, 2, 1],
   })

   # Define schema
   schema = Schema([
       DimensionSpec("region", DimensionType.CATEGORICAL),
       DimensionSpec("product", DimensionType.CATEGORICAL),
       DimensionSpec("priority", DimensionType.ORDINAL),
   ])

   # Build MDD
   mdd = Builder(schema, BuildConfig(ordering="heuristic")).fit(df)
   print(mdd)  # MDD(dims=['priority', 'product', 'region'], nodes=8, arcs=9)

   # Query: find top completions for partial input
   results = mdd.complete({"region": "EU"}, k=3)
   for r in results:
       print(f"{r.path} (score: {r.score:.2f})")

Installation
------------

.. code-block:: bash

   # Basic installation
   pip install mdd4tables

   # With visualization support
   pip install mdd4tables[viz]

   # Development installation
   git clone https://github.com/deepakmehta79/mdd4tables.git
   cd mdd4tables
   pip install -e ".[all]"

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart
   concepts
   api/index
   examples
   visualization

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


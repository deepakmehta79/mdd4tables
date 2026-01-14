Visualization Guide
===================

mdd4tables provides multiple visualization backends for different use cases.

Installation
------------

Visualization requires optional dependencies:

.. code-block:: bash

   pip install mdd4tables[viz]

This installs: NetworkX, Matplotlib, Plotly, and PyVis.

Quick Start
-----------

.. code-block:: python

   from mdd4tables.viz_advanced import visualize_mdd

   # Simple hierarchical diagram
   visualize_mdd(mdd, method="hierarchical", save_path="mdd.png")

Visualization Methods
---------------------

hierarchical (default)
^^^^^^^^^^^^^^^^^^^^^^

Clean top-to-bottom layered layout. Best for understanding structure.

.. code-block:: python

   from mdd4tables.viz_advanced import visualize_mdd

   visualize_mdd(
       mdd,
       method="hierarchical",
       title="My MDD Structure",
       save_path="mdd_hierarchical.png",
       figsize=(16, 12)
   )

**Features:**

- Nodes grouped by layer (dimension)
- Edge thickness proportional to traversal count
- Terminal nodes highlighted in green
- Color-coded layers

force
^^^^^

Physics-based force-directed layout using NetworkX spring algorithm.

.. code-block:: python

   visualize_mdd(
       mdd,
       method="force",
       title="Force-Directed MDD",
       save_path="mdd_force.png",
       figsize=(14, 14)
   )

**Features:**

- Reveals natural clustering
- Good for finding dense subgraphs
- Edges act as springs

pyvis
^^^^^

Interactive HTML visualization with physics simulation. Opens in browser.

.. code-block:: python

   visualize_mdd(
       mdd,
       method="pyvis",
       title="Interactive MDD",
       save_path="mdd_interactive.html"
   )

**Features:**

- Drag nodes to rearrange
- Zoom and pan
- Hover for node/edge details
- Physics simulation (can be disabled)

interactive (Plotly)
^^^^^^^^^^^^^^^^^^^^

Interactive Plotly-based visualization. Works in Jupyter notebooks.

.. code-block:: python

   visualize_mdd(
       mdd,
       method="interactive",
       title="Plotly MDD",
       save_path="mdd_plotly.html"
   )

**Features:**

- Interactive zoom/pan
- Hover tooltips
- Export to PNG/SVG
- Jupyter notebook integration

graphviz
^^^^^^^^

Professional hierarchical layout using Graphviz (requires system installation).

.. code-block:: python

   visualize_mdd(
       mdd,
       method="graphviz",
       title="Graphviz MDD",
       save_path="mdd_graphviz.png"
   )

**Requirements:**

.. code-block:: bash

   # macOS
   brew install graphviz
   pip install pygraphviz

   # Ubuntu/Debian
   sudo apt-get install graphviz graphviz-dev
   pip install pygraphviz

Basic Visualization Module
--------------------------

For simple use cases, use the basic ``viz`` module:

.. code-block:: python

   from mdd4tables.viz import to_networkx, draw

   # Convert to NetworkX graph
   G = to_networkx(mdd)
   print(f"Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")

   # Simple matplotlib drawing
   draw(mdd, max_nodes=100, show_edge_labels=True)

Customizing Visualizations
--------------------------

Size Limits
^^^^^^^^^^^

For large MDDs, visualization becomes cluttered. Set limits:

.. code-block:: python

   visualize_mdd(
       mdd,
       method="hierarchical",
       max_nodes=200,  # Skip if more nodes
       save_path="mdd.png"
   )

Figure Size
^^^^^^^^^^^

Adjust figure dimensions:

.. code-block:: python

   visualize_mdd(
       mdd,
       method="hierarchical",
       figsize=(20, 16),  # Width x Height in inches
       save_path="mdd_large.png"
   )

PyVis Customization
^^^^^^^^^^^^^^^^^^^

PyVis supports additional options:

.. code-block:: python

   from mdd4tables.viz_advanced import visualize_mdd

   # The function creates a PyVis Network internally
   # For more control, you can create your own:

   from mdd4tables.viz import to_networkx
   from pyvis.network import Network

   G = to_networkx(mdd)

   net = Network(
       height="800px",
       width="100%",
       bgcolor="#ffffff",
       font_color="black",
       directed=True
   )

   # Customize physics
   net.barnes_hut(
       gravity=-80000,
       central_gravity=0.3,
       spring_length=250,
       spring_strength=0.001
   )

   # Add nodes and edges from NetworkX graph
   net.from_nx(G)

   # Save
   net.save_graph("custom_mdd.html")

Exporting to DOT Format
-----------------------

For very large MDDs or custom processing, export to Graphviz DOT format:

.. code-block:: python

   from mdd4tables.viz import to_networkx
   import networkx as nx

   G = to_networkx(mdd)

   # Write DOT file
   nx.drawing.nx_pydot.write_dot(G, "mdd.dot")

   # Then render with Graphviz CLI:
   # dot -Tpng mdd.dot -o mdd.png
   # dot -Tsvg mdd.dot -o mdd.svg
   # dot -Tpdf mdd.dot -o mdd.pdf

Visualization Examples
----------------------

Example 1: BDD for Boolean Function
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   import pandas as pd
   from mdd4tables import Schema, DimensionSpec, DimensionType, BuildConfig, Builder
   from mdd4tables.viz_advanced import visualize_mdd

   # XOR function
   df = pd.DataFrame({
       "x": [0, 0, 1, 1],
       "y": [0, 1, 0, 1],
       "f": [0, 1, 1, 0],
   })

   schema = Schema([
       DimensionSpec("x", DimensionType.ORDINAL),
       DimensionSpec("y", DimensionType.ORDINAL),
       DimensionSpec("f", DimensionType.ORDINAL),
   ])

   mdd = Builder(schema, BuildConfig(ordering="fixed")).fit(df, order=["x", "y", "f"])

   visualize_mdd(mdd, method="hierarchical", title="XOR BDD", save_path="xor_bdd.png")

Example 2: Comparing Compilation Methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from mdd4tables import BuildConfig, Builder
   from mdd4tables.viz_advanced import visualize_mdd

   # Build with trie
   mdd_trie = Builder(schema, BuildConfig(compilation_method="trie")).fit(df)
   visualize_mdd(mdd_trie, title="Trie Method", save_path="mdd_trie.png")

   # Build with slice
   mdd_slice = Builder(schema, BuildConfig(compilation_method="slice")).fit(df)
   visualize_mdd(mdd_slice, title="Slice Method", save_path="mdd_slice.png")

Tips for Large MDDs
-------------------

1. **Use max_nodes limit**: Prevent memory issues

   .. code-block:: python

      visualize_mdd(mdd, max_nodes=100)

2. **Filter before visualizing**: Build MDD on subset

   .. code-block:: python

      df_sample = df.sample(n=100)
      mdd_sample = Builder(schema).fit(df_sample)
      visualize_mdd(mdd_sample)

3. **Use PyVis for interactivity**: Better for exploration

   .. code-block:: python

      visualize_mdd(mdd, method="pyvis", save_path="explore.html")

4. **Export to DOT for very large graphs**: Use Graphviz CLI

   .. code-block:: bash

      dot -Tsvg mdd.dot -o mdd.svg

Troubleshooting
---------------

**"Too many nodes to draw"**

The MDD is too large. Either:

- Increase ``max_nodes`` parameter
- Filter your data to a smaller subset
- Use PyVis which handles larger graphs better

**"Install extra 'viz'"**

Install visualization dependencies:

.. code-block:: bash

   pip install mdd4tables[viz]

**Graphviz errors**

Install Graphviz system package:

.. code-block:: bash

   # macOS
   brew install graphviz

   # Ubuntu
   sudo apt-get install graphviz graphviz-dev

**PyVis not showing in Jupyter**

Use ``net.show("mdd.html")`` or display the HTML file directly.


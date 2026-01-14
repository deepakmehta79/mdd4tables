Visualization Guide
===================

mdd4tables provides multiple visualization options for MDDs.

Installation
------------

Visualization requires optional dependencies:

.. code-block:: bash

   pip install -e ".[viz]"

This installs NetworkX, Matplotlib, Plotly, and PyVis.

Static Diagrams
---------------

Using Matplotlib for static PNG/PDF output:

.. code-block:: python

   from mdd4tables.viz import draw_mdd

   # Basic diagram
   draw_mdd(mdd, filename="mdd.png")

   # Customize appearance
   draw_mdd(mdd, filename="mdd.pdf", figsize=(12, 8), show_counts=True)

Interactive Plotly
------------------

Create interactive diagrams viewable in browser or Jupyter:

.. code-block:: python

   from mdd4tables.viz_advanced import draw_mdd_plotly

   fig = draw_mdd_plotly(mdd, layout="hierarchical")
   fig.show()

   # Save to HTML
   fig.write_html("mdd_interactive.html")

PyVis Networks
--------------

Generate standalone interactive HTML files:

.. code-block:: python

   from mdd4tables.viz_advanced import draw_mdd_pyvis

   # Generates HTML file with physics-based layout
   draw_mdd_pyvis(mdd, filename="mdd_network.html")

   # Customize options
   draw_mdd_pyvis(
       mdd,
       filename="mdd_custom.html",
       height="800px",
       width="100%",
       physics=True
   )

Layout Options
--------------

**hierarchical**
   Top-to-bottom layout showing layer structure clearly.

**force**
   Physics-based force-directed layout.

**circular**
   Nodes arranged in a circle.

Tips for Large MDDs
-------------------

For MDDs with many nodes:

1. **Limit depth**: Show only first N layers
2. **Filter paths**: Focus on specific patterns
3. **Use PyVis**: Better performance for large graphs
4. **Export to DOT**: Use Graphviz for very large diagrams

.. code-block:: python

   # Export to DOT format for Graphviz
   from mdd4tables.viz import export_dot

   dot_string = export_dot(mdd)
   with open("mdd.dot", "w") as f:
       f.write(dot_string)

   # Then render with: dot -Tpng mdd.dot -o mdd.png


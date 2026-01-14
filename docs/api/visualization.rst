Visualization Module
====================

Tools for visualizing MDDs using various libraries.

viz Module
----------

Basic visualization with NetworkX and Matplotlib.

.. automodule:: mdd4tables.viz
   :members:
   :undoc-members:
   :show-inheritance:

viz_advanced Module
-------------------

Advanced interactive visualizations with Plotly and PyVis.

.. automodule:: mdd4tables.viz_advanced
   :members:
   :undoc-members:
   :show-inheritance:

Usage Examples
--------------

Static Visualization (Matplotlib)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from mdd4tables.viz import draw_mdd

   # Draw MDD with matplotlib
   draw_mdd(mdd, filename="mdd_diagram.png")

Interactive Visualization (Plotly)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from mdd4tables.viz_advanced import draw_mdd_plotly

   # Create interactive Plotly figure
   fig = draw_mdd_plotly(mdd)
   fig.show()

PyVis Network
^^^^^^^^^^^^^

.. code-block:: python

   from mdd4tables.viz_advanced import draw_mdd_pyvis

   # Generate interactive HTML
   draw_mdd_pyvis(mdd, filename="mdd_network.html")


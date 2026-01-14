mdd4tables Documentation
=========================

**mdd4tables** is a Python library for building Multi-Valued Decision Diagrams (MDDs) from tabular data.

Each row becomes a root→terminal path, each column a layer, and each distinct value or numeric bin an arc label.

Features
--------

- **Compression**: Bottom-up merging (canonical reduction) for compact representation
- **Conditional Probabilities**: Arc/node counts with Laplace smoothing
- **Partial-Input Completion**: Find top-k completions ranked by probability
- **Dimension Ordering**: Heuristics and budgeted search for optimal ordering
- **Visualization**: Interactive diagrams with NetworkX, Matplotlib, Plotly, and PyVis

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart
   api/index
   examples
   visualization

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


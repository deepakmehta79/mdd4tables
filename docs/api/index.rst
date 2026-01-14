API Reference
=============

This section contains the complete API documentation for mdd4tables.

Overview
--------

The main classes and functions are:

**Core Classes:**

- :class:`~mdd4tables.Schema` - Define dimension types and binning
- :class:`~mdd4tables.DimensionSpec` - Specification for a single dimension
- :class:`~mdd4tables.DimensionType` - Enum of dimension types
- :class:`~mdd4tables.Builder` - Build MDDs from DataFrames
- :class:`~mdd4tables.MDD` - The compiled decision diagram
- :class:`~mdd4tables.BuildConfig` - Build configuration options
- :class:`~mdd4tables.QueryConfig` - Query configuration options

**Ordering Functions:**

- :func:`~mdd4tables.propose_order` - Heuristic dimension ordering
- :func:`~mdd4tables.evaluate_order` - Evaluate an ordering

**Visualization:**

- :mod:`mdd4tables.viz` - Basic NetworkX/Matplotlib visualization
- :mod:`mdd4tables.viz_advanced` - Advanced interactive visualization

Import Shortcuts
----------------

All main classes are available from the top-level package:

.. code-block:: python

   from mdd4tables import (
       # Schema
       Schema,
       DimensionSpec,
       DimensionType,

       # Building
       Builder,
       BuildConfig,
       OrderingConfig,
       QueryConfig,

       # The MDD itself
       MDD,

       # Ordering utilities
       propose_order,
       evaluate_order,
   )

Module Reference
----------------

.. toctree::
   :maxdepth: 2

   schema
   config
   builder
   mdd
   ordering
   visualization


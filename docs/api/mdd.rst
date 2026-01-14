MDD Module
==========

The core MDD class and query functionality.

.. automodule:: mdd4tables.mdd
   :members:
   :undoc-members:
   :show-inheritance:

MDD
---

.. autoclass:: mdd4tables.mdd.MDD
   :members:
   :undoc-members:
   :special-members: __init__, __repr__

QueryResult
-----------

.. autoclass:: mdd4tables.mdd.QueryResult
   :members:
   :undoc-members:

Node
----

.. autoclass:: mdd4tables.mdd.Node
   :members:
   :undoc-members:

Arc
---

.. autoclass:: mdd4tables.mdd.Arc
   :members:
   :undoc-members:

Query Methods
-------------

exists
^^^^^^

Check if an exact path exists in the MDD.

.. code-block:: python

   mdd.exists({"region": "EU", "priority": 1})  # Returns True/False

count
^^^^^

Count paths matching a pattern without enumerating them.

.. code-block:: python

   mdd.count({"region": "EU"})  # Count all paths with region=EU
   mdd.count()  # Count all paths

match
^^^^^

Find all paths matching a pattern.

.. code-block:: python

   paths = mdd.match({"region": "EU"}, limit=100)

complete
^^^^^^^^

Find top-k completions ranked by conditional probability.

.. code-block:: python

   results = mdd.complete({"region": "EU"}, k=5)
   for r in results:
       print(r.path, r.score)


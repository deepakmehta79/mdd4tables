'''
This example builds a BDD for a custom boolean function defined by the user.
It compares the trie compilation method vs slice compilation method.

The function is defined by the following truth table:
    x1  x2  x3  |  f
    0   0   0   |  1
    0   0   1   |  0
    0   1   0   |  0
    0   1   1   |  1
    1   0   0   |  0
    1   0   1   |  0
    1   1   0   |  1
    1   1   1   |  1
'''

import pandas as pd
import numpy as np
from mdd4tables import Schema, DimensionSpec, DimensionType, BuildConfig, Builder

# Create truth table for the custom function
# as defined by the user's truth table.
def custom_function(x1, x2, x3):
    # Implemented as a lookup table for clarity
    return {
        (0, 0, 0): 1,
        (0, 0, 1): 0,
        (0, 1, 0): 0,
        (0, 1, 1): 1,
        (1, 0, 0): 0,
        (1, 0, 1): 0,
        (1, 1, 0): 1,
        (1, 1, 1): 1,
    }[(x1, x2, x3)]

# Generate all combinations
rows = []
for x1 in [0, 1]:
    for x2 in [0, 1]:
        for x3 in [0, 1]:
            f = custom_function(x1, x2, x3)
            rows.append({"x1": x1, "x2": x2, "x3": x3, "f": f})

df = pd.DataFrame(rows)
print("Truth Table for Custom Function f(x1,x2,x3):")
print(df.to_string(index=False))
print()

# Build MDD with fixed ordering x1 -> x2 -> x3 -> f
schema = Schema([
    DimensionSpec("x1", DimensionType.ORDINAL),
    DimensionSpec("x2", DimensionType.ORDINAL),
    DimensionSpec("x3", DimensionType.ORDINAL),
    DimensionSpec("f", DimensionType.ORDINAL),
])

print("=" * 70)
print("METHOD 1: TRIE COMPILATION (with reduction)")
print("=" * 70)

# Build with trie method
cfg_trie = BuildConfig(ordering="fixed", compilation_method="trie", enable_reduction=True)
mdd_trie = Builder(schema, cfg_trie).fit(df, order=["x1", "x2", "x3", "f"])

print(f"MDD Statistics: {mdd_trie.size()}")
print(f"Dimension order: {mdd_trie.dim_names}")
print()

# Show the structure
print("MDD Node Structure:")
print("-" * 70)
for i, node in enumerate(mdd_trie.nodes):
    layer_name = mdd_trie.dim_names[node.layer] if node.layer < len(mdd_trie.dim_names) else "Terminal"
    edges_str = ", ".join(f"{k}->{v}" for k, v in sorted(node.edges.items()))
    term_info = f" [TERMINAL: {node.terminal_count} paths]" if node.terminal_count > 0 else ""
    print(f"Node {i} (layer {node.layer}: {layer_name}): edges=[{edges_str}]{term_info}")

print()
print("=" * 70)
print("METHOD 2: SLICE COMPILATION (incremental reduction)")
print("=" * 70)

# Build with slice method
cfg_slice = BuildConfig(ordering="fixed", compilation_method="slice")
mdd_slice = Builder(schema, cfg_slice).fit(df, order=["x1", "x2", "x3", "f"])

print(f"MDD Statistics: {mdd_slice.size()}")
print(f"Dimension order: {mdd_slice.dim_names}")
print()

# Show the structure
print("MDD Node Structure:")
print("-" * 70)
for i, node in enumerate(mdd_slice.nodes):
    layer_name = mdd_slice.dim_names[node.layer] if node.layer < len(mdd_slice.dim_names) else "Terminal"
    edges_str = ", ".join(f"{k}->{v}" for k, v in sorted(node.edges.items()))
    term_info = f" [TERMINAL: {node.terminal_count} paths]" if node.terminal_count > 0 else ""
    print(f"Node {i} (layer {node.layer}: {layer_name}): edges=[{edges_str}]{term_info}")

print()
print("=" * 70)
print("COMPARISON")
print("=" * 70)
trie_size = mdd_trie.size()
slice_size = mdd_slice.size()
print(f"Trie method:  {trie_size['nodes']} nodes, {trie_size['arcs']} arcs")
print(f"Slice method: {slice_size['nodes']} nodes, {slice_size['arcs']} arcs")
print(f"Match: {'YES ✓' if trie_size == slice_size else 'NO ✗'}")

# Verify queries work identically
print()
print("=" * 70)
print("QUERY VERIFICATION (both methods should produce same results)")
print("=" * 70)

test_cases = [
    {"x1": 0, "x2": 0, "x3": 0},  # Expected f=1
    {"x1": 0, "x2": 0, "x3": 1},  # Expected f=0
    {"x1": 1, "x2": 0, "x3": 1},  # Expected f=0
    {"x1": 0, "x2": 1, "x3": 1},  # Expected f=1
]

for tc in test_cases:
    matches_trie = mdd_trie.match(tc)
    matches_slice = mdd_slice.match(tc)
    f_trie = [m['f'] for m in matches_trie]
    f_slice = [m['f'] for m in matches_slice]
    match_symbol = "✓" if f_trie == f_slice else "✗"
    print(f"Input: {tc}")
    print(f"  Trie:  f={f_trie}  |  Slice: f={f_slice}  [{match_symbol}]")

print()
print("All paths where f=1 (custom function returns true):")
paths_trie = mdd_trie.match({"f": 1})
paths_slice = mdd_slice.match({"f": 1})
print(f"Trie found {len(paths_trie)} paths, Slice found {len(paths_slice)} paths")
for path in paths_trie:
    print(f"  x1={path['x1']}, x2={path['x2']}, x3={path['x3']}")
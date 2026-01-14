import pandas as pd
from mdd4tables import Schema, DimensionSpec, DimensionType, BuildConfig, Builder

df = pd.DataFrame({
    "region": ["EU","EU","EU","US","US","APAC"],
    "priority": [1,2,1,3,1,2],
    "qty": [10.1, 9.7, 10.3, 4.9, 5.1, 8.2],
})

schema = Schema([
    DimensionSpec("region", DimensionType.CATEGORICAL),
    DimensionSpec("priority", DimensionType.ORDINAL),
    DimensionSpec("qty", DimensionType.NUMERIC, bins={"strategy":"quantile","k":3}),
])

mdd = Builder(schema, BuildConfig(ordering="heuristic")).fit(df)
print("size:", mdd.size())

# Print the intervals created for qty dimension
print("\nIntervals for 'qty' dimension:")
if "qty" in mdd.bin_models:
    bin_model = mdd.bin_models["qty"]
    print(f"  Strategy: {bin_model.strategy}")
    print(f"  Edges: {bin_model.edges}")
    print(f"  Number of bins: {len(bin_model.edges) - 1}")
    for i in range(len(bin_model.edges) - 1):
        print(f"    Bin {i}: [{bin_model.edges[i]}, {bin_model.edges[i+1]})")

print("\nTop completions for region=EU")
for r in mdd.complete({"region":"EU"}, k=5):
    print(r)

# nearest with custom distance on ordinal
def ord_dist(a,b): return abs(int(a)-int(b))
res = mdd.nearest({"region":"US","priority":2}, dist_fns={"priority": ord_dist}, k=3)
print("\nNearest to region=US, priority=2")
for r in res:
    print(r)

# Visualization
print("\nAttempting to visualize MDD...")
try:
    from mdd4tables.viz import draw
    draw(mdd, show_edge_labels=True)
except ImportError as e:
    print(f"Visualization not available: {e}")
    print("Install viz dependencies with: pip install mdd4tables[viz]")
except Exception as e:
    print(f"Visualization error: {e}")


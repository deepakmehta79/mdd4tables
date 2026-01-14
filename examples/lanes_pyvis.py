"""
Generate PyVis Interactive Visualization for Lanes MDD

This creates a beautiful interactive network visualization with:
- Physics simulation
- Draggable nodes
- Hover for details
- Hierarchical layout
"""

import pandas as pd
from mdd4tables import Schema, DimensionSpec, DimensionType, BuildConfig, Builder
from mdd4tables.viz_advanced import visualize_mdd

# Configuration
EXCEL_FILE = "examples/ib_weekly_splits_20250807-091113.xlsx"
SHEET_NAME = "Lanes"
COMPILATION_METHOD = "slice"  # or "trie"

# Select key dimensions for MDD
SELECTED_COLUMNS = [
    "LOB",                      # Line of Business
    "GEO",                      # Geography
    "MODE_TYPE",                # Air/Ocean/etc
    "DEPLOYMENT_MODE",          # FD/DS
    "BULK_PARCEL",             # Bulk/Parcel
    "LOG_COMMIT_COUNTRY_GRP",  # Logistics country group
    "PRIMARY_UPLIFT_LOC",      # Primary uplift location
    "OEM_DESC"
]

print("=" * 70)
print("LANES MDD - PYVIS INTERACTIVE VISUALIZATION")
print("=" * 70)
print(f"Compilation method: {COMPILATION_METHOD.upper()}")
print()

# Read data
print("Reading Excel file...")
df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)
print(f"Loaded {len(df):,} rows")

# Select and clean data
df_selected = df[SELECTED_COLUMNS].copy()
critical_columns = ["LOB", "GEO", "MODE_TYPE"]
df_clean = df_selected.dropna(subset=critical_columns)

# Sample if too large
MAX_ROWS = 1000
if len(df_clean) > MAX_ROWS:
    print(f"Sampling {MAX_ROWS:,} rows for demo...")
    df_clean = df_clean.sample(n=MAX_ROWS, random_state=42)

print(f"Building MDD from {len(df_clean):,} rows...")

# Create schema
schema = Schema([
    DimensionSpec(col, DimensionType.CATEGORICAL, missing_token="UNKNOWN")
    for col in SELECTED_COLUMNS
])

# Build MDD
cfg = BuildConfig(
    ordering="heuristic",
    compilation_method=COMPILATION_METHOD
)
mdd = Builder(schema, cfg).fit(df_clean)

# Show stats
size = mdd.size()
print(f"\nMDD Statistics:")
print(f"  Nodes: {size['nodes']:,}")
print(f"  Arcs:  {size['arcs']:,}")
print(f"  Compression: {len(df_clean) / size['nodes']:.1f}x")
print()

# Generate PyVis visualization
print("=" * 70)
print("GENERATING PYVIS INTERACTIVE VISUALIZATION")
print("=" * 70)

output_file = f"lanes_mdd_pyvis_{COMPILATION_METHOD}.html"

visualize_mdd(
    mdd,
    method="pyvis",
    title=f"Lanes MDD Interactive - {COMPILATION_METHOD.upper()} Method ({size['nodes']} nodes)",
    save_path=output_file
)

print()
print("=" * 70)
print("COMPLETE!")
print("=" * 70)
print(f"\nInteractive visualization saved to: {output_file}")
print("\nFeatures you can try:")
print("  ✓ Drag nodes to reposition them")
print("  ✓ Hover over nodes to see layer info and edge counts")
print("  ✓ Hover over edges to see labels and counts")
print("  ✓ Zoom in/out with mouse wheel")
print("  ✓ Pan by dragging the background")
print("  ✓ Watch the physics simulation settle")
print("\nThe visualization should open automatically in your browser!")
"""
Build MDD from Lanes shipping data.

This script reads the "Lanes" tab from the Excel file and builds a Multi-Valued
Decision Diagram to represent shipping lane configurations.

Usage:
    python examples/lanes_mdd_example.py           # Default: trie method
    python examples/lanes_mdd_example.py slice     # Use slice method
    python examples/lanes_mdd_example.py trie      # Explicit trie method
"""

import pandas as pd
import sys
from mdd4tables import Schema, DimensionSpec, DimensionType, BuildConfig, Builder

# Configuration
EXCEL_FILE = "examples/ib_weekly_splits_20250807-091113.xlsx"
SHEET_NAME = "Lanes"

# Select key dimensions for MDD (avoid too many to keep it manageable)
SELECTED_COLUMNS = [
    "LOB",                      # Line of Business
    "GEO",                      # Geography
    "MODE_TYPE",                # Air/Ocean/etc
    "DEPLOYMENT_MODE",          # FD/DS
    "BULK_PARCEL",             # Bulk/Parcel
    "LOG_COMMIT_COUNTRY_GRP",  # Logistics country group
    "PRIMARY_UPLIFT_LOC",      # Primary uplift location
]

# Check command line argument for compilation method
compilation_method = "trie"  # default
if len(sys.argv) > 1:
    method = sys.argv[1].lower()
    if method in ["slice", "trie"]:
        compilation_method = method
    else:
        print(f"Unknown method '{method}'. Use 'trie' or 'slice'. Defaulting to trie.")

print("=" * 70)
print("LANES MDD BUILDER")
print("=" * 70)
print(f"Compilation method: {compilation_method.upper()}")
print(f"Excel file: {EXCEL_FILE}")
print(f"Sheet: {SHEET_NAME}")
print()

# Read data
print("Reading Excel file...")
df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME)
print(f"Loaded {len(df):,} rows with {len(df.columns)} columns")
print()

# Select columns and handle missing values
print(f"Selecting {len(SELECTED_COLUMNS)} key dimensions:")
for col in SELECTED_COLUMNS:
    print(f"  - {col}")
print()

df_selected = df[SELECTED_COLUMNS].copy()

# Show data statistics before cleaning
print("Data Quality Check:")
print("-" * 70)
for col in SELECTED_COLUMNS:
    total = len(df_selected)
    missing = df_selected[col].isna().sum()
    unique = df_selected[col].nunique()
    pct_missing = (missing / total) * 100
    print(f"{col:30s}: {unique:5d} unique, {missing:5d} missing ({pct_missing:5.1f}%)")
print()

# Drop rows with too many missing values (optional - or we can use __MISSING__ token)
# For now, let's keep all rows and use missing tokens
print(f"Total rows before cleaning: {len(df_selected):,}")

# Remove rows where critical columns are missing
critical_columns = ["LOB", "GEO", "MODE_TYPE"]
df_clean = df_selected.dropna(subset=critical_columns)
print(f"Total rows after removing critical nulls: {len(df_clean):,}")
print()

# Take a sample if dataset is too large (for demo purposes)
MAX_ROWS = 1000
if len(df_clean) > MAX_ROWS:
    print(f"Dataset is large ({len(df_clean):,} rows). Taking a sample of {MAX_ROWS:,} rows for demo.")
    df_clean = df_clean.sample(n=MAX_ROWS, random_state=42)
    print()

# Show unique value counts after cleaning
print("Dimension Cardinality (after cleaning):")
print("-" * 70)
for col in SELECTED_COLUMNS:
    unique = df_clean[col].nunique()
    print(f"{col:30s}: {unique:5d} unique values")
print()

# Create schema - all categorical for this dataset
schema = Schema([
    DimensionSpec(col, DimensionType.CATEGORICAL, missing_token="UNKNOWN")
    for col in SELECTED_COLUMNS
])

# Build MDD
print("=" * 70)
print(f"Building MDD with {compilation_method.upper()} method...")
print("=" * 70)

if compilation_method == "slice":
    cfg = BuildConfig(
        ordering="heuristic",  # Let algorithm decide best order
        compilation_method="slice"
    )
else:
    cfg = BuildConfig(
        ordering="heuristic",  # Let algorithm decide best order
        compilation_method="trie",
        enable_reduction=True
    )

mdd = Builder(schema, cfg).fit(df_clean)

# Show results
print(f"\nMDD Statistics:")
print("-" * 70)
size = mdd.size()
print(f"Nodes:  {size['nodes']:,}")
print(f"Arcs:   {size['arcs']:,}")
print(f"Layers: {size['layers']}")
print()

print("Dimension order chosen by heuristic:")
for i, dim in enumerate(mdd.dim_names):
    node_count = sum(1 for n in mdd.nodes if n.layer == i)
    print(f"  Layer {i}: {dim:30s} ({node_count} nodes)")
print()

# Compression ratio
original_paths = len(df_clean)
compression_ratio = original_paths / size['nodes'] if size['nodes'] > 0 else 0
print(f"Compression:")
print(f"  Original paths: {original_paths:,}")
print(f"  MDD nodes:      {size['nodes']:,}")
print(f"  Ratio:          {compression_ratio:.2f}x")
print()

# Example queries
print("=" * 70)
print("EXAMPLE QUERIES")
print("=" * 70)

# Query 1: Count paths by LOB
print("\n1. Count of shipping lanes by Line of Business (LOB):")
print("-" * 70)
for lob in sorted(df_clean['LOB'].unique()):
    count = mdd.count({"LOB": lob})
    print(f"  {lob:15s}: {count:5d} lanes")

# Query 2: Find lanes for specific criteria
print("\n2. Find lanes for IPHONE in APAC with AIR mode:")
print("-" * 70)
query = {"LOB": "IPHONE", "GEO": "APAC", "MODE_TYPE": "AIR"}
matches = mdd.match(query, limit=10)
if matches:
    print(f"Found {len(matches)} matching lanes (showing first 10):")
    for i, path in enumerate(matches[:10], 1):
        print(f"\n  Lane {i}:")
        for key, val in path.items():
            print(f"    {key:30s}: {val}")
else:
    print("No matches found. Trying just LOB and GEO...")
    query2 = {"LOB": "IPHONE", "GEO": "APAC"}
    matches2 = mdd.match(query2, limit=5)
    if matches2:
        print(f"Found {len(matches2)} matches for {query2}:")
        for i, path in enumerate(matches2[:5], 1):
            print(f"\n  Lane {i}:")
            for key, val in path.items():
                print(f"    {key:30s}: {val}")

# Query 3: Complete partial specification
print("\n3. Top-5 most likely completions for LOB=ACCY, GEO=EURO:")
print("-" * 70)
partial = {"LOB": "ACCY", "GEO": "EURO"}
completions = mdd.complete(partial, k=5)
if completions:
    for i, result in enumerate(completions, 1):
        print(f"\n  Completion {i} (score: {result.score:.3f}):")
        for key, val in result.path.items():
            print(f"    {key:30s}: {val}")
else:
    print("No completions found.")

# Query 4: Exists check
print("\n4. Check if specific lane configuration exists:")
print("-" * 70)
if len(df_clean) > 0:
    sample_row = df_clean.iloc[0].to_dict()
    exists = mdd.exists(sample_row)
    print(f"Lane configuration from first row:")
    for key, val in sample_row.items():
        print(f"  {key:30s}: {val}")
    print(f"\nExists in MDD: {'YES ✓' if exists else 'NO ✗'}")

print()
print("=" * 70)
print("COMPLETE")
print("=" * 70)
print(f"MDD built successfully with {compilation_method.upper()} method")
print(f"Final size: {size['nodes']:,} nodes, {size['arcs']:,} arcs")
print()
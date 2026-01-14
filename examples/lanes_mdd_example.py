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
    "OEM_DESC"
    "DESTINATION"
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

# Visualization
print()
print("=" * 70)
print("VISUALIZATION")
print("=" * 70)

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    def draw_mdd(mdd, title="Multi-Valued Decision Diagram", save_path=None, max_nodes=200):
        """Draw MDD with hierarchical layout."""

        # Check if too large to visualize
        if len(mdd.nodes) > max_nodes:
            print(f"MDD has {len(mdd.nodes)} nodes, which is too large to visualize clearly.")
            print(f"Skipping visualization (max {max_nodes} nodes recommended).")
            return

        fig, ax = plt.subplots(figsize=(16, 12))

        # Group nodes by layer
        layers = {}
        for i, n in enumerate(mdd.nodes):
            layers.setdefault(n.layer, []).append(i)

        # Calculate positions - top to bottom layout
        pos = {}
        layer_widths = {layer: len(nodes) for layer, nodes in layers.items()}
        max_width = max(layer_widths.values())

        for layer, nodes in layers.items():
            width = len(nodes)
            for j, node_id in enumerate(nodes):
                # Center nodes horizontally within each layer
                x = (j - (width - 1) / 2) * 2.0
                y = -layer * 2.5  # Top to bottom
                pos[node_id] = (x, y)

        # Draw edges first (so they're behind nodes)
        for node_id, (x, y) in pos.items():
            node = mdd.nodes[node_id]
            for label, child_id in node.edges.items():
                cx, cy = pos[child_id]

                # Color edges by count if available
                count = node.edge_counts.get(label, 0)
                # Normalize alpha by count (higher count = more opaque)
                max_count = max(node.edge_counts.values()) if node.edge_counts else 1
                alpha = 0.3 + 0.7 * (count / max_count) if max_count > 0 else 0.5

                # Draw edge
                ax.annotate("", xy=(cx, cy + 0.3), xytext=(x, y - 0.3),
                           arrowprops=dict(arrowstyle='->', color='gray',
                                          alpha=alpha, lw=1.5))

                # Edge label (show only if not too many edges)
                if len(node.edges) <= 5:
                    mid_x, mid_y = (x + cx) / 2, (y + cy) / 2
                    label_str = str(label)[:15] + "..." if len(str(label)) > 15 else str(label)
                    ax.text(mid_x + 0.2, mid_y, label_str, fontsize=7,
                           color='gray', ha='left', va='center', alpha=0.7)

        # Draw nodes
        for node_id, (x, y) in pos.items():
            node = mdd.nodes[node_id]

            if node.terminal_count > 0:
                # Terminal nodes - rounded squares
                rect = mpatches.FancyBboxPatch((x - 0.25, y - 0.25), 0.5, 0.5,
                                               boxstyle="round,pad=0.05",
                                               facecolor='#27ae60', edgecolor='#229954',
                                               linewidth=2)
                ax.add_patch(rect)
                # Show terminal count
                ax.text(x, y, f"✓\n{node.terminal_count}", fontsize=8,
                       fontweight='bold', ha='center', va='center', color='white')
            else:
                # Decision nodes - circles
                layer_name = mdd.dim_names[node.layer] if node.layer < len(mdd.dim_names) else "?"
                # Color by layer
                colors = ['#3498db', '#9b59b6', '#e74c3c', '#f39c12', '#1abc9c', '#34495e', '#e67e22']
                color = colors[node.layer % len(colors)]
                edge_color = '#2c3e50'

                circle = plt.Circle((x, y), 0.35, facecolor=color,
                                    edgecolor=edge_color, linewidth=2)
                ax.add_patch(circle)

                # Node label - show layer name and node ID
                label_text = layer_name[:10]  # Truncate long names
                ax.text(x, y, f"{label_text}\n#{node_id}", fontsize=8, fontweight='bold',
                       ha='center', va='center', color='white')

        # Add legend
        legend_elements = [
            mpatches.Patch(facecolor='#3498db', edgecolor='#2c3e50', label='Decision Node'),
            mpatches.Patch(facecolor='#27ae60', edgecolor='#229954', label='Terminal Node'),
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=10)

        # Labels
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlim(-max_width * 1.2, max_width * 1.2)
        ax.set_ylim(-len(layers) * 2.5 - 1, 1.5)
        ax.set_aspect('equal')
        ax.axis('off')

        # Add layer labels on the side
        for layer in range(len(mdd.dim_names)):
            layer_name = mdd.dim_names[layer]
            node_count = sum(1 for n in mdd.nodes if n.layer == layer)
            ax.text(-max_width * 1.1, -layer * 2.5,
                   f"Layer {layer}: {layer_name}\n({node_count} nodes)",
                   fontsize=9, va='center', ha='left',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='wheat', alpha=0.3))

        # Add statistics box
        stats_text = f"Nodes: {len(mdd.nodes)}\nArcs: {sum(len(n.edges) for n in mdd.nodes)}\nCompression: {compression_ratio:.1f}x"
        ax.text(-max_width * 1.1, 1, stats_text,
               fontsize=10, va='top', ha='left',
               bbox=dict(boxstyle='round,pad=0.8', facecolor='lightblue', alpha=0.5))

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            print(f"\nVisualization saved to: {save_path}")

        plt.close()

    # Draw the MDD
    vis_path = f"lanes_mdd_{compilation_method}.png"
    draw_mdd(mdd,
             title=f"Lanes MDD - {compilation_method.upper()} Method\n({size['nodes']} nodes, {size['arcs']} arcs, {compression_ratio:.1f}x compression)",
             save_path=vis_path,
             max_nodes=200)

    if size['nodes'] <= 200:
        print(f"Opening visualization: {vis_path}")
        import subprocess
        subprocess.run(['open', vis_path], check=False)

except ImportError as e:
    print(f"Visualization requires matplotlib: {e}")
    print("Install with: pip install matplotlib")
except Exception as e:
    print(f"Visualization error: {e}")

print()
print("=" * 70)
print("COMPLETE")
print("=" * 70)
print(f"MDD built successfully with {compilation_method.upper()} method")
print(f"Final size: {size['nodes']:,} nodes, {size['arcs']:,} arcs")
print()
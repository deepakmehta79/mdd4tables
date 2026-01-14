"""
Demo of Advanced MDD Visualization Methods

This script demonstrates multiple visualization approaches:
1. Hierarchical - Simple layer-based layout (default)
2. Force-directed - Physics-based spring layout (NetworkX)
3. Graphviz - Professional hierarchical layout
4. Interactive - Plotly-based interactive HTML
5. PyVis - Beautiful interactive network with physics

Usage:
    python examples/viz_demo.py hierarchical
    python examples/viz_demo.py force
    python examples/viz_demo.py graphviz
    python examples/viz_demo.py interactive
    python examples/viz_demo.py pyvis
    python examples/viz_demo.py all          # Create all visualizations
"""

import pandas as pd
import sys
import os

# Add parent directory to path to import mdd4tables
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mdd4tables import Schema, DimensionSpec, DimensionType, BuildConfig, Builder
from mdd4tables.viz_advanced import visualize_mdd

# Create sample dataset
print("=" * 70)
print("ADVANCED MDD VISUALIZATION DEMO")
print("=" * 70)

# Sample data: shipping lanes
data = {
    "LOB": ["IPHONE", "IPHONE", "IPAD", "IPAD", "WATCH", "WATCH", "ACCY", "ACCY"] * 3,
    "GEO": ["APAC", "EURO", "APAC", "EURO", "APAC", "EURO", "APAC", "EURO"] * 3,
    "MODE": ["AIR", "AIR", "OCEAN", "AIR", "AIR", "OCEAN", "AIR", "OCEAN"] * 3,
    "PRIORITY": ["HIGH", "LOW", "HIGH", "HIGH", "LOW", "LOW", "HIGH", "LOW"] * 3,
}

df = pd.DataFrame(data)
print(f"Dataset: {len(df)} rows, {len(df.columns)} columns")
print(f"Sample rows:\n{df.head()}\n")

# Build MDD
schema = Schema([
    DimensionSpec("LOB", DimensionType.CATEGORICAL),
    DimensionSpec("GEO", DimensionType.CATEGORICAL),
    DimensionSpec("MODE", DimensionType.CATEGORICAL),
    DimensionSpec("PRIORITY", DimensionType.CATEGORICAL),
])

cfg = BuildConfig(ordering="heuristic", compilation_method="slice")
mdd = Builder(schema, cfg).fit(df)

size = mdd.size()
print(f"MDD built: {size['nodes']} nodes, {size['arcs']} arcs")
print()

# Check command line argument
method = "all" if len(sys.argv) == 1 else sys.argv[1].lower()

if method not in ["hierarchical", "force", "graphviz", "interactive", "pyvis", "all"]:
    print(f"Unknown method: {method}")
    print("Valid methods: hierarchical, force, graphviz, interactive, pyvis, all")
    sys.exit(1)

methods_to_run = ["hierarchical", "force", "graphviz", "interactive", "pyvis"] if method == "all" else [method]

for viz_method in methods_to_run:
    print("=" * 70)
    print(f"VISUALIZATION METHOD: {viz_method.upper()}")
    print("=" * 70)

    title = f"Shipping Lanes MDD - {viz_method.capitalize()} Layout"
    save_path = f"mdd_viz_{viz_method}.png"

    try:
        print(f"Creating {viz_method} visualization...")
        visualize_mdd(mdd, method=viz_method, title=title,
                     save_path=save_path, max_nodes=100)
        print(f"✓ Success: {save_path}")

        # Open the file
        if viz_method != "interactive":  # Interactive creates HTML
            import subprocess
            subprocess.run(['open', save_path], check=False)

    except Exception as e:
        print(f"✗ Failed: {e}")

    print()

print("=" * 70)
print("DEMO COMPLETE")
print("=" * 70)
print("\nVisualization comparison:")
print("  - Hierarchical: Clean, simple, good for understanding layers")
print("  - Force-directed: Physics-based, good for seeing cluster patterns")
print("  - Graphviz: Professional, optimized hierarchical layout")
print("  - Interactive (Plotly): Hover for details, pan/zoom")
print("  - PyVis: Full physics simulation, draggable nodes, most interactive")
print("\nRecommendations:")
print("  - Small MDDs (< 50 nodes): Any method works well")
print("  - Medium MDDs (50-100 nodes): Force-directed, Graphviz, or PyVis")
print("  - Large MDDs (> 100 nodes): Hierarchical or Interactive only")
print("  - Presentations: Graphviz (cleanest) or PyVis (most impressive)")
print("  - Exploration: PyVis (best interactivity)")
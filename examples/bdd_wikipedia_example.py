'''
This example builds a BDD for a custom boolean function defined by the user.

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

Usage:
    python examples/bdd_wikipedia_example.py           # Default: trie method
    python examples/bdd_wikipedia_example.py slice     # Use slice method
    python examples/bdd_wikipedia_example.py trie      # Explicit trie method
'''

import pandas as pd
import numpy as np
import sys
from mdd4tables import Schema, DimensionSpec, DimensionType, BuildConfig, Builder

# Check command line argument for compilation method
compilation_method = "trie"  # default
if len(sys.argv) > 1:
    method = sys.argv[1].lower()
    if method in ["slice", "trie"]:
        compilation_method = method
    else:
        print(f"Unknown method '{method}'. Use 'trie' or 'slice'. Defaulting to trie.")

print(f"Using compilation method: {compilation_method.upper()}")
print("=" * 60)

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

# Build with selected method
if compilation_method == "slice":
    cfg = BuildConfig(ordering="fixed", compilation_method="slice")
else:
    cfg = BuildConfig(ordering="fixed", compilation_method="trie", enable_reduction=True)

mdd = Builder(schema, cfg).fit(df, order=["x1", "x2", "x3", "f"])

print(f"MDD Statistics: {mdd.size()}")
print(f"Dimension order: {mdd.dim_names}")
print()

# Show the structure
print("MDD Node Structure:")
print("-" * 60)
for i, node in enumerate(mdd.nodes):
    layer_name = mdd.dim_names[node.layer] if node.layer < len(mdd.dim_names) else "Terminal"
    edges_str = ", ".join(f"{k}->{v}" for k, v in sorted(node.edges.items()))
    term_info = f" [TERMINAL: {node.terminal_count} paths]" if node.terminal_count > 0 else ""
    print(f"Node {i} (layer {node.layer}: {layer_name}): edges=[{edges_str}]{term_info}")

print()
print("=" * 60)
print("Attempting visualization...")
print("=" * 60)

# Visualization
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    def draw_bdd_style(mdd, title="Binary Decision Diagram", save_path=None):
        """Draw MDD in classic BDD style with proper layout."""
        fig, ax = plt.subplots(figsize=(12, 10))

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
                x = (j - (width - 1) / 2) * 2.5
                y = -layer * 2  # Top to bottom
                pos[node_id] = (x, y)

        # Draw edges first (so they're behind nodes)
        for node_id, (x, y) in pos.items():
            node = mdd.nodes[node_id]
            for label, child_id in node.edges.items():
                cx, cy = pos[child_id]

                # Style based on label (0 = dashed, 1 = solid)
                linestyle = '-'
                color = 'black'
                label_color = 'black'

                # Draw edge
                ax.annotate("", xy=(cx, cy + 0.35), xytext=(x, y - 0.35),
                           arrowprops=dict(arrowstyle='->', color=color,
                                          linestyle=linestyle, lw=2))

                # Edge label
                mid_x, mid_y = (x + cx) / 2, (y + cy) / 2
                offset_x = 0.25 if label == 1 else -0.25
                ax.text(mid_x + offset_x, mid_y, str(label), fontsize=10,
                       fontweight='bold', color=label_color, ha='center', va='center')

        # Draw nodes
        for node_id, (x, y) in pos.items():
            node = mdd.nodes[node_id]

            if node.terminal_count > 0:
                # Terminal nodes - squares
                rect = mpatches.FancyBboxPatch((x - 0.35, y - 0.35), 0.7, 0.7,
                                               boxstyle="round,pad=0.05",
                                               facecolor='#f39c12', edgecolor='#d68910',
                                               linewidth=2)
                ax.add_patch(rect)
                # Show terminal count
                ax.text(x, y, f"T\n({node.terminal_count})", fontsize=9,
                       fontweight='bold', ha='center', va='center')
            else:
                # Decision nodes - circles
                layer_name = mdd.dim_names[node.layer] if node.layer < len(mdd.dim_names) else "?"
                circle = plt.Circle((x, y), 0.4, facecolor='#3498db',
                                    edgecolor='#2980b9', linewidth=2)
                ax.add_patch(circle)
                ax.text(x, y, layer_name, fontsize=11, fontweight='bold',
                       ha='center', va='center', color='white')

        # Add legend
        legend_elements = [
            mpatches.Patch(facecolor='#3498db', edgecolor='#2980b9', label='Decision Node'),
            mpatches.Patch(facecolor='#f39c12', edgecolor='#d68910', label='Terminal Node'),
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=9)

        # Labels
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.set_xlim(-max_width * 1.5, max_width * 1.5)
        ax.set_ylim(-len(layers) * 2 - 1, 1.5)
        ax.set_aspect('equal')
        ax.axis('off')

        # Add layer labels on the side
        for layer in range(len(mdd.dim_names)):
            layer_name = mdd.dim_names[layer]
            ax.text(-max_width * 1.3, -layer * 2, f"Layer {layer}: {layer_name}",
                   fontsize=10, va='center', ha='left', style='italic')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            print(f"Saved to: {save_path}")

        plt.show()

    # Draw the MDD
    draw_bdd_style(mdd, title=f"MDD for Custom Function f(x1,x2,x3) [{compilation_method.upper()}]",
                   save_path=f"bdd_majority_function_{compilation_method}.png")

except ImportError as e:
    print(f"Visualization requires matplotlib: {e}")
    print("Install with: pip install matplotlib")

# Also demonstrate queries
print()
print("=" * 60)
print("Query Examples:")
print("=" * 60)

# Check some specific inputs
test_cases = [
    {"x1": 0, "x2": 0, "x3": 0},  # Expected f=1
    {"x1": 0, "x2": 0, "x3": 1},  # Expected f=0
    {"x1": 1, "x2": 0, "x3": 1},  # Expected f=0
    {"x1": 0, "x2": 1, "x3": 1},  # Expected f=1
]

for tc in test_cases:
    matches = mdd.match(tc)
    print(f"Input: {tc} -> Output f: {[m['f'] for m in matches]}")

print()
print("All paths where f=1 (custom function true):")
for path in mdd.match({"f": 1}):
    print(f"  x1={path['x1']}, x2={path['x2']}, x3={path['x3']}")
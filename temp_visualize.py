'''
Binary Decision Diagram Example from Wikipedia

This example recreates the classic BDD example from Wikipedia:
https://en.wikipedia.org/wiki/Binary_decision_diagram

The function used is the majority function (also known as the voting function):
    f(x1, x2, x3) = (x1 AND x2) OR (x2 AND x3) OR (x1 AND x3)

This function outputs 1 if at least 2 of the 3 inputs are 1.

Truth table:
    x1  x2  x3  |  f
    0   0   0   |  0
    0   0   1   |  0
    0   1   0   |  0
    0   1   1   |  1
    1   0   0   |  0
    1   0   1   |  1
    1   1   0   |  1
    1   1   1   |  1

The MDD/BDD compresses this by sharing equivalent substructures. 
'''

import pandas as pd
import numpy as np
from mdd4tables import Schema, DimensionSpec, DimensionType, BuildConfig, Builder

# Create truth table for the majority function
# f(x1, x2, x3) = (x1 AND x2) OR (x2 AND x3) OR (x1 AND x3)
def majority(x1, x2, x3):
    return int((x1 and x2) or (x2 and x3) or (x1 and x3))

# Generate all combinations
rows = []
for x1 in [0, 1]:
    for x2 in [0, 1]:
        for x3 in [0, 1]:
            f = majority(x1, x2, x3)
            rows.append({"x1": x1, "x2": x2, "x3": x3, "f": f})

df = pd.DataFrame(rows)
print("Truth Table for Majority Function f(x1,x2,x3) = (x1∧x2) ∨ (x2∧x3) ∨ (x1∧x3):")
print(df.to_string(index=False))
print()

# Build MDD with fixed ordering x1 -> x2 -> x3 -> f
schema = Schema([
    DimensionSpec("x1", DimensionType.ORDINAL),
    DimensionSpec("x2", DimensionType.ORDINAL),
    DimensionSpec("x3", DimensionType.ORDINAL),
    DimensionSpec("f", DimensionType.ORDINAL),
])

# Build with reduction enabled (default)
mdd = Builder(schema, BuildConfig(ordering="fixed", enable_reduction=True)).fit(
    df, order=["x1", "x2", "x3", "f"]
)

print(f'MDD Statistics: {mdd.size()}')
print(f'Dimension order: {mdd.dim_names}')
print()

# Show the structure
print("MDD Node Structure:")
print("-" * 60)
for i, node in enumerate(mdd.nodes):
    layer_name = mdd.dim_names[node.layer] if node.layer < len(mdd.dim_names) else "Terminal"
    edges_str = ", ".join(f'{k}->{v}' for k, v in sorted(node.edges.items()))
    term_info = f' [TERMINAL: {node.terminal_count} paths]' if node.terminal_count > 0 else ""
    print(f'Node {i} (layer {node.layer}: {layer_name}): edges=[{edges_str}]{term_info}')

print()
print("=" * 60)
print("Attempting visualization...")
print("=" * 60)

# Visualization
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    def draw_bdd_style(mdd, title="Binary Decision Diagram", save_path=None):
        '''Draw MDD in classic BDD style with proper layout.'''
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
                ax.text(x, y, f'T\n({node.terminal_count})', fontsize=9,
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
            ax.text(-max_width * 1.3, -layer * 2, f'Layer {layer}: {layer_name}',
                   fontsize=10, va='center', ha='left', style='italic')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            print(f'Saved to: {save_path}')

        plt.show()

    # Draw the MDD
    draw_bdd_style(mdd, title="MDD for Majority Function: f(x1,x2,x3) = (x1∧x2) ∨ (x2∧x3) ∨ (x1∧x3)",
                   save_path="bdd_majority_function.png")

except ImportError as e:
    print(f'Visualization requires matplotlib: {e}')
    print("Install with: pip install matplotlib")

# Also demonstrate queries
print()
print("=" * 60)
print("Query Examples:")
print("=" * 60)

# Check some specific inputs
test_cases = [
    {"x1": 0, "x2": 0, "x3": 0},  # Expected f=0
    {"x1": 1, "x2": 1, "x3": 0},  # Expected f=1
    {"x1": 1, "x2": 1, "x3": 1},  # Expected f=1
]

for tc in test_cases:
    matches = mdd.match(tc)
    print(f'Input: {tc} -> Output f: {[m["f"] for m in matches]}')

print()
print("All paths where f=1 (majority true):")
for path in mdd.match({"f": 1}):
    print(f'  x1={path["x1"]}, x2={path["x2"]}, x3={path["x3"]}')
"""
Advanced MDD Visualization Module

Provides multiple visualization approaches:
1. Hierarchical (default) - Layer-based top-to-bottom
2. Force-directed - Physics-based spring layout
3. Graphviz - Professional hierarchical layout (requires graphviz)
4. Interactive - Plotly-based interactive visualization
5. PyVis - Beautiful interactive network with physics simulation
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from typing import Optional, Dict, List, Tuple

def visualize_mdd(mdd, method="hierarchical", title=None, save_path=None,
                  max_nodes=200, figsize=(16, 12), interactive=False):
    """
    Visualize MDD using various layout algorithms.

    Args:
        mdd: The MDD object to visualize
        method: Visualization method - "hierarchical", "force", "graphviz", "interactive", "pyvis"
        title: Title for the plot
        save_path: Path to save the visualization
        max_nodes: Maximum nodes to visualize (performance limit)
        figsize: Figure size tuple
        interactive: If True and method="force", create interactive plot
    """

    if len(mdd.nodes) > max_nodes:
        print(f"MDD has {len(mdd.nodes)} nodes, which is too large to visualize clearly.")
        print(f"Skipping visualization (max {max_nodes} nodes recommended).")
        return

    if method == "hierarchical":
        return _visualize_hierarchical(mdd, title, save_path, figsize)
    elif method == "force":
        return _visualize_force_directed(mdd, title, save_path, figsize, interactive)
    elif method == "graphviz":
        return _visualize_graphviz(mdd, title, save_path)
    elif method == "interactive":
        return _visualize_interactive_plotly(mdd, title, save_path)
    elif method == "pyvis":
        return _visualize_pyvis(mdd, title, save_path)
    else:
        raise ValueError(f"Unknown visualization method: {method}")


def _build_graph_structure(mdd):
    """Build graph structure from MDD for visualization."""
    # Group nodes by layer
    layers = {}
    for i, n in enumerate(mdd.nodes):
        layers.setdefault(n.layer, []).append(i)

    # Build edge list with weights
    edges = []
    for node_id in range(len(mdd.nodes)):
        node = mdd.nodes[node_id]
        for label, child_id in node.edges.items():
            weight = node.edge_counts.get(label, 1)
            edges.append((node_id, child_id, label, weight))

    return layers, edges


def _visualize_hierarchical(mdd, title, save_path, figsize):
    """Original hierarchical layout - simple and clean."""
    fig, ax = plt.subplots(figsize=figsize)

    layers, edges = _build_graph_structure(mdd)

    # Calculate positions - top to bottom layout
    pos = {}
    max_width = max(len(nodes) for nodes in layers.values())

    for layer, nodes in layers.items():
        width = len(nodes)
        for j, node_id in enumerate(nodes):
            x = (j - (width - 1) / 2) * 2.0
            y = -layer * 2.5
            pos[node_id] = (x, y)

    # Draw edges
    for node_id, child_id, label, weight in edges:
        x, y = pos[node_id]
        cx, cy = pos[child_id]

        # Edge thickness by weight
        max_weight = max(e[3] for e in edges)
        lw = 0.5 + 2.5 * (weight / max_weight)
        alpha = 0.3 + 0.5 * (weight / max_weight)

        ax.annotate("", xy=(cx, cy + 0.3), xytext=(x, y - 0.3),
                   arrowprops=dict(arrowstyle='->', color='gray',
                                  alpha=alpha, lw=lw))

        # Edge labels for small fan-out
        node = mdd.nodes[node_id]
        if len(node.edges) <= 4:
            mid_x, mid_y = (x + cx) / 2, (y + cy) / 2
            label_str = str(label)[:12]
            ax.text(mid_x + 0.2, mid_y, label_str, fontsize=7,
                   color='gray', ha='left', va='center', alpha=0.7)

    # Draw nodes
    colors = ['#3498db', '#9b59b6', '#e74c3c', '#f39c12', '#1abc9c', '#34495e', '#e67e22']
    for node_id, (x, y) in pos.items():
        node = mdd.nodes[node_id]

        if node.terminal_count > 0:
            rect = mpatches.FancyBboxPatch((x - 0.25, y - 0.25), 0.5, 0.5,
                                           boxstyle="round,pad=0.05",
                                           facecolor='#27ae60', edgecolor='#229954',
                                           linewidth=2)
            ax.add_patch(rect)
            ax.text(x, y, f"✓", fontsize=10, fontweight='bold',
                   ha='center', va='center', color='white')
        else:
            layer_name = mdd.dim_names[node.layer] if node.layer < len(mdd.dim_names) else "?"
            color = colors[node.layer % len(colors)]
            circle = plt.Circle((x, y), 0.35, facecolor=color,
                                edgecolor='#2c3e50', linewidth=2)
            ax.add_patch(circle)
            label_text = layer_name[:8]
            ax.text(x, y, label_text, fontsize=8, fontweight='bold',
                   ha='center', va='center', color='white')

    # Title and formatting
    if title:
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.set_xlim(-max_width * 1.2, max_width * 1.2)
    ax.set_ylim(-len(layers) * 2.5 - 1, 1.5)
    ax.set_aspect('equal')
    ax.axis('off')

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        print(f"Saved: {save_path}")
    plt.close()


def _visualize_force_directed(mdd, title, save_path, figsize, interactive):
    """Physics-based force-directed layout using NetworkX spring algorithm."""
    try:
        import networkx as nx
    except ImportError:
        print("Force-directed visualization requires networkx.")
        print("Install with: pip install networkx")
        return

    # Build NetworkX graph
    G = nx.DiGraph()

    # Add nodes with layer attribute
    for i, node in enumerate(mdd.nodes):
        G.add_node(i, layer=node.layer, terminal=node.terminal_count > 0)

    # Add weighted edges
    for node_id in range(len(mdd.nodes)):
        node = mdd.nodes[node_id]
        for label, child_id in node.edges.items():
            weight = node.edge_counts.get(label, 1)
            G.add_edge(node_id, child_id, weight=weight, label=label)

    # Spring layout with customization
    # Use layer as initial y-coordinate hint for better hierarchical structure
    pos_hint = {}
    layers, _ = _build_graph_structure(mdd)
    for layer, nodes in layers.items():
        for i, node_id in enumerate(nodes):
            x = (i - len(nodes)/2) * 0.3
            y = -layer * 2.0
            pos_hint[node_id] = np.array([x, y])

    # Spring layout with position hints
    pos = nx.spring_layout(G, pos=pos_hint, k=2.0, iterations=100,
                          weight='weight', seed=42, scale=5)

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Draw edges with varying width
    edges = G.edges(data=True)
    weights = [e[2]['weight'] for e in edges]
    max_weight = max(weights) if weights else 1

    for (u, v, data) in edges:
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        weight = data['weight']
        lw = 0.5 + 3.0 * (weight / max_weight)
        alpha = 0.3 + 0.5 * (weight / max_weight)

        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                   arrowprops=dict(arrowstyle='->', color='gray',
                                  alpha=alpha, lw=lw,
                                  connectionstyle="arc3,rad=0.1"))

    # Draw nodes
    colors = ['#3498db', '#9b59b6', '#e74c3c', '#f39c12', '#1abc9c', '#34495e', '#e67e22']
    for node_id in G.nodes():
        x, y = pos[node_id]
        node = mdd.nodes[node_id]

        if node.terminal_count > 0:
            circle = plt.Circle((x, y), 0.15, facecolor='#27ae60',
                                edgecolor='#229954', linewidth=2, zorder=3)
            ax.add_patch(circle)
            ax.text(x, y, "✓", fontsize=8, fontweight='bold',
                   ha='center', va='center', color='white', zorder=4)
        else:
            color = colors[node.layer % len(colors)]
            circle = plt.Circle((x, y), 0.2, facecolor=color,
                                edgecolor='#2c3e50', linewidth=2, zorder=3)
            ax.add_patch(circle)

    # Title and formatting
    if title:
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.axis('equal')
    ax.axis('off')

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        print(f"Saved: {save_path}")
    plt.close()


def _visualize_graphviz(mdd, title, save_path):
    """Professional hierarchical layout using Graphviz."""
    try:
        import networkx as nx
        from networkx.drawing.nx_agraph import graphviz_layout
    except ImportError:
        print("Graphviz visualization requires networkx and pygraphviz.")
        print("Install with: pip install networkx pygraphviz")
        print("Note: pygraphviz requires graphviz to be installed system-wide")
        print("  macOS: brew install graphviz")
        print("  Linux: sudo apt-get install graphviz graphviz-dev")
        return

    # Build NetworkX graph
    G = nx.DiGraph()

    # Add nodes
    for i, node in enumerate(mdd.nodes):
        layer_name = mdd.dim_names[node.layer] if node.layer < len(mdd.dim_names) else "T"
        label = f"{layer_name[:8]}\n#{i}"
        if node.terminal_count > 0:
            label = f"✓\n{node.terminal_count}"
        G.add_node(i, label=label, layer=node.layer)

    # Add edges
    for node_id in range(len(mdd.nodes)):
        node = mdd.nodes[node_id]
        for label, child_id in node.edges.items():
            weight = node.edge_counts.get(label, 1)
            G.add_edge(node_id, child_id, weight=weight, label=str(label)[:10])

    # Use graphviz dot layout
    try:
        pos = graphviz_layout(G, prog='dot')
    except Exception as e:
        print(f"Graphviz layout failed: {e}")
        print("Falling back to hierarchical layout...")
        return _visualize_hierarchical(mdd, title, save_path, (16, 12))

    # Draw
    fig, ax = plt.subplots(figsize=(16, 12))

    # Draw edges
    for (u, v, data) in G.edges(data=True):
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        weight = data.get('weight', 1)
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                   arrowprops=dict(arrowstyle='->', color='gray',
                                  lw=1.5, alpha=0.6))

    # Draw nodes
    colors = ['#3498db', '#9b59b6', '#e74c3c', '#f39c12', '#1abc9c', '#34495e', '#e67e22']
    for node_id in G.nodes():
        x, y = pos[node_id]
        node = mdd.nodes[node_id]

        if node.terminal_count > 0:
            circle = plt.Circle((x, y), 20, facecolor='#27ae60',
                                edgecolor='#229954', linewidth=2)
            ax.add_patch(circle)
        else:
            color = colors[node.layer % len(colors)]
            circle = plt.Circle((x, y), 25, facecolor=color,
                                edgecolor='#2c3e50', linewidth=2)
            ax.add_patch(circle)

    if title:
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.axis('equal')
    ax.axis('off')

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        print(f"Saved: {save_path}")
    plt.close()


def _visualize_interactive_plotly(mdd, title, save_path):
    """Interactive visualization using Plotly."""
    try:
        import plotly.graph_objects as go
        import networkx as nx
    except ImportError:
        print("Interactive visualization requires plotly and networkx.")
        print("Install with: pip install plotly networkx")
        return

    # Build NetworkX graph
    G = nx.DiGraph()
    for i, node in enumerate(mdd.nodes):
        G.add_node(i, layer=node.layer, terminal=node.terminal_count > 0)

    for node_id in range(len(mdd.nodes)):
        node = mdd.nodes[node_id]
        for label, child_id in node.edges.items():
            weight = node.edge_counts.get(label, 1)
            G.add_edge(node_id, child_id, weight=weight, label=str(label))

    # Layout
    pos = nx.spring_layout(G, k=2.0, iterations=50, seed=42)

    # Create edges
    edge_trace = []
    for (u, v, data) in G.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_trace.append(go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            mode='lines',
            line=dict(width=0.5 + data['weight']*0.5, color='#888'),
            hoverinfo='none',
            showlegend=False
        ))

    # Create nodes
    node_x = []
    node_y = []
    node_text = []
    node_color = []

    colors = ['#3498db', '#9b59b6', '#e74c3c', '#f39c12', '#1abc9c', '#34495e', '#e67e22']
    for node_id in G.nodes():
        x, y = pos[node_id]
        node_x.append(x)
        node_y.append(y)

        node = mdd.nodes[node_id]
        if node.terminal_count > 0:
            node_text.append(f"Terminal: {node.terminal_count} paths")
            node_color.append('#27ae60')
        else:
            layer_name = mdd.dim_names[node.layer] if node.layer < len(mdd.dim_names) else "?"
            node_text.append(f"Layer {node.layer}: {layer_name}<br>Node #{node_id}")
            node_color.append(colors[node.layer % len(colors)])

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        text=node_text,
        marker=dict(
            color=node_color,
            size=15,
            line=dict(width=2, color='#2c3e50')
        )
    )

    # Create figure
    fig = go.Figure(data=edge_trace + [node_trace],
                   layout=go.Layout(
                       title=dict(text=title or "Interactive MDD Visualization", font=dict(size=16)),
                       showlegend=False,
                       hovermode='closest',
                       margin=dict(b=0, l=0, r=0, t=40),
                       xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                       yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                   )

    if save_path:
        html_path = save_path.replace('.png', '.html')
        fig.write_html(html_path)
        print(f"Saved interactive visualization: {html_path}")
        print("Open in browser to interact with the graph.")

    fig.show()


def _visualize_pyvis(mdd, title, save_path):
    """
    Beautiful interactive network visualization using PyVis.

    Creates an HTML file with:
    - Physics simulation (nodes repel, edges attract)
    - Drag nodes to reposition
    - Click nodes for details
    - Zoom and pan
    - Configurable physics parameters
    """
    try:
        from pyvis.network import Network
    except ImportError:
        print("PyVis visualization requires pyvis.")
        print("Install with: pip install pyvis")
        return

    # Create PyVis network
    net = Network(
        height="900px",
        width="100%",
        bgcolor="#ffffff",
        font_color="#2c3e50",
        directed=True,
        notebook=False
    )

    # Configure physics for better layout
    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "hierarchicalRepulsion": {
          "centralGravity": 0.0,
          "springLength": 200,
          "springConstant": 0.01,
          "nodeDistance": 150,
          "damping": 0.09
        },
        "solver": "hierarchicalRepulsion",
        "stabilization": {
          "enabled": true,
          "iterations": 1000,
          "updateInterval": 25
        }
      },
      "layout": {
        "hierarchical": {
          "enabled": true,
          "direction": "UD",
          "sortMethod": "directed",
          "levelSeparation": 200,
          "nodeSpacing": 150,
          "treeSpacing": 200
        }
      }
    }
    """)

    # Color scheme by layer
    colors = ['#3498db', '#9b59b6', '#e74c3c', '#f39c12', '#1abc9c', '#34495e', '#e67e22']

    # Add nodes
    for node_id in range(len(mdd.nodes)):
        node = mdd.nodes[node_id]

        if node.terminal_count > 0:
            # Terminal node
            layer_name = "Terminal"
            color = '#27ae60'
            shape = 'box'
            label = f"✓ Terminal\n{node.terminal_count} paths"
            title = f"<b>Terminal Node</b><br>ID: {node_id}<br>Paths: {node.terminal_count}"
        else:
            # Decision node
            layer_name = mdd.dim_names[node.layer] if node.layer < len(mdd.dim_names) else "?"
            color = colors[node.layer % len(colors)]
            shape = 'dot'
            label = f"{layer_name}\n#{node_id}"

            # Build detailed hover info
            edge_info = "<br>".join([f"{lbl}: {node.edge_counts.get(lbl, 0)}"
                                     for lbl in list(node.edges.keys())[:5]])
            if len(node.edges) > 5:
                edge_info += f"<br>... and {len(node.edges) - 5} more"

            title = f"<b>Layer {node.layer}: {layer_name}</b><br>" \
                   f"Node ID: {node_id}<br>" \
                   f"Reach Count: {node.reach_count}<br>" \
                   f"Outgoing: {len(node.edges)} edges<br>" \
                   f"<hr><b>Top Edges:</b><br>{edge_info}"

        net.add_node(
            node_id,
            label=label,
            title=title,
            color=color,
            shape=shape,
            size=25 if node.terminal_count > 0 else 20,
            level=node.layer  # For hierarchical layout
        )

    # Add edges with labels and weights
    max_weight = max(
        (node.edge_counts.get(label, 1)
         for node_id, node in enumerate(mdd.nodes)
         for label in node.edges.keys()),
        default=1
    )

    for node_id in range(len(mdd.nodes)):
        node = mdd.nodes[node_id]
        for label, child_id in node.edges.items():
            weight = node.edge_counts.get(label, 1)

            # Edge width based on weight
            edge_width = 1 + 5 * (weight / max_weight)

            # Edge label (show only for significant edges or small fan-out)
            edge_label = str(label)[:20] if len(node.edges) <= 4 or weight > max_weight * 0.3 else ""

            # Hover title for edge
            edge_title = f"<b>{label}</b><br>Count: {weight}<br>From #{node_id} to #{child_id}"

            net.add_edge(
                node_id,
                child_id,
                label=edge_label,
                title=edge_title,
                width=edge_width,
                arrows="to",
                color={'color': '#888888', 'opacity': 0.6},
                smooth={'enabled': True, 'type': 'curvedCW', 'roundness': 0.2}
            )

    # Set title
    if title:
        net.heading = title

    # Save to HTML
    html_path = save_path.replace('.png', '.html') if save_path else 'mdd_pyvis.html'
    net.save_graph(html_path)

    print(f"Saved PyVis interactive visualization: {html_path}")
    print("Features:")
    print("  - Drag nodes to reposition")
    print("  - Hover for detailed info")
    print("  - Zoom with mouse wheel")
    print("  - Pan by dragging background")
    print("  - Physics simulation running")
    print("\nOpen in browser to explore!")

    # Try to open in browser
    try:
        import webbrowser
        webbrowser.open(f'file://{html_path}')
    except Exception:
        print(f"Couldn't auto-open. Manually open: {html_path}")
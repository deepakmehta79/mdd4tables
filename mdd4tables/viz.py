from __future__ import annotations
from typing import Any, Dict, Optional
from .mdd import MDD

def to_networkx(mdd: MDD):
    try:
        import networkx as nx
    except ImportError as e:
        raise ImportError("Install extra 'viz': pip install mdd4tables[viz]") from e

    G = nx.DiGraph()
    for i, n in enumerate(mdd.nodes):
        G.add_node(i, layer=n.layer, reach=n.reach_count, terminal=n.terminal_count)
        for lab, ch in n.edges.items():
            G.add_edge(i, ch, label=str(lab), count=n.edge_counts.get(lab, 0))
    return G

def draw(mdd: MDD, max_nodes: int = 500, show_edge_labels: bool = True, figsize: Optional[tuple] = None):
    try:
        import matplotlib.pyplot as plt
    except ImportError as e:
        raise ImportError("Install extra 'viz': pip install mdd4tables[viz]") from e

    G = to_networkx(mdd)
    if G.number_of_nodes() > max_nodes:
        raise ValueError(f"Too many nodes to draw ({G.number_of_nodes()}); increase max_nodes or filter.")

    # simple layered layout
    layers = {}
    for node, data in G.nodes(data=True):
        layers.setdefault(data["layer"], []).append(node)

    pos = {}
    for layer, nodes in layers.items():
        for j, node in enumerate(nodes):
            pos[node] = (layer * 3, -j * 2)

    if figsize is None:
        figsize = (min(16, 3 + mdd.terminal_layer*3), max(8, len(mdd.nodes) * 0.5))

    plt.figure(figsize=figsize)
    import networkx as nx

    # Draw nodes with labels showing node ID
    node_colors = ['lightblue' if mdd.nodes[n].terminal_count > 0 else 'lightgray' for n in G.nodes()]
    nx.draw_networkx_nodes(G, pos, node_size=500, node_color=node_colors)
    nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')

    # Draw edges
    nx.draw_networkx_edges(G, pos, arrows=True, arrowsize=15, arrowstyle='->',
                          edge_color='gray', width=1.5)

    # Draw edge labels with arc label and count
    if show_edge_labels:
        edge_labels = {}
        for u, v, data in G.edges(data=True):
            label = data['label']
            count = data['count']
            edge_labels[(u, v)] = f"{label}\n({count})"
        nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=7)

    # Add layer labels
    for layer in range(mdd.terminal_layer + 1):
        if layer < len(mdd.dim_names):
            plt.text(layer * 3, max([-j * 2 for j in range(len(layers.get(layer, [])))]) + 1.5,
                    mdd.dim_names[layer], fontsize=10, fontweight='bold', ha='center')
        else:
            plt.text(layer * 3, max([-j * 2 for j in range(len(layers.get(layer, [])))]) + 1.5,
                    'Terminal', fontsize=10, fontweight='bold', ha='center')

    plt.title(f"MDD: {mdd.size()['nodes']} nodes, {mdd.size()['arcs']} arcs", fontsize=12)
    plt.axis('off')
    plt.tight_layout()
    plt.show()

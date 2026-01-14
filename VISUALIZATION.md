# Advanced MDD Visualization

This document describes the advanced visualization methods available for Multi-Valued Decision Diagrams (MDDs).

## Available Visualization Methods

### 1. Hierarchical Layout (Default)
**Best for:** Understanding layer structure, presentations

```python
from mdd4tables.viz_advanced import visualize_mdd

visualize_mdd(mdd, method="hierarchical",
              title="My MDD",
              save_path="output.png")
```

**Features:**
- Clean, simple top-to-bottom layout
- Nodes organized by layers
- Edge thickness based on arc counts
- Color-coded by layer
- Edge labels for low fan-out nodes

**Dependencies:** matplotlib (included)

---

### 2. Force-Directed Layout (Physics-Based)
**Best for:** Discovering cluster patterns, understanding node relationships

```python
visualize_mdd(mdd, method="force",
              title="Force-Directed MDD",
              save_path="force.png")
```

**Features:**
- Physics-based spring layout algorithm
- Nodes repel each other, edges attract
- Natural clustering of related nodes
- Uses layer hints for better hierarchical preservation
- Curved edges to avoid overlaps

**Dependencies:** matplotlib, networkx

```bash
pip install networkx
```

---

### 3. Graphviz Layout (Professional)
**Best for:** Publications, professional presentations

```python
visualize_mdd(mdd, method="graphviz",
              title="Graphviz MDD",
              save_path="graphviz.png")
```

**Features:**
- Professional hierarchical layout using Graphviz's DOT algorithm
- Optimized edge routing to minimize crossings
- Clean, publication-quality output
- Falls back to hierarchical if graphviz not available

**Dependencies:** matplotlib, networkx, pygraphviz, graphviz (system)

```bash
# macOS
brew install graphviz
pip install networkx pygraphviz

# Linux
sudo apt-get install graphviz graphviz-dev
pip install networkx pygraphviz
```

---

### 4. Interactive Layout (Plotly)
**Best for:** Exploration, presentations, web embedding

```python
visualize_mdd(mdd, method="interactive",
              title="Interactive MDD",
              save_path="interactive.png")  # Creates .html file
```

**Features:**
- Interactive HTML visualization
- Hover over nodes for details
- Pan and zoom
- Drag nodes to reposition
- Can be embedded in web pages
- Creates standalone HTML file

**Dependencies:** matplotlib, networkx, plotly

```bash
pip install plotly networkx
```

---

## Quick Start

### Demo Script

```bash
# Try all methods
python examples/viz_demo.py all

# Or individual methods
python examples/viz_demo.py hierarchical
python examples/viz_demo.py force
python examples/viz_demo.py graphviz
python examples/viz_demo.py interactive
```

### In Your Code

```python
from mdd4tables import Schema, DimensionSpec, DimensionType, Builder, BuildConfig
from mdd4tables.viz_advanced import visualize_mdd
import pandas as pd

# Build your MDD
df = pd.DataFrame(...)
schema = Schema([...])
mdd = Builder(schema, BuildConfig()).fit(df)

# Visualize with different methods
visualize_mdd(mdd, method="hierarchical", save_path="hier.png")
visualize_mdd(mdd, method="force", save_path="force.png")
visualize_mdd(mdd, method="interactive", save_path="interactive.png")
```

---

## Recommendations by MDD Size

| MDD Size | Recommended Methods | Notes |
|----------|-------------------|-------|
| **Small** (< 50 nodes) | Any method works well | Force-directed shows nice patterns |
| **Medium** (50-100 nodes) | Force, Graphviz, Interactive | Hierarchical may be cluttered |
| **Large** (100-200 nodes) | Hierarchical, Interactive | Force-directed may be slow |
| **Very Large** (> 200 nodes) | Hierarchical only (with max_nodes limit) | Others become unreadable |

---

## Comparison Table

| Feature | Hierarchical | Force-Directed | Graphviz | Interactive |
|---------|-------------|---------------|----------|-------------|
| **Setup** | None (default) | pip install networkx | System graphviz required | pip install plotly networkx |
| **Speed** | ⚡⚡⚡ Fast | ⚡⚡ Medium | ⚡⚡ Medium | ⚡ Slow |
| **Clarity** | ⭐⭐⭐⭐ Excellent | ⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ Best | ⭐⭐⭐ Good |
| **Patterns** | ⭐⭐ Limited | ⭐⭐⭐⭐ Excellent | ⭐⭐⭐ Good | ⭐⭐⭐⭐ Excellent |
| **Interactive** | ❌ No | ❌ No | ❌ No | ✅ Yes |
| **Publication** | ⭐⭐⭐ Good | ⭐⭐ Fair | ⭐⭐⭐⭐⭐ Best | ⭐⭐ Fair |
| **Web Ready** | ❌ No | ❌ No | ❌ No | ✅ Yes |

---

## Advanced Options

### Custom Sizing
```python
visualize_mdd(mdd, method="force",
              figsize=(20, 16),  # Larger figure
              max_nodes=300)     # Allow more nodes
```

### No Auto-Open
```python
# Files are saved but not automatically opened
# Just navigate to the file manually
```

### Batch Visualization
```python
methods = ["hierarchical", "force", "interactive"]
for method in methods:
    visualize_mdd(mdd, method=method,
                  title=f"{method.capitalize()} Layout",
                  save_path=f"mdd_{method}.png")
```

---

## Output Files

- **Hierarchical/Force/Graphviz**: PNG images (150 DPI)
- **Interactive**: HTML file (can be 4-10MB due to embedded Plotly library)

---

## Troubleshooting

### "Force-directed visualization requires networkx"
```bash
pip install networkx
```

### "Graphviz visualization requires networkx and pygraphviz"
```bash
# macOS
brew install graphviz
pip install networkx pygraphviz

# Linux
sudo apt-get install graphviz graphviz-dev
pip install networkx pygraphviz
```

### "Interactive visualization requires plotly"
```bash
pip install plotly networkx
```

### Visualization too cluttered
- Use `max_nodes` parameter to limit size
- Try force-directed layout for better spacing
- Consider filtering your data before building MDD

### Interactive HTML won't open automatically
- The file is still saved
- Open manually: `open mdd_viz_interactive.html`
- Or just open in your browser

---

## Examples Gallery

See `examples/viz_demo.py` for a complete working example that generates all visualization types.

---

## Implementation Details

All visualization methods are in `/Users/macbook/Downloads/mdd4tables/mdd4tables/viz_advanced.py`.

### Key Features:
- Unified API across all methods
- Automatic fallback for missing dependencies
- Color-coding by layer (consistent across methods)
- Edge weight visualization
- Terminal node highlighting
- Configurable size limits

---

## Credits

- **Hierarchical**: Custom matplotlib implementation
- **Force-Directed**: NetworkX spring_layout algorithm
- **Graphviz**: AT&T Graphviz DOT algorithm via pygraphviz
- **Interactive**: Plotly graph visualization library
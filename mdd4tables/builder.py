from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from .schema import Schema, DimensionType
from .config import BuildConfig
from .binning import fit_binner, BinModel
from .mdd import MDD, Node
from .slice_compile import SliceCompiler

@dataclass
class Builder:
    schema: Schema
    config: BuildConfig = BuildConfig()

    def fit(self, df: pd.DataFrame, order: Optional[List[str]] = None) -> MDD:
        self.schema.validate(df.columns)

        # decide ordering
        dim_names = order or self.schema.names()
        if self.config.ordering != "fixed" and order is None:
            from .ordering import propose_order, search_order
            if self.config.ordering == "search":
                dim_names = search_order(df, self.schema, self.config.ordering_config).order
            else:
                dim_names = propose_order(df, self.schema, self.config.ordering_config).order

        schema = self.schema.subset(dim_names)

        # fit bin models for numeric dims
        bin_models: Dict[str, BinModel] = {}
        working = df.copy()
        for d in schema.dims:
            if d.dtype == DimensionType.NUMERIC:
                bins_cfg = d.bins or self.config.default_numeric_bins or {"strategy":"quantile","k":10}
                b = fit_binner(working[d.name].astype(float), bins_cfg,
                               missing_token=d.missing_token)
                bin_models[d.name] = b
                working[d.name] = b.transform(working[d.name].astype(float))
            else:
                # normalize missing
                working[d.name] = working[d.name].where(~working[d.name].isna(), other=d.missing_token)

        # Choose compilation method
        if self.config.compilation_method == "slice":
            # Slice-based incremental compilation (Nicholson-Bridge-Wilson 2006)
            compiler = SliceCompiler(schema=schema, dim_names=dim_names)
            nodes, root, terminal_layer = compiler.compile(working)
        else:
            # Traditional trie construction followed by optional reduction
            nodes, root, terminal_layer = self._build_trie(working, dim_names)
            if self.config.enable_reduction:
                nodes, root = self._reduce(nodes, terminal_layer)

        return MDD(dim_names=dim_names, nodes=nodes, root=root, terminal_layer=terminal_layer,
                   laplace_alpha=self.config.laplace_alpha, bin_models=bin_models)

    def _build_trie(self, working: pd.DataFrame, dim_names: List[str]) -> Tuple[List[Node], int, int]:
        """Build an uncompressed trie from the data.

        Returns:
            (nodes, root, terminal_layer)
        """
        nodes: List[Node] = []
        root = 0
        nodes.append(Node(layer=0, edges={}, edge_counts={}, reach_count=0, terminal_count=0))

        # insert each row as a path (using itertuples for performance)
        for row in working[dim_names].itertuples(index=False, name=None):
            nid = root
            nodes[nid].reach_count += 1
            for layer, v in enumerate(row):
                n = nodes[nid]
                if v in n.edges:
                    child = n.edges[v]
                    n.edge_counts[v] = n.edge_counts.get(v, 0) + 1
                else:
                    child = len(nodes)
                    n.edges[v] = child
                    n.edge_counts[v] = n.edge_counts.get(v, 0) + 1
                    nodes.append(Node(layer=layer+1, edges={}, edge_counts={}, reach_count=0, terminal_count=0))
                nid = child
                nodes[nid].reach_count += 1
            nodes[nid].terminal_count += 1

        terminal_layer = len(dim_names)
        return nodes, root, terminal_layer

    def _reduce(self, nodes: List[Node], terminal_layer: int) -> Tuple[List[Node], int]:
        """Bottom-up reduction by merging equivalent nodes within same layer.

        Nodes are considered equivalent if they have identical structure:
        - Same layer
        - Same outgoing edges (label -> child mapping after remapping)
        - Same terminal_count (for terminal nodes)

        Note: reach_count and edge_counts are NOT part of the signature because
        they are context-dependent. When merging nodes, we aggregate these counts.
        """
        # group node ids by layer
        by_layer: List[List[int]] = [[] for _ in range(terminal_layer+1)]
        for i, n in enumerate(nodes):
            if n.layer <= terminal_layer:
                by_layer[n.layer].append(i)

        # mapping old->new
        old_to_new: Dict[int, int] = {}

        new_nodes: List[Node] = []

        # Track which old nodes map to each new node (for aggregating counts)
        new_to_old_list: Dict[int, List[int]] = {}

        # signature: structural identity (excludes counts which get aggregated)
        sig_map: Dict[Tuple, int] = {}

        for layer in range(terminal_layer, -1, -1):
            sig_map.clear()
            for nid in by_layer[layer]:
                n = nodes[nid]
                # rewrite children ids to new ids (for layers below already processed)
                if layer < terminal_layer:
                    remapped_edges = {lab: old_to_new[ch] for lab, ch in n.edges.items()}
                else:
                    remapped_edges = dict(n.edges)  # should be empty

                # Signature: structural identity only (layer, terminal_count, edge structure)
                # Edge counts are excluded - they get aggregated when nodes merge
                items = tuple(sorted((lab, remapped_edges[lab]) for lab in remapped_edges))
                sig = (layer, n.terminal_count, items)

                if sig in sig_map:
                    rep = sig_map[sig]
                    old_to_new[nid] = rep
                    new_to_old_list[rep].append(nid)
                else:
                    rep = len(new_nodes)
                    sig_map[sig] = rep
                    old_to_new[nid] = rep
                    new_to_old_list[rep] = [nid]
                    new_nodes.append(Node(layer=layer, edges=remapped_edges, edge_counts={},
                                          reach_count=0, terminal_count=n.terminal_count))

        # Aggregate counts for merged nodes
        for new_id, old_ids in new_to_old_list.items():
            new_node = new_nodes[new_id]
            for old_id in old_ids:
                old_node = nodes[old_id]
                new_node.reach_count += old_node.reach_count
                for lab, count in old_node.edge_counts.items():
                    new_node.edge_counts[lab] = new_node.edge_counts.get(lab, 0) + count

        # new_nodes were appended in reverse-layer order; reorder by layer ascending for readability
        # (optional). We'll rebuild a stable list and remap ids.
        layer_groups: Dict[int, List[int]] = {}
        for i, n in enumerate(new_nodes):
            layer_groups.setdefault(n.layer, []).append(i)
        ordered_old_ids = []
        for layer in range(0, terminal_layer+1):
            ordered_old_ids.extend(layer_groups.get(layer, []))

        id_map = {old: new for new, old in enumerate(ordered_old_ids)}
        final_nodes: List[Node] = []
        for old in ordered_old_ids:
            n = new_nodes[old]
            edges = {lab: id_map[ch] for lab, ch in n.edges.items()}
            final_nodes.append(Node(layer=n.layer, edges=edges, edge_counts=dict(n.edge_counts),
                                    reach_count=n.reach_count, terminal_count=n.terminal_count))

        # compute new root id
        # root was old node 0 -> old_to_new[0] in new_nodes space -> id_map -> final
        root_new_nodes = old_to_new[0]
        root_final = id_map[root_new_nodes]
        return final_nodes, root_final

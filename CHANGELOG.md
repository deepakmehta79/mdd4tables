# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial public release
- Multi-Valued Decision Diagram (MDD) construction from tabular data
- Two compilation methods: trie-then-reduce and incremental slice-based
- Three dimension ordering strategies: fixed, heuristic, budgeted search
- Query operations: exists, match, complete, nearest, count
- Conditional probability computation with Laplace smoothing
- Numeric binning support (quantile and fixed-width strategies)
- Advanced visualization module with 5 methods:
  - Hierarchical layout (matplotlib)
  - Force-directed layout (NetworkX)
  - Graphviz DOT layout
  - Interactive Plotly visualizations
  - PyVis physics-based interactive networks
- Comprehensive test suite
- Example scripts for BDD and shipping lanes data

## [0.1.0] - 2025-01-14

### Added
- Initial development version
- Core MDD data structure with node compression
- Builder with configurable construction pipeline
- Schema definition for mixed-type dimensions
- Basic query methods
- Example notebooks and scripts
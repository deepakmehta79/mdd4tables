"""Comprehensive tests for mdd4tables library."""
import pytest
import pandas as pd
import numpy as np
from mdd4tables import Schema, DimensionSpec, DimensionType, BuildConfig, Builder, OrderingConfig


# ==============================================================================
# Basic Build and Exists Tests
# ==============================================================================

def test_build_and_exists():
    """Test basic MDD construction and exists query."""
    df = pd.DataFrame({
        "a": ["x", "x", "y"],
        "b": [1, 2, 1],
    })
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema, BuildConfig(ordering="fixed")).fit(df, order=["a", "b"])
    assert mdd.exists({"a": "x", "b": 1})
    assert mdd.exists({"a": "x", "b": 2})
    assert mdd.exists({"a": "y", "b": 1})
    assert not mdd.exists({"a": "z", "b": 1})
    assert not mdd.exists({"a": "y", "b": 2})


def test_exists_missing_dimension():
    """Test exists returns False when dimension is missing."""
    df = pd.DataFrame({"a": ["x"], "b": [1]})
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema).fit(df)
    assert not mdd.exists({"a": "x"})  # Missing "b"
    assert not mdd.exists({"b": 1})    # Missing "a"
    assert not mdd.exists({})          # Missing all


# ==============================================================================
# Complete Tests
# ==============================================================================

def test_complete():
    """Test completion query with partial input."""
    df = pd.DataFrame({
        "a": ["x", "x", "y", "y", "y"],
        "b": [1, 1, 2, 2, 3],
    })
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema).fit(df)
    out = mdd.complete({"a": "y"}, k=2)
    assert len(out) >= 1
    # All results should have a="y"
    for r in out:
        assert r.path["a"] == "y"


def test_complete_empty_result():
    """Test complete returns empty list when no matches."""
    df = pd.DataFrame({"a": ["x"], "b": [1]})
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema).fit(df)
    out = mdd.complete({"a": "nonexistent"}, k=5)
    assert out == []


def test_complete_no_constraints():
    """Test complete with empty partial returns top paths."""
    df = pd.DataFrame({
        "a": ["x", "x", "x", "y"],
        "b": [1, 1, 1, 2],
    })
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema).fit(df)
    out = mdd.complete({}, k=10)
    assert len(out) == 2  # Two distinct paths


# ==============================================================================
# Match Tests
# ==============================================================================

def test_match_with_wildcard():
    """Test pattern matching with wildcards."""
    df = pd.DataFrame({
        "a": ["x", "x", "y"],
        "b": [1, 2, 1],
    })
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema).fit(df)

    # Match all paths with a="x"
    results = mdd.match({"a": "x"})
    assert len(results) == 2
    for r in results:
        assert r["a"] == "x"

    # Match all paths (empty pattern)
    all_paths = mdd.match({})
    assert len(all_paths) == 3


def test_match_with_limit():
    """Test match respects limit parameter."""
    df = pd.DataFrame({
        "a": ["x"] * 100,
        "b": list(range(100)),
    })
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema).fit(df)
    results = mdd.match({}, limit=10)
    assert len(results) == 10


# ==============================================================================
# Count Tests
# ==============================================================================

def test_count_all():
    """Test count without pattern returns total paths."""
    df = pd.DataFrame({
        "a": ["x", "x", "y", "y", "y"],
        "b": [1, 2, 1, 2, 3],
    })
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema).fit(df)
    assert mdd.count() == 5
    assert mdd.count({}) == 5


def test_count_with_pattern():
    """Test count with pattern constraint."""
    df = pd.DataFrame({
        "a": ["x", "x", "y", "y", "y"],
        "b": [1, 2, 1, 2, 3],
    })
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema).fit(df)
    assert mdd.count({"a": "x"}) == 2
    assert mdd.count({"a": "y"}) == 3
    assert mdd.count({"b": 1}) == 2
    assert mdd.count({"a": "x", "b": 1}) == 1


def test_count_no_match():
    """Test count returns 0 when no paths match."""
    df = pd.DataFrame({"a": ["x"], "b": [1]})
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema).fit(df)
    assert mdd.count({"a": "nonexistent"}) == 0


# ==============================================================================
# Nearest Tests
# ==============================================================================

def test_nearest_basic():
    """Test nearest query with distance function."""
    df = pd.DataFrame({
        "a": ["x", "x", "y"],
        "b": [1, 5, 3],
    })
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema).fit(df)

    def ordinal_dist(a, b):
        return abs(int(a) - int(b))

    results = mdd.nearest({"b": 4}, dist_fns={"b": ordinal_dist}, k=3)
    assert len(results) >= 1
    # First result should be closest (b=5 or b=3, distance=1)
    assert results[0].details["distance"] == 1.0


def test_nearest_no_dist_fn():
    """Test nearest uses default distance when no function provided."""
    df = pd.DataFrame({
        "a": ["x", "y"],
        "b": [1, 2],
    })
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema).fit(df)
    results = mdd.nearest({"a": "x"}, dist_fns={}, k=2)
    # Should find path with a="x" with distance 0
    assert any(r.path["a"] == "x" and r.details["distance"] == 0.0 for r in results)


# ==============================================================================
# Numeric Binning Tests
# ==============================================================================

def test_numeric_binning_quantile():
    """Test quantile binning for numeric dimensions."""
    df = pd.DataFrame({
        "cat": ["a", "b", "c", "d"],
        "num": [1.0, 2.0, 3.0, 4.0],
    })
    schema = Schema([
        DimensionSpec("cat", DimensionType.CATEGORICAL),
        DimensionSpec("num", DimensionType.NUMERIC, bins={"strategy": "quantile", "k": 2}),
    ])
    mdd = Builder(schema).fit(df)
    assert mdd.size()["nodes"] > 0
    assert "num" in mdd.bin_models


def test_numeric_binning_fixed_width():
    """Test fixed-width binning for numeric dimensions."""
    df = pd.DataFrame({
        "cat": ["a", "b", "c", "d"],
        "num": [0.0, 25.0, 50.0, 100.0],
    })
    schema = Schema([
        DimensionSpec("cat", DimensionType.CATEGORICAL),
        DimensionSpec("num", DimensionType.NUMERIC, bins={"strategy": "fixed_width", "k": 4}),
    ])
    mdd = Builder(schema).fit(df)
    assert mdd.size()["nodes"] > 0
    assert mdd.bin_models["num"].strategy == "fixed_width"


def test_numeric_with_missing():
    """Test numeric binning handles NaN values."""
    df = pd.DataFrame({
        "cat": ["a", "b", "c"],
        "num": [1.0, np.nan, 3.0],
    })
    schema = Schema([
        DimensionSpec("cat", DimensionType.CATEGORICAL),
        DimensionSpec("num", DimensionType.NUMERIC, bins={"strategy": "quantile", "k": 2}),
    ])
    mdd = Builder(schema).fit(df)
    # Should handle NaN gracefully
    assert mdd.count() == 3


def test_numeric_custom_missing_token():
    """Test custom missing token for numeric dimension."""
    df = pd.DataFrame({
        "num": [1.0, np.nan, 3.0],
    })
    schema = Schema([
        DimensionSpec("num", DimensionType.NUMERIC,
                     bins={"strategy": "quantile", "k": 2},
                     missing_token="NA"),
    ])
    mdd = Builder(schema).fit(df)
    # Verify missing token is used in bin model
    assert mdd.bin_models["num"].missing_token == "NA"


# ==============================================================================
# Missing Value Tests
# ==============================================================================

def test_categorical_missing_values():
    """Test handling of missing values in categorical columns."""
    df = pd.DataFrame({
        "a": ["x", None, "y"],
        "b": [1, 2, 3],
    })
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema).fit(df)
    assert mdd.count() == 3
    # Should have a path with missing token
    assert mdd.exists({"a": "__MISSING__", "b": 2})


def test_custom_missing_token():
    """Test custom missing token is used."""
    df = pd.DataFrame({
        "a": ["x", None],
        "b": [1, 2],
    })
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL, missing_token="N/A"),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema).fit(df)
    assert mdd.exists({"a": "N/A", "b": 2})


# ==============================================================================
# Ordering Tests
# ==============================================================================

def test_heuristic_ordering():
    """Test heuristic ordering produces valid MDD."""
    df = pd.DataFrame({
        "high_card": list(range(100)),
        "low_card": ["a", "b"] * 50,
    })
    schema = Schema([
        DimensionSpec("high_card", DimensionType.ORDINAL),
        DimensionSpec("low_card", DimensionType.CATEGORICAL),
    ])
    mdd = Builder(schema, BuildConfig(ordering="heuristic")).fit(df)
    assert mdd.count() == 100
    # Heuristic should put low_card first
    assert mdd.dim_names[0] == "low_card"


def test_search_ordering():
    """Test search ordering produces valid MDD."""
    df = pd.DataFrame({
        "a": ["x", "y", "z"] * 10,
        "b": list(range(30)),
    })
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    cfg = BuildConfig(
        ordering="search",
        ordering_config=OrderingConfig(max_evals=20, time_budget_s=0.5)
    )
    mdd = Builder(schema, cfg).fit(df)
    assert mdd.count() == 30


def test_fixed_ordering():
    """Test fixed ordering respects provided order."""
    df = pd.DataFrame({
        "a": ["x", "y"],
        "b": [1, 2],
    })
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema, BuildConfig(ordering="fixed")).fit(df, order=["b", "a"])
    assert mdd.dim_names == ["b", "a"]


# ==============================================================================
# Reduction Tests
# ==============================================================================

def test_reduction_merges_equivalent_nodes():
    """Test that reduction merges structurally equivalent subtrees."""
    # Create data where reduction should merge terminals
    df = pd.DataFrame({
        "a": ["x", "y"],
        "b": [1, 1],  # Same value leads to same terminal structure
    })
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd_reduced = Builder(schema, BuildConfig(enable_reduction=True)).fit(df)
    mdd_unreduced = Builder(schema, BuildConfig(enable_reduction=False)).fit(df)

    # Reduced should have fewer or equal nodes
    assert mdd_reduced.size()["nodes"] <= mdd_unreduced.size()["nodes"]


def test_reduction_preserves_counts():
    """Test that reduction correctly aggregates counts."""
    df = pd.DataFrame({
        "a": ["x", "x", "y", "y"],
        "b": [1, 1, 1, 1],
    })
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema, BuildConfig(enable_reduction=True)).fit(df)

    # Total count should be preserved
    assert mdd.count() == 4

    # Counts per prefix should be preserved
    assert mdd.count({"a": "x"}) == 2
    assert mdd.count({"a": "y"}) == 2


def test_reduction_disabled():
    """Test that reduction can be disabled."""
    df = pd.DataFrame({
        "a": ["x", "y"],
        "b": [1, 1],
    })
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema, BuildConfig(enable_reduction=False)).fit(df)
    # Without reduction, each path creates separate nodes
    assert mdd.size()["nodes"] >= 4  # At least root + 2 layer1 + 2 terminals


# ==============================================================================
# Edge Cases
# ==============================================================================

def test_single_row():
    """Test MDD with single row."""
    df = pd.DataFrame({"a": ["x"], "b": [1]})
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema).fit(df)
    assert mdd.exists({"a": "x", "b": 1})
    assert mdd.count() == 1


def test_single_column():
    """Test MDD with single dimension."""
    df = pd.DataFrame({"a": ["x", "y", "z"]})
    schema = Schema([DimensionSpec("a", DimensionType.CATEGORICAL)])
    mdd = Builder(schema).fit(df)
    assert mdd.count() == 3
    assert mdd.size()["layers"] == 1


def test_duplicate_rows():
    """Test MDD handles duplicate rows correctly."""
    df = pd.DataFrame({
        "a": ["x", "x", "x"],
        "b": [1, 1, 1],
    })
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema).fit(df)
    # Should have 3 paths but possibly merged structure
    assert mdd.count() == 3


def test_many_dimensions():
    """Test MDD with many dimensions."""
    n_dims = 10
    df = pd.DataFrame({f"d{i}": ["a", "b"] for i in range(n_dims)})
    schema = Schema([
        DimensionSpec(f"d{i}", DimensionType.CATEGORICAL)
        for i in range(n_dims)
    ])
    mdd = Builder(schema).fit(df)
    assert mdd.size()["layers"] == n_dims


def test_constant_column():
    """Test MDD with column having single unique value."""
    df = pd.DataFrame({
        "a": ["x", "x", "x"],
        "b": [1, 2, 3],
    })
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema).fit(df)
    assert mdd.count() == 3


def test_all_unique_rows():
    """Test MDD where every row is unique."""
    df = pd.DataFrame({
        "a": ["x", "y", "z"],
        "b": [1, 2, 3],
    })
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema).fit(df)
    assert mdd.count() == 3


# ==============================================================================
# Input Validation Tests
# ==============================================================================

def test_invalid_k_in_complete():
    """Test complete raises error for invalid k."""
    df = pd.DataFrame({"a": ["x"], "b": [1]})
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema).fit(df)

    with pytest.raises(ValueError):
        mdd.complete({}, k=0)

    with pytest.raises(ValueError):
        mdd.complete({}, k=-1)


def test_invalid_beam_in_complete():
    """Test complete raises error for invalid beam."""
    df = pd.DataFrame({"a": ["x"], "b": [1]})
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema).fit(df)

    with pytest.raises(ValueError):
        mdd.complete({}, beam=0)


def test_invalid_limit_in_match():
    """Test match raises error for invalid limit."""
    df = pd.DataFrame({"a": ["x"], "b": [1]})
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema).fit(df)

    with pytest.raises(ValueError):
        mdd.match({}, limit=0)


def test_unknown_dimension_in_partial():
    """Test queries raise error for unknown dimension names."""
    df = pd.DataFrame({"a": ["x"], "b": [1]})
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema).fit(df)

    with pytest.raises(ValueError, match="Unknown dimensions"):
        mdd.complete({"unknown_dim": "value"})

    with pytest.raises(ValueError, match="Unknown dimensions"):
        mdd.match({"unknown_dim": "value"})

    with pytest.raises(ValueError, match="Unknown dimensions"):
        mdd.count({"unknown_dim": "value"})


def test_invalid_partial_type():
    """Test queries raise error when partial is not a dict."""
    df = pd.DataFrame({"a": ["x"], "b": [1]})
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema).fit(df)

    with pytest.raises(TypeError):
        mdd.complete("not a dict")

    with pytest.raises(TypeError):
        mdd.match(["not", "a", "dict"])


def test_schema_validation():
    """Test schema validation catches missing columns."""
    df = pd.DataFrame({"a": ["x"]})
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),  # Missing from df
    ])

    with pytest.raises(ValueError, match="missing required columns"):
        Builder(schema).fit(df)


# ==============================================================================
# Size and Structure Tests
# ==============================================================================

def test_size_method():
    """Test size method returns correct statistics."""
    df = pd.DataFrame({
        "a": ["x", "y"],
        "b": [1, 2],
    })
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema).fit(df)
    size = mdd.size()
    assert "nodes" in size
    assert "arcs" in size
    assert "layers" in size
    assert size["layers"] == 2
    assert size["nodes"] > 0
    assert size["arcs"] > 0


def test_repr():
    """Test __repr__ methods."""
    df = pd.DataFrame({"a": ["x"], "b": [1]})
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema).fit(df)
    repr_str = repr(mdd)
    assert "MDD" in repr_str
    assert "nodes=" in repr_str


# ==============================================================================
# Probability Tests
# ==============================================================================

def test_completion_probability_ranking():
    """Test that completions are ranked by probability."""
    df = pd.DataFrame({
        "a": ["x"] * 10 + ["y"] * 2,
        "b": [1] * 10 + [2] * 2,
    })
    schema = Schema([
        DimensionSpec("a", DimensionType.CATEGORICAL),
        DimensionSpec("b", DimensionType.ORDINAL),
    ])
    mdd = Builder(schema).fit(df)
    results = mdd.complete({}, k=2)

    # First result should have higher probability (more frequent path)
    assert results[0].score >= results[1].score
    assert results[0].path["a"] == "x"  # "x" appears 10 times
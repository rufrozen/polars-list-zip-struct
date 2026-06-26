from __future__ import annotations

import pytest

import polars as pl
import polars_list_zip_struct  # noqa: F401
from polars_list_zip_struct import _core
from polars_list_zip_struct import zip_list


def test_list_zip_matches_issue_example() -> None:
    df = pl.DataFrame(
        {
            "a": [[1, 2], [3], None, [None]],
            "b": [[10, 20], [30, 35], [40], [35]],
        }
    )

    out = df.with_columns(
        pl.col("a").list.zip(pl.col("b")).alias("zipped")
    )

    assert out["zipped"].to_list() == [
        [
            {"a": 1, "b": 10},
            {"a": 2, "b": 20},
        ],
        [{"a": 3, "b": 30}],
        None,
        [{"a": None, "b": 35}],
    ]


def test_zip_list_accepts_more_than_two_columns_and_custom_fields() -> None:
    df = pl.DataFrame(
        {
            "a": [[1, 2], [3]],
            "b": [[10, 20], [30, 35]],
            "c": [["x", "y"], ["z", "ignored"]],
        }
    )

    out = df.with_columns(
        zip_list("a", "b", "c", fields=["a", "b", "c"]).alias("zipped")
    )

    assert out["zipped"].to_list() == [
        [{"a": 1, "b": 10, "c": "x"}, {"a": 2, "b": 20, "c": "y"}],
        [{"a": 3, "b": 30, "c": "z"}],
    ]


def test_pad_true_matches_longest_list() -> None:
    df = pl.DataFrame(
        {
            "a": [[1], [], None],
            "b": [[10, 20], [30], [40]],
        }
    )

    out = df.with_columns(
        pl.col("a")
        .list.zip(pl.col("b"), pad=True)
        .alias("zipped")
    )

    assert out["zipped"].to_list() == [
        [{"a": 1, "b": 10}, {"a": None, "b": 20}],
        [{"a": None, "b": 30}],
        None,
    ]


def test_lazy_frame_usage() -> None:
    df = pl.DataFrame({"a": [[1, 2]], "b": [["x", "y"]]})

    out = df.lazy().with_columns(pl.zip_list("a", "b").alias("z")).collect()

    assert out["z"].to_list() == [
        [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]
    ]


def test_validation_errors() -> None:
    with pytest.raises(ValueError, match="at least two"):
        zip_list("a")

    with pytest.raises(ValueError, match="exactly 2"):
        zip_list("a", "b", fields=["a"])

    with pytest.raises(ValueError, match="unique"):
        zip_list("a", "b", fields=["same", "same"])

    with pytest.raises(TypeError, match="single string"):
        zip_list("a", "b", fields="ab")

    with pytest.raises(TypeError, match="bool"):
        zip_list("a", "b", pad="yes")  # type: ignore[arg-type]


@pytest.mark.skipif(
    not _core._native_library_available(),
    reason="native plugin has not been built",
)
def test_native_plugin_errors() -> None:
    df = pl.DataFrame({"a": [[1, 2]], "not_list": [1]})

    with pytest.raises(pl.exceptions.ComputeError, match="has more than one occurrence"):
        df.select(pl.col("a").list.zip(pl.col("a")))

    with pytest.raises(pl.exceptions.ComputeError, match="expected `List`"):
        df.select(pl.col("a").list.zip(pl.col("not_list")))

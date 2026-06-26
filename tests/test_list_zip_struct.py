from __future__ import annotations

import pytest

import polars as pl
import polars_list_zip_struct  # noqa: F401
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
            {"field_0": 1, "field_1": 10},
            {"field_0": 2, "field_1": 20},
        ],
        [{"field_0": 3, "field_1": 30}],
        None,
        [{"field_0": None, "field_1": 35}],
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
        .list.zip(pl.col("b"), pad=True, fields=["a", "b"])
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
        [{"field_0": 1, "field_1": "x"}, {"field_0": 2, "field_1": "y"}]
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

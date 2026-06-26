from __future__ import annotations

from collections.abc import Mapping, Sequence
from itertools import zip_longest
from typing import Any

import polars as pl
from polars._utils.wrap import wrap_expr

IntoExpr = Any

_INPUT_PREFIX = "__polars_list_zip_struct_input_"


def zip_list(
    *exprs: IntoExpr,
    pad: bool = False,
    fields: Sequence[str] | None = None,
    return_dtype: Any | None = None,
) -> pl.Expr:
    """Zip list expressions into a ``list[struct]`` expression.

    Parameters
    ----------
    *exprs
        List expressions to zip. Strings are parsed as column names.
    pad
        If false, truncate to the shortest list. If true, pad shorter lists with
        nulls to match the longest list.
    fields
        Optional struct field names. Defaults to ``field_0``, ``field_1``, ...
    return_dtype
        Optional Polars return dtype for ``Expr.map_elements``.
    """
    if not isinstance(pad, bool):
        msg = "pad must be a bool"
        raise TypeError(msg)
    if len(exprs) < 2:
        msg = "zip_list requires at least two list expressions"
        raise ValueError(msg)

    parsed_exprs = [_parse_into_expr(expr) for expr in exprs]
    field_names = _normalize_fields(fields, len(parsed_exprs))
    aliases = [f"{_INPUT_PREFIX}{i}" for i in range(len(parsed_exprs))]

    row_expr = pl.struct(
        expr.alias(alias) for expr, alias in zip(parsed_exprs, aliases)
    )

    def zip_row(row: Any) -> list[dict[str, Any]] | None:
        values = _row_values(row, aliases)
        if any(value is None for value in values):
            return None

        for value in values:
            if not isinstance(value, list):
                msg = "zip_list expects expressions with List or Array dtype"
                raise TypeError(msg)

        rows = (
            zip_longest(*values, fillvalue=None)
            if pad
            else zip(*values)
        )
        return [dict(zip(field_names, values_row)) for values_row in rows]

    return row_expr.map_elements(
        zip_row,
        return_dtype=return_dtype,
        skip_nulls=False,
    )


def install(*, overwrite: bool = False) -> None:
    """Register fallback Polars helpers when native ones are absent."""
    list_namespace = type(pl.col("__polars_list_zip_struct_probe__").list)

    if overwrite or not hasattr(list_namespace, "zip"):
        setattr(list_namespace, "zip", _expr_list_zip)

    if overwrite or not hasattr(pl, "zip_list"):
        setattr(pl, "zip_list", zip_list)


def _expr_list_zip(
    self: Any,
    other: IntoExpr,
    *,
    pad: bool = False,
    fields: Sequence[str] | None = None,
    return_dtype: Any | None = None,
) -> pl.Expr:
    base_expr = wrap_expr(self._pyexpr)
    return zip_list(
        base_expr,
        other,
        pad=pad,
        fields=fields,
        return_dtype=return_dtype,
    )


def _parse_into_expr(expr: IntoExpr) -> pl.Expr:
    if isinstance(expr, pl.Expr):
        return expr
    if isinstance(expr, str):
        return pl.col(expr)
    return pl.lit(expr)


def _normalize_fields(
    fields: Sequence[str] | None,
    width: int,
) -> list[str]:
    if fields is None:
        return [f"field_{i}" for i in range(width)]
    if isinstance(fields, str):
        msg = "fields must be a sequence of strings, not a single string"
        raise TypeError(msg)

    field_names = list(fields)
    if len(field_names) != width:
        msg = f"fields must contain exactly {width} names"
        raise ValueError(msg)
    if not all(isinstance(field, str) for field in field_names):
        msg = "fields must contain only strings"
        raise TypeError(msg)
    if len(set(field_names)) != len(field_names):
        msg = "fields must be unique"
        raise ValueError(msg)
    return field_names


def _row_values(row: Any, aliases: Sequence[str]) -> list[Any]:
    if row is None:
        return [None] * len(aliases)
    if isinstance(row, Mapping):
        return [row[alias] for alias in aliases]
    return list(row)

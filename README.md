# polars-list-zip-struct

`polars-list-zip-struct` is a native expression plugin for the accepted Polars
`list.zip` proposal from [pola-rs/polars#22719](https://github.com/pola-rs/polars/issues/22719).

It adds:

- `pl.col("a").list.zip(pl.col("b"), pad=False)`
- `pl.zip_list("a", "b", "c", pad=False)`

Both return a `list[struct]` expression. By default, lists are truncated to the
shortest input, like Python's `zip`. With `pad=True`, shorter lists are padded
with nulls to match the longest input. Struct fields default to the input
column/expression names, matching the upstream Polars pull request.

If a future Polars release ships native `list.zip` or `pl.zip_list`, this package
leaves the native implementation untouched.

## Installation

```bash
pip install polars-list-zip-struct
```

## Usage

Import the package once to register the Polars helpers:

```python
import polars as pl
import polars_list_zip_struct  # noqa: F401

df = pl.DataFrame(
    {
        "a": [[1, 2], [3], None, [None]],
        "b": [[10, 20], [30, 35], [40], [35]],
    }
)

out = df.with_columns(
    pl.col("a").list.zip(pl.col("b")).alias("zipped")
)
```

```text
shape: (4, 3)
┌───────────┬───────────┬──────────────────┐
│ a         ┆ b         ┆ zipped           │
│ ---       ┆ ---       ┆ ---              │
│ list[i64] ┆ list[i64] ┆ list[struct[2]]  │
╞═══════════╪═══════════╪══════════════════╡
│ [1, 2]    ┆ [10, 20]  ┆ [{1,10}, {2,20}] │
│ [3]       ┆ [30, 35]  ┆ [{3,30}]         │
│ null      ┆ [40]      ┆ null             │
│ [null]    ┆ [35]      ┆ [{null,35}]      │
└───────────┴───────────┴──────────────────┘
```

Zip more than two list expressions with `pl.zip_list`:

```python
df.with_columns(
    pl.zip_list("a", "b", "c", fields=["a", "b", "c"]).alias("all_zipped")
)
```

Use `pad=True` for `zip_longest` behavior:

```python
df.with_columns(
    pl.col("a").list.zip(pl.col("b"), pad=True).alias("zipped")
)
```

## Notes

The core implementation is a Rust Polars expression plugin built with
`pyo3-polars`. It follows the original upstream implementation idea: build a
`LargeListArray` of `StructArray` values with Arrow builders, offsets, and row
validity, rather than running a Python row loop.

## Development

```bash
python -m pip install -e ".[dev]"
maturin develop
python -m pytest
```

Build and upload:

```bash
python -m pip install ".[publish]"
maturin build --release
python -m twine upload target/wheels/*
```

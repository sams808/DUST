"""CSV import with automatic oxide-column recognition.

Users' CSVs are messy in practice (different capitalization, "Na2O wt%"
vs "Na2O", unicode subscripts, stray whitespace/BOM, semicolon vs comma
separators - see EXAMPLES/DYB/Si50P0-Bi0.csv which uses ';'). This module
normalizes headers and maps them onto the canonical oxide list, plus
carries through any non-oxide columns (sample name, reference, Tg...)
untouched so they survive the round trip into the table/plot.
"""
from __future__ import annotations

import csv
import re
import unicodedata
from io import StringIO

import pandas as pd

from .oxides import CANONICAL_OXIDES

# Accepts things like "Na2O", "Na2O (mol%)", "Na2O_wt%", "SiO2 mol %",
# unicode subscript digits, stray asterisks/footnote markers, etc.
_SUBSCRIPT_MAP = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")


def _normalize(name: str) -> str:
    name = unicodedata.normalize("NFKC", str(name)).translate(_SUBSCRIPT_MAP)
    name = name.strip()
    # drop trailing unit / annotation hints for matching purposes only
    name = re.sub(r"[\[(].*?[\])]", "", name)
    name = re.sub(r"(?i)\b(mol\s*%|wt\s*%|mol|wt|percent|pct)\b", "", name)
    name = re.sub(r"[\s._-]+", "", name)
    return name.lower()


_CANONICAL_LOOKUP = {_normalize(ox): ox for ox in CANONICAL_OXIDES}
# A few common alternate spellings / typos worth catching explicitly.
_ALIASES = {
    "na2o3": "Na2O",  # common typo
    "sio2mol": "SiO2",
    "b2o3mol": "B2O3",
}
_CANONICAL_LOOKUP.update({_normalize(k): v for k, v in _ALIASES.items()})


def detect_delimiter(sample_text: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(sample_text, delimiters=",;\t")
        return dialect.delimiter
    except csv.Error:
        # fall back: whichever of , ; \t appears more often in the header line
        header = sample_text.splitlines()[0] if sample_text else ""
        counts = {d: header.count(d) for d in (",", ";", "\t")}
        return max(counts, key=counts.get) if any(counts.values()) else ","


def read_csv_auto(path_or_buffer) -> pd.DataFrame:
    """Read a CSV, auto-detecting the delimiter (comma or semicolon or tab)."""
    if hasattr(path_or_buffer, "read"):
        text = path_or_buffer.read()
        if isinstance(text, bytes):
            text = text.decode("utf-8-sig")
    else:
        with open(path_or_buffer, "r", encoding="utf-8-sig") as fh:
            text = fh.read()
    delim = detect_delimiter(text)
    return pd.read_csv(StringIO(text), sep=delim)


def suggest_column_mapping(columns) -> dict:
    """Return {original_column_name: canonical_oxide_or_None} best guesses.

    Columns that don't look like a known oxide map to None and are left
    for the user to either ignore or map manually (e.g. sample name,
    reference, Tg, pressure...).
    """
    mapping = {}
    for col in columns:
        key = _normalize(col)
        mapping[col] = _CANONICAL_LOOKUP.get(key)
    return mapping


def apply_mapping(df: pd.DataFrame, mapping: dict, extra_columns: list[str] | None = None) -> pd.DataFrame:
    """Rename columns per ``mapping`` (original -> canonical oxide or None),
    coerce mapped oxide columns to numeric, and keep any columns listed in
    ``extra_columns`` (e.g. a "Sample" label column) even if unmapped.
    """
    extra_columns = extra_columns or []
    keep = {}
    for col in df.columns:
        target = mapping.get(col)
        if target:
            keep[col] = target
        elif col in extra_columns:
            keep[col] = col
    out = df[list(keep.keys())].rename(columns=keep)
    for ox in out.columns:
        if ox in CANONICAL_OXIDES:
            out[ox] = pd.to_numeric(out[ox], errors="coerce")
    return out


def wt_to_mol_percent(df: pd.DataFrame, molar_mass: dict) -> pd.DataFrame:
    """Convert oxide wt% columns to mol% (renormalized to sum to 100 per row)."""
    out = df.copy()
    oxide_cols = [c for c in out.columns if c in molar_mass]
    moles = out[oxide_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0) / pd.Series(
        {c: molar_mass[c] for c in oxide_cols}
    )
    total = moles.sum(axis=1)
    for c in oxide_cols:
        with pd.option_context("mode.use_inf_as_na", True):
            out[c] = (moles[c] / total * 100.0).where(total > 0)
    return out

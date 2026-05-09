"""Shared data models for the visual-logic function catalog."""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class FuncEntry:
    """Metadata for a single callable in the function catalog."""

    path: str
    label: str
    signature: str
    min_args: int
    max_args: int | None
    param_names: tuple[str, ...]
    param_types: tuple[str, ...] = ()
    return_type: str = 'any'
    is_class: bool = False


@dataclasses.dataclass(frozen=True)
class TraceParam:
    """Metadata for one parameter of a plotly trace."""

    name: str
    label: str
    required: bool
    hint: str = ''


@dataclasses.dataclass(frozen=True)
class PlotlyTraceEntry:
    """Metadata for a go.<Trace> type."""

    kind: str
    label: str
    go_class: str
    params: tuple[TraceParam, ...]


def param_names_for(entry: FuncEntry) -> list[str]:
    """Return ordered parameter names for a FuncEntry."""
    return list(entry.param_names)


def param_types_for(entry: FuncEntry) -> list[str]:
    """Return ordered parameter type tags for a FuncEntry."""
    return list(entry.param_types)
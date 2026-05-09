"""Transient preview result helpers for Acherion graph workbenches."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from copy import deepcopy
from typing import Any, cast

from acherion.catalog import types as _catalog_types
from acherion.theme import acherion_plotly_template_payload


@dataclass
class AcherionPreviewRunResult:
    """Transient preview payload returned by one preview execution."""

    reference_values: dict[str, Any] = field(default_factory=dict)
    state_values: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AcherionPreviewValueAdapter:
    """Host-registered preview behavior for one family of runtime values."""

    name: str
    matcher: Callable[[Any], bool]
    summary: Callable[[Any], str | None] | None = None
    type_tag: Callable[[Any], str | None] | None = None


_REGISTERED_PREVIEW_VALUE_ADAPTERS: dict[str, AcherionPreviewValueAdapter] = {}


def register_preview_value_adapter(
    adapter: AcherionPreviewValueAdapter,
    *,
    replace: bool = False,
) -> None:
    """Register one host preview adapter by stable name."""
    clean_name = str(adapter.name or '').strip()
    if not clean_name:
        raise ValueError('Preview adapter name is required.')
    if clean_name in _REGISTERED_PREVIEW_VALUE_ADAPTERS and not replace:
        raise ValueError(f'Preview adapter already registered: {clean_name}')
    _REGISTERED_PREVIEW_VALUE_ADAPTERS[clean_name] = adapter


def _registered_preview_value_adapters() -> tuple[AcherionPreviewValueAdapter, ...]:
    """Return registered preview adapters in stable registration order."""
    return tuple(_REGISTERED_PREVIEW_VALUE_ADAPTERS.values())


def preview_value_type_tag(value: Any) -> str:
    """Return best-effort type tag for one preview value."""
    for adapter in _registered_preview_value_adapters():
        if not adapter.matcher(value) or adapter.type_tag is None:
            continue
        type_tag = str(adapter.type_tag(value) or '').strip()
        if type_tag:
            return type_tag
    return cast(str, _catalog_types.value_to_type_tag(value))


def preview_value_summary(value: Any) -> str:
    """Return one short human-readable preview summary."""
    for adapter in _registered_preview_value_adapters():
        if not adapter.matcher(value) or adapter.summary is None:
            continue
        summary = str(adapter.summary(value) or '').strip()
        if summary:
            return summary
    return _simple_summary(value)


def preview_value_plotly_payload(value: Any) -> dict[str, Any] | None:
    """Return serialized payload for one Plotly figure preview value."""
    value_type = type(value)
    module_name = str(getattr(value_type, '__module__', '') or '')
    if not module_name.startswith('plotly'):
        return None
    serializer = getattr(value, 'to_plotly_json', None)
    if not callable(serializer):
        return None
    try:
        payload = serializer()
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    themed_payload = deepcopy(payload)
    layout = themed_payload.get('layout')
    if not isinstance(layout, dict):
        layout = {}
        themed_payload['layout'] = layout
    layout['template'] = acherion_plotly_template_payload()
    return themed_payload


def _simple_summary(value: Any) -> str:
    if value is None:
        return 'None'
    if isinstance(value, bool):
        return 'True' if value else 'False'
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        text = value.strip()
        if len(text) <= 48:
            return text or "''"
        return text[:45] + '...'
    if isinstance(value, dict):
        return f'dict[{len(value)}]'
    if isinstance(value, list):
        return f'list[{len(value)}]'
    if isinstance(value, tuple):
        return f'tuple[{len(value)}]'
    if isinstance(value, set):
        return f'set[{len(value)}]'
    value_type = type(value)
    module_name = str(getattr(value_type, '__module__', '') or '')
    type_name = str(getattr(value_type, '__name__', '') or 'object')
    if module_name.startswith('plotly') and type_name == 'Figure':
        return 'plotly figure'
    if module_name.startswith('numpy') and type_name == 'ndarray':
        shape = getattr(value, 'shape', None)
        if isinstance(shape, tuple):
            return 'ndarray' + str(shape)
        return 'ndarray'
    return type_name


__all__ = [
    'AcherionPreviewRunResult',
    'AcherionPreviewValueAdapter',
    'preview_value_plotly_payload',
    'preview_value_summary',
    'preview_value_type_tag',
    'register_preview_value_adapter',
]
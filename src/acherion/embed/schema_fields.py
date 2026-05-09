"""Schema renderer registry and generic editor helpers for Acherion."""

from __future__ import annotations

from collections.abc import Callable, Mapping
import re
from typing import Any

from nicegui import ui

_SchemaComponentFieldRenderer = Callable[..., None]

_IDENTIFIER_RE = re.compile(r'[^a-zA-Z0-9_]+')

_SCHEMA_COMPONENT_FIELD_RENDERERS: dict[
    str,
    _SchemaComponentFieldRenderer,
] = {}


def _schema_label(node: Any, fallback: str) -> str:
    label = str(getattr(node, 'title', '') or '').strip()
    return label or fallback


def schema_label(node: Any, fallback: str) -> str:
    """Return a title-derived label with a fallback for schema metadata."""
    return _schema_label(node, fallback)


def _auto_identifier(text: str, fallback: str = 'field') -> str:
    identifier = _IDENTIFIER_RE.sub('_', str(text or '').strip().lower())
    identifier = re.sub(r'_+', '_', identifier).strip('_')
    if not identifier:
        identifier = fallback
    if identifier[0].isdigit():
        identifier = f'field_{identifier}'
    return identifier


def register_schema_component_field_renderer(
    component_kind: str,
    renderer: _SchemaComponentFieldRenderer,
) -> None:
    """Register one schema-field renderer for a component kind."""
    kind = str(component_kind or '').strip()
    if not kind:
        raise ValueError('Schema component kind must be non-empty.')
    _SCHEMA_COMPONENT_FIELD_RENDERERS[kind] = renderer


def register_schema_component_field_renderers(
    renderers: Mapping[str, _SchemaComponentFieldRenderer],
) -> None:
    """Register a batch of schema-field renderers."""
    for component_kind, renderer in renderers.items():
        register_schema_component_field_renderer(component_kind, renderer)


def _default_event_emitter(index: int) -> dict[str, str]:
    if index <= 1:
        return {
            'name': 'changed',
            'label': 'Changed',
            'description': '',
        }
    return {
        'name': f'event_{index}',
        'label': f'Event {index}',
        'description': '',
    }


def _normalise_event_emitter(
    value: Any,
    *,
    index: int,
) -> dict[str, str]:
    raw = dict(value) if isinstance(value, dict) else {}
    emitter = dict(_default_event_emitter(index))
    emitter['name'] = _auto_identifier(
        str(raw.get('name') or emitter['name']),
        emitter['name'],
    )
    emitter['label'] = str(raw.get('label') or '').strip() or emitter['label']
    emitter['description'] = str(raw.get('description') or '').strip()
    return emitter


def _normalise_event_emitters(value: Any) -> list[dict[str, str]]:
    raw_emitters = value if isinstance(value, list) else []
    emitters = [
        _normalise_event_emitter(raw_emitter, index=index + 1)
        for index, raw_emitter in enumerate(raw_emitters)
        if isinstance(raw_emitter, dict)
    ]
    seen_names: set[str] = set()
    for index, emitter in enumerate(emitters, start=1):
        base_name = _auto_identifier(
            str(emitter.get('name') or ''),
            f'event_{index}',
        )
        name = base_name
        suffix = 1
        while name in seen_names:
            name = f'{base_name}_{suffix}'
            suffix += 1
        emitter['name'] = name
        seen_names.add(name)
    return emitters


def normalise_event_emitters(value: Any) -> list[dict[str, str]]:
    """Return one normalized list of component-emitted event metadata."""
    return _normalise_event_emitters(value)


def _set_event_emitter_field(
    emitters: list[dict[str, str]],
    index: int,
    key: str,
    value: Any,
) -> list[dict[str, str]]:
    next_emitters = [dict(emitter) for emitter in emitters]
    if not (0 <= index < len(next_emitters)):
        return next_emitters
    if key == 'name':
        next_emitters[index][key] = _auto_identifier(
            str(value or '').strip(),
            f'event_{index + 1}',
        )
    else:
        next_emitters[index][key] = str(value or '').strip()
    return _normalise_event_emitters(next_emitters)


def _render_event_emitter_fields(
    *,
    state: dict[str, Any],
    set_field: Callable[..., None],
) -> None:
    emitters = _normalise_event_emitters(state.get('event_emitters'))
    ui.label('Emitted events').classes('text-xs font-semibold oe-muted')
    ui.label(
        'Optional component-scoped runtime events. Embedded hosts can map '
        'their widget callbacks into these event keys.'
    ).classes('text-xs oe-muted')
    if not emitters:
        ui.label('No emitted events yet.').classes('text-xs oe-muted')
    for index, emitter in enumerate(emitters):
        with ui.card().classes('w-full gap-2').style(
            'padding:8px; border-radius:8px'
        ):
            with ui.row().classes('w-full items-start gap-2'):
                ui.input(
                    'Event name',
                    value=str(emitter.get('name') or ''),
                    on_change=lambda e, i=index: set_field(
                        'event_emitters',
                        _set_event_emitter_field(
                            emitters,
                            i,
                            'name',
                            e.value,
                        ),
                    ),
                ).props('outlined dense').classes('flex-1 ach-editor-field')
                ui.button(
                    icon='close',
                    on_click=lambda _e, i=index: set_field(
                        'event_emitters',
                        [
                            emitter_item
                            for emitter_index, emitter_item in enumerate(emitters)
                            if emitter_index != i
                        ],
                        True,
                    ),
                ).props('flat dense round color=negative').tooltip(
                    'Remove event'
                )
            ui.input(
                'Label',
                value=str(emitter.get('label') or ''),
                on_change=lambda e, i=index: set_field(
                    'event_emitters',
                    _set_event_emitter_field(
                        emitters,
                        i,
                        'label',
                        e.value,
                    ),
                ),
            ).props('outlined dense').classes('w-full ach-editor-field')
            ui.input(
                'Description (optional)',
                value=str(emitter.get('description') or ''),
                on_change=lambda e, i=index: set_field(
                    'event_emitters',
                    _set_event_emitter_field(
                        emitters,
                        i,
                        'description',
                        e.value,
                    ),
                ),
            ).props('outlined dense').classes('w-full ach-editor-field')

    ui.button(
        'Add event',
        icon='add',
        on_click=lambda: set_field(
            'event_emitters',
            [
                *emitters,
                _default_event_emitter(len(emitters) + 1),
            ],
            True,
        ),
    ).props('flat dense')


def _render_schema_component_fields(
    *,
    component_kind: str,
    state: dict[str, Any],
    set_field: Callable[..., None],
    refresh_editor: Callable[[], None] | None,
) -> None:
    renderer = _SCHEMA_COMPONENT_FIELD_RENDERERS.get(component_kind)
    if renderer is None:
        return
    renderer(
        component_kind=component_kind,
        state=state,
        set_field=set_field,
        refresh_editor=refresh_editor,
    )


def render_schema_component_fields(
    *,
    component_kind: str,
    state: dict[str, Any],
    set_field: Callable[..., None],
    refresh_editor: Callable[[], None] | None,
) -> None:
    """Render shared editor fields for one schema-backed component."""
    _render_schema_component_fields(
        component_kind=component_kind,
        state=state,
        set_field=set_field,
        refresh_editor=refresh_editor,
    )


def render_event_emitter_fields(
    *,
    state: dict[str, Any],
    set_field: Callable[..., None],
) -> None:
    """Render shared editor fields for component-scoped emitted events."""
    _render_event_emitter_fields(
        state=state,
        set_field=set_field,
    )


__all__ = [
    'normalise_event_emitters',
    'register_schema_component_field_renderer',
    'register_schema_component_field_renderers',
    'render_event_emitter_fields',
    'render_schema_component_fields',
    'schema_label',
]
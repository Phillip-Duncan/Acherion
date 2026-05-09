"""Standalone event definitions for embedded Acherion runtimes."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import re
from typing import Any

EXTERNAL_EVENT_NODE_KIND = 'external_event'
RUN_EVENT_KEY = 'run'

_EVENT_IDENTIFIER_RE = re.compile(r'[^a-zA-Z0-9_]+')


@dataclass(frozen=True, slots=True)
class AcherionExternalEvent:
    """Describe one external event that a host can feed into Acherion."""

    event_key: str
    title: str
    handler_name: str
    description: str = ''
    source_kind: str = 'host'
    component_key: str = ''
    component_event: str = ''


def _clean_identifier(text: str, fallback: str = 'event') -> str:
    """Return one safe Python identifier fragment."""
    identifier = _EVENT_IDENTIFIER_RE.sub('_', str(text or '').strip().lower())
    identifier = re.sub(r'_+', '_', identifier).strip('_')
    if not identifier:
        identifier = fallback
    if identifier[0].isdigit():
        identifier = f'{fallback}_{identifier}'
    return identifier


def acherion_event_handler_name(
    event_key: str,
    *,
    prefix: str = 'on',
) -> str:
    """Return the default handler name for one external event key."""
    identifier = _clean_identifier(event_key)
    if not prefix:
        return identifier
    return f'{prefix}_{identifier}'


def component_event_key(component_key: str, component_event: str) -> str:
    """Return the stable runtime event key for one component event."""
    clean_component_key = _clean_identifier(component_key, 'component')
    clean_component_event = _clean_identifier(component_event, 'event')
    return (
        f'component:{clean_component_key}:{clean_component_event}'
    )


def build_component_external_event(
    *,
    component_key: str,
    component_event: str,
    component_label: str = '',
    event_label: str = '',
    description: str = '',
) -> AcherionExternalEvent:
    """Return one normalized component-driven external event."""
    clean_component_key = _clean_identifier(component_key, 'component')
    clean_component_event = _clean_identifier(component_event, 'event')
    clean_component_label = str(component_label or component_key).strip()
    clean_event_label = str(event_label or component_event).strip()
    event_key = component_event_key(
        clean_component_key,
        clean_component_event,
    )
    return AcherionExternalEvent(
        event_key=event_key,
        title=(
            f'Event: {clean_component_label or clean_component_key} - '
            f'{clean_event_label or clean_component_event}'
        ),
        handler_name=acherion_event_handler_name(event_key),
        description=str(description or '').strip(),
        source_kind='component',
        component_key=clean_component_key,
        component_event=clean_component_event,
    )


def acherion_external_event_params(
    event: AcherionExternalEvent,
) -> dict[str, str]:
    """Return one plain-dict payload for persisted/generated event metadata."""
    return {
        'event_key': event.event_key,
        'title': event.title,
        'handler_name': event.handler_name,
        'description': event.description,
        'source_kind': event.source_kind,
        'component_key': event.component_key,
        'component_event': event.component_event,
    }


def normalize_acherion_external_event_params(
    params: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Return cleaned params for one external-event node payload."""
    event_data = dict(params or {})
    event_key = str(event_data.get('event_key') or '').strip()
    handler_name = str(event_data.get('handler_name') or '').strip()
    description = str(event_data.get('description') or '').strip()
    component_key = str(event_data.get('component_key') or '').strip()
    component_event = str(event_data.get('component_event') or '').strip()
    source_kind = str(event_data.get('source_kind') or '').strip() or 'host'
    if component_key or component_event:
        source_kind = 'component'
    if not handler_name and event_key == RUN_EVENT_KEY:
        handler_name = 'run'
    elif not handler_name and event_key:
        handler_name = acherion_event_handler_name(event_key)
    event_data.update({
        'event_key': event_key,
        'handler_name': handler_name,
        'description': description,
        'source_kind': source_kind,
        'component_key': component_key,
        'component_event': component_event,
    })
    return event_data


def normalize_acherion_external_events(
    events: Mapping[str, Any] | None,
) -> dict[str, AcherionExternalEvent]:
    """Return a cleaned event mapping keyed by normalized event key."""
    normalized: dict[str, AcherionExternalEvent] = {}
    if not events:
        return normalized
    for raw_key, raw_event in events.items():
        if isinstance(raw_event, AcherionExternalEvent):
            event_data = acherion_external_event_params(raw_event)
        elif isinstance(raw_event, Mapping):
            event_data = normalize_acherion_external_event_params(raw_event)
        else:
            continue
        event_key = str(event_data.get('event_key') or raw_key).strip()
        title = str(event_data.get('title') or '').strip()
        handler_name = str(event_data.get('handler_name') or '').strip()
        description = str(event_data.get('description') or '').strip()
        component_key = str(event_data.get('component_key') or '').strip()
        component_event = str(event_data.get('component_event') or '').strip()
        source_kind = str(event_data.get('source_kind') or '').strip() or 'host'
        if not title:
            title = f'Event: {event_key}'
        if not event_key or not title or not handler_name:
            continue
        normalized[event_key] = AcherionExternalEvent(
            event_key=event_key,
            title=title,
            handler_name=handler_name,
            description=description,
            source_kind=source_kind,
            component_key=component_key,
            component_event=component_event,
        )
    return normalized


def resolve_acherion_external_event(
    events: Mapping[str, Any] | None,
    event_key: str,
) -> AcherionExternalEvent | None:
    """Return one normalized external event by key, if present."""
    return normalize_acherion_external_events(events).get(
        str(event_key or '').strip()
    )


def component_events_for_key(
    events: Mapping[str, Any] | None,
    component_key: str,
) -> tuple[AcherionExternalEvent, ...]:
    """Return all component-driven events bound to one component key."""
    clean_component_key = _clean_identifier(component_key, 'component')
    if not clean_component_key:
        return ()
    return tuple(
        event
        for event in normalize_acherion_external_events(events).values()
        if event.source_kind == 'component'
        and event.component_key == clean_component_key
    )


def collect_acherion_external_events(
    nodes: Iterable[Any],
) -> dict[str, AcherionExternalEvent]:
    """Return normalized external events declared by graph source nodes."""
    events: dict[str, dict[str, Any]] = {}
    for node in nodes:
        if str(getattr(node, 'kind', '') or '').strip() != EXTERNAL_EVENT_NODE_KIND:
            continue
        params = dict(getattr(node, 'params', {}) or {})
        if str(params.get('parent_function') or '').strip():
            continue
        event_data = normalize_acherion_external_event_params(params)
        event_key = str(event_data.get('event_key') or '').strip()
        if not event_key:
            continue
        title = str(getattr(node, 'title', '') or params.get('title') or '').strip()
        if title:
            event_data['title'] = title
        events[event_key] = event_data
    return normalize_acherion_external_events(events)


def serializable_acherion_external_events(
    events: Mapping[str, Any] | None,
) -> dict[str, dict[str, str]]:
    """Return one plain-dict mapping safe to inject into generated code."""
    return {
        event_key: acherion_external_event_params(event)
        for event_key, event in normalize_acherion_external_events(events).items()
    }


def default_acherion_external_events() -> dict[str, AcherionExternalEvent]:
    """Return builtin host-driven events available to generic graphs."""
    return normalize_acherion_external_events({
        RUN_EVENT_KEY: {
            'event_key': RUN_EVENT_KEY,
            'title': 'Event: Run',
            'handler_name': 'run',
            'description': 'Start run() execution for this graph path.',
        },
    })


def compose_acherion_external_events(
    *event_maps: Mapping[str, Any] | None,
    include_defaults: bool = True,
) -> dict[str, AcherionExternalEvent]:
    """Return normalized host events merged with optional builtin defaults."""
    merged: dict[str, Any] = {}
    if include_defaults:
        merged.update(default_acherion_external_events())
    for event_map in event_maps:
        if not event_map:
            continue
        merged.update(dict(event_map))
    return normalize_acherion_external_events(merged)
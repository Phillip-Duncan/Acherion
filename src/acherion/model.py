"""Data model for the Acherion graph."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from acherion.events import (
    EXTERNAL_EVENT_NODE_KIND,
    normalize_acherion_external_event_params,
)
from acherion.node import (
    acherion_auto_identifier,
    acherion_node_identifier,
)
from acherion.constants import (
    _MANUAL_X,
    _MANUAL_Y,
    _NODE_STEP,
    _NODE_TOP,
)
from acherion.registry import (
    get_acherion_node_definition,
    _node_template,
    _template_has_exec_input,
)


@dataclass
class AcherionNode:
    """One node in the Acherion graph."""

    node_id: str
    kind: str
    title: str = ''
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class AcherionGraph:
    """Serialisable Acherion graph."""

    version: int = 1
    nodes: list[AcherionNode] = field(default_factory=list)
    groups: dict[str, str] = field(default_factory=dict)
    user_functions: dict[str, dict[str, Any]] = field(default_factory=dict)


def _graph_from_dict(data: dict[str, Any] | None) -> AcherionGraph:
    """Decode persisted Acherion graph state."""
    data_map = dict(data or {})
    nodes: list[AcherionNode] = []
    for raw_node in data_map.get('nodes', []):
        node_dict = dict(raw_node or {})
        node_id = str(node_dict.get('node_id') or '').strip()
        if not node_id:
            node_id = uuid.uuid4().hex[:8]
        params = dict(node_dict.get('params', {}))
        kind = str(node_dict.get('kind') or 'constant').strip() or 'constant'
        if kind == EXTERNAL_EVENT_NODE_KIND:
            params = normalize_acherion_external_event_params(params)
        nodes.append(
            AcherionNode(
                node_id=node_id,
                kind=kind,
                title=str(node_dict.get('title') or '').strip(),
                params=params,
            )
        )
    raw_groups = data_map.get('groups') or {}
    groups: dict[str, str] = {}
    if isinstance(raw_groups, dict):
        for k, v in raw_groups.items():
            if k and isinstance(k, str) and isinstance(v, str):
                groups[str(k)] = str(v)
    raw_user_functions = data_map.get('user_functions') or {}
    user_functions: dict[str, dict[str, Any]] = {}
    if isinstance(raw_user_functions, dict):
        for path, raw_data in raw_user_functions.items():
            if not isinstance(path, str) or not path:
                continue
            if not isinstance(raw_data, dict):
                continue
            user_functions[path] = dict(raw_data)
    return AcherionGraph(
        version=int(data_map.get('version') or 1),
        nodes=nodes,
        groups=groups,
        user_functions=user_functions,
    )


def _graph_to_dict(graph: AcherionGraph) -> dict[str, Any]:
    """Encode an Acherion graph as plain dict/list state."""
    return {
        'version': int(graph.version or 1),
        'nodes': [
            {
                'node_id': node.node_id,
                'kind': node.kind,
                'title': node.title,
                'params': dict(node.params),
            }
            for node in graph.nodes
        ],
        'groups': dict(graph.groups),
        'user_functions': {
            path: dict(data)
            for path, data in graph.user_functions.items()
        },
    }


def _template_title(kind: str) -> str:
    """Return the display title for a node kind."""
    template = _node_template(kind)
    if template is not None:
        return template.label
    return kind.replace('_', ' ').title()


def _template_icon(kind: str) -> str:
    """Return the Material Icon name for a node kind."""
    template = _node_template(kind)
    if template is not None:
        return template.icon
    return 'account_tree'


def _system_node_id(kind: str, key: str) -> str:
    """Return the deterministic node_id for a system node."""
    return f'{kind}:{key}'


def _node_var_name(index: int, node: AcherionNode) -> str:
    """Return the Python variable name emitted for a producer node."""
    identifier = acherion_node_identifier(node.kind, node)
    if identifier is not None:
        return identifier
    if str(node.title or '').strip():
        return acherion_auto_identifier(node.title, node.kind)
    return f'node_{index + 1}_{node.kind}'


def _default_node(kind: str) -> AcherionNode:
    """Return a new node with default params for the requested kind."""
    node_id = uuid.uuid4().hex[:8]
    definition = get_acherion_node_definition(kind)
    params: dict[str, Any]
    if definition is not None:
        params = definition.default_params(node_id=node_id)
        title = definition.default_title()
    else:
        params = {'source_key': ''}
        if _template_has_exec_input(kind):
            params.setdefault('exec_sources', [])
        title = _template_title(kind)
    return AcherionNode(
        node_id=node_id,
        kind=kind,
        title=title,
        params=params,
    )

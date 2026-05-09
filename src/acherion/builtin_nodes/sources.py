"""Core source node definitions for Acherion."""

from __future__ import annotations

from acherion.events import EXTERNAL_EVENT_NODE_KIND
import acherion.node as acherion_node


class ExternalEventNode(acherion_node.SystemSourceNodeDefinition):
    kind = EXTERNAL_EVENT_NODE_KIND
    label = 'External Event'
    icon = 'bolt'
    tooltip = 'Fire logic from a host-driven or component-driven runtime event.'
    flavor = 'event'
    exec_out = True


BUILTIN_SOURCE_NODES = (
    ExternalEventNode(),
)

__all__ = [
    'BUILTIN_SOURCE_NODES',
]

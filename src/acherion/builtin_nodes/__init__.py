"""Built-in class-based node definitions for Acherion."""

from __future__ import annotations

import acherion.builtin_nodes.composite as _composite
import acherion.builtin_nodes.compute as _compute
import acherion.builtin_nodes.flow as _flow
import acherion.builtin_nodes.objects as _objects
import acherion.builtin_nodes.sources as _sources

BUILTIN_NODE_DEFINITIONS = (
    *_sources.BUILTIN_SOURCE_NODES,
    *_compute.BUILTIN_COMPUTE_NODES,
    *_flow.BUILTIN_FLOW_NODES,
    *_objects.BUILTIN_OBJECT_NODES,
    *_composite.BUILTIN_COMPOSITE_NODES,
)

__all__ = ['BUILTIN_NODE_DEFINITIONS']

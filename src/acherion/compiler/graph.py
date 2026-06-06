"""Graph and function-box helper logic for visual-logic compilation."""

from __future__ import annotations

from typing import Any

import acherion.graph_helpers as _graph_helpers
from acherion.compiler.utils import (
    _safe_function_name,
)
from acherion.model import AcherionNode
from acherion.registry import (
    get_acherion_node_definition,
)


def _iter_param_sources(node: AcherionNode) -> list[str]:
    """Return all source-id strings referenced in params."""
    params = dict(node.params)
    definition = get_acherion_node_definition(node.kind)
    source_param_ids = (
        list(definition.source_param_ids(node))
        if definition is not None
        else []
    )
    return _graph_helpers.iter_param_sources(params, source_param_ids)


def _pure_source_id(source_id: str) -> str:
    """Return the node_id portion of a source reference."""
    return _graph_helpers.pure_source_id(source_id)


class _FunctionBoxGraphView:
    """Own function-box boundary and ordering state for one node set."""

    def __init__(self, nodes: list[AcherionNode]) -> None:
        self._nodes = list(nodes)
        self._node_index = {
            node.node_id: node for node in self._nodes
        }
        self._boundary_records: list[
            tuple[str, str, str, dict[str, Any], list[str]]
        ] | None = None
        self._boundary_cache: dict[str, tuple[list[str], list[str]]] = {}

    @property
    def nodes(self) -> list[AcherionNode]:
        """Return nodes visible through this graph view."""
        return self._nodes

    @property
    def node_index(self) -> dict[str, AcherionNode]:
        """Return node lookup table for this graph view."""
        return self._node_index

    @staticmethod
    def pure_source_id(source_id: str) -> str:
        """Return the node id portion of a source reference."""
        return _pure_source_id(source_id)

    def _native_boundary_records(
        self,
    ) -> list[tuple[str, str, str, dict[str, Any], list[str]]]:
        if self._boundary_records is not None:
            return self._boundary_records
        records: list[tuple[str, str, str, dict[str, Any], list[str]]] = []
        for node in self._nodes:
            params = dict(node.params)
            definition = get_acherion_node_definition(node.kind)
            source_param_ids = (
                list(definition.source_param_ids(node))
                if definition is not None
                else []
            )
            records.append((
                node.node_id,
                node.kind,
                str(params.get('parent_function') or '').strip(),
                params,
                source_param_ids,
            ))
        self._boundary_records = records
        return records

    def _boundary_sources(
        self,
        box_node_id: str,
    ) -> tuple[list[str], list[str]]:
        if box_node_id not in self._boundary_cache:
            input_sources, output_sources = _graph_helpers.function_box_boundary_sources(
                self._native_boundary_records(),
                box_node_id,
            )
            self._boundary_cache[box_node_id] = (
                list(input_sources),
                list(output_sources),
            )
        inputs, outputs = self._boundary_cache[box_node_id]
        return list(inputs), list(outputs)

    def ordered_io_nodes(
        self,
        box_node_id: str,
        *,
        io_kind: str,
        ordered_ids: list[str],
    ) -> list[AcherionNode]:
        """Explicit function IO nodes are obsolete and no longer exposed."""
        del box_node_id, io_kind, ordered_ids
        return []

    def function_box_depth(self, box_node: AcherionNode) -> int:
        """Return nesting depth for one function box node."""
        depth = 0
        seen: set[str] = set()
        parent_id = str(box_node.params.get('parent_function') or '')
        while parent_id and parent_id not in seen:
            seen.add(parent_id)
            parent = self._node_index.get(parent_id)
            if parent is None or parent.kind != 'function_box':
                break
            depth += 1
            parent_id = str(parent.params.get('parent_function') or '')
        return depth

    def boundary_input_sources(self, box_node_id: str) -> list[str]:
        """Return sources that cross from outside into a function box."""
        sources, _outputs = self._boundary_sources(box_node_id)
        return sources

    def boundary_output_sources(self, box_node_id: str) -> list[str]:
        """Return sources that cross from inside a function box outward."""
        _inputs, sources = self._boundary_sources(box_node_id)
        return sources

    def external_inputs(self, box: AcherionNode) -> list[tuple[str, str]]:
        """Return helper parameter metadata for a function box."""
        input_source_ids = self.boundary_input_sources(box.node_id)
        inferred_inputs: list[tuple[str, str]] = []
        inferred_names: set[str] = set()
        for index, source_id in enumerate(input_source_ids, start=1):
            source_node = self._node_index.get(_pure_source_id(source_id))
            source_name = (
                str(source_node.title or source_node.kind)
                if source_node is not None
                else f'arg_{index}'
            )
            base_name = _safe_function_name(source_name, f'arg_{index}')
            name = base_name
            suffix = 2
            while name in inferred_names:
                name = f'{base_name}_{suffix}'
                suffix += 1
            inferred_names.add(name)
            inferred_inputs.append((name, source_id))
        return inferred_inputs

    def return_sources(self, box: AcherionNode) -> list[str]:
        """Return sources a function box should emit as helper returns."""
        return self.boundary_output_sources(box.node_id)

    def _node_has_function_ancestor(
        self,
        node: AcherionNode,
        ancestor_box_id: str,
    ) -> bool:
        seen: set[str] = set()
        current: AcherionNode | None = node
        while current is not None:
            parent_id = str(current.params.get('parent_function') or '')
            if not parent_id or parent_id in seen:
                return False
            if parent_id == ancestor_box_id:
                return True
            seen.add(parent_id)
            current = self._node_index.get(parent_id)
        return False


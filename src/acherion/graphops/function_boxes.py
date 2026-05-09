"""Function-box helper mixin for visual-logic graph ops."""

# pyright: reportAttributeAccessIssue=false

from __future__ import annotations

from typing import Any, Protocol, cast

from acherion.constants import _NODE_STEP
from acherion.model import AcherionNode, _default_node


class _FunctionBoxOwner(Protocol):
    def _node_by_id(self, node_id: str) -> AcherionNode | None:
        ...

    def _pure_node_id(self, source_id: str) -> str:
        ...

    def _function_parent_id(self, node: AcherionNode) -> str:
        ...


class _GraphOpsFunctionBoxesMixin:
    """Function-box traversal and port-sync helpers."""

    _selected_connection_id: str | None = None

    @staticmethod
    def _is_function_box(node: AcherionNode) -> bool:
        return node.kind == 'function_box'

    @staticmethod
    def _is_function_input(node: AcherionNode) -> bool:
        return node.kind == 'function_input'

    @staticmethod
    def _is_function_output(node: AcherionNode) -> bool:
        return node.kind == 'function_output'

    @staticmethod
    def _is_function_entry(node: AcherionNode) -> bool:
        return node.kind == 'function_entry'

    @staticmethod
    def _function_entry_node_id(box_id: str) -> str:
        return f'{box_id}:entry'

    def _function_parent_id(self: Any, node: AcherionNode) -> str:
        return str(node.params.get('parent_function') or '').strip()

    def _function_child_nodes(self: Any, box_id: str) -> list[AcherionNode]:
        return [
            node for node in self._manual_nodes()
            if self._function_parent_id(node) == box_id
        ]

    def _function_entry_node(self: Any, box_id: str) -> AcherionNode | None:
        for node in self._function_child_nodes(box_id):
            if self._is_function_entry(node):
                return cast(AcherionNode, node)
        return None

    def _visible_function_child_nodes(self: Any, box_id: str) -> list[AcherionNode]:
        return [
            node for node in self._function_child_nodes(box_id)
            if not self._is_function_input(node)
            and not self._is_function_output(node)
            and not self._is_function_entry(node)
        ]

    def _node_has_function_ancestor(
        self: Any,
        node_id: str,
        ancestor_box_id: str,
    ) -> bool:
        current = self._node_by_id(node_id)
        seen: set[str] = set()
        while current is not None:
            parent_id = self._function_parent_id(current)
            if not parent_id or parent_id in seen:
                return False
            if parent_id == ancestor_box_id:
                return True
            seen.add(parent_id)
            current = self._node_by_id(parent_id)
        return False

    def _containing_function_box_id(
        self: Any,
        x: int,
        y: int,
        *,
        exclude_node_id: str = '',
    ) -> str:
        x = self._world_to_canvas_x(x)
        y = self._world_to_canvas_y(y)
        candidates: list[tuple[int, int, int, str]] = []
        for node in self._manual_nodes():
            if not self._is_function_box(node):
                continue
            if exclude_node_id and node.node_id == exclude_node_id:
                continue
            if exclude_node_id and self._node_has_function_ancestor(
                node.node_id,
                exclude_node_id,
            ):
                continue
            left, top, width, height = self._node_bounds(node)
            if left <= x <= left + width and top <= y <= top + height:
                candidates.append((width * height, top, left, node.node_id))
        if not candidates:
            return ''
        candidates.sort()
        return candidates[0][3]

    def _assign_node_to_containing_function_box(
        self: Any,
        node: AcherionNode,
        left: int,
        top: int,
    ) -> None:
        if self._is_system_node(node):
            return
        if self._is_function_input(node) or self._is_function_output(node):
            return
        center_x = left + max(1, self._node_width(node) // 2)
        center_y = top + max(1, self._node_height(node) // 2)
        parent_box_id = self._containing_function_box_id(
            center_x,
            center_y,
            exclude_node_id=node.node_id,
        )
        node.params['parent_function'] = parent_box_id

    def _selected_function_box_target(self: Any) -> str:
        if not self._selected_node_ids:
            return ''
        target_ids: set[str] = set()
        for node in self._manual_nodes():
            if node.node_id not in self._selected_node_ids:
                continue
            if self._is_function_box(node):
                target_ids.add(node.node_id)
            else:
                target_ids.add(self._function_parent_id(node))
        target_ids.discard('')
        if len(target_ids) == 1:
            return next(iter(target_ids))
        return ''

    def _place_node_inside_function_box(
        self: Any,
        node: AcherionNode,
        box_id: str,
    ) -> None:
        box = self._node_by_id(box_id)
        if box is None or not self._is_function_box(box):
            return
        visible_children = [
            child for child in self._visible_function_child_nodes(box_id)
            if child.node_id != node.node_id
        ]
        if visible_children:
            node.params['x'] = max(
                self._node_world_left(box) + 220,
                max(
                    self._node_world_left(child)
                    for child in visible_children
                ),
            )
            node.params['y'] = max(
                self._node_world_top(box) + 116,
                max(
                    self._node_world_top(child)
                    for child in visible_children
                )
                + _NODE_STEP,
            )
        else:
            node.params['x'] = self._node_world_left(box) + 220
            node.params['y'] = self._node_world_top(box) + 116
        node.params['parent_function'] = box_id

    def _build_function_entry_node(
        self: Any,
        box: AcherionNode,
    ) -> AcherionNode:
        entry = _default_node('function_entry')
        entry.node_id = self._function_entry_node_id(box.node_id)
        entry.title = 'Entry'
        entry.params['parent_function'] = box.node_id
        entry.params['manual_position'] = True
        entry.params['dock'] = 'free'
        entry.params['x'] = self._node_world_left(box) + 48
        entry.params['y'] = self._node_world_top(box) + 116
        return entry

    def _ensure_function_box_entries(self: Any) -> None:
        existing_ids = {node.node_id for node in self._graph.nodes}
        new_entries: list[AcherionNode] = []
        for box in [node for node in self._manual_nodes() if self._is_function_box(node)]:
            entry = self._function_entry_node(box.node_id)
            expected_id = self._function_entry_node_id(box.node_id)
            if entry is not None:
                if entry.node_id != expected_id and expected_id not in existing_ids:
                    existing_ids.discard(entry.node_id)
                    entry.node_id = expected_id
                    existing_ids.add(expected_id)
                entry.title = 'Entry'
                entry.params['parent_function'] = box.node_id
                continue
            if expected_id in existing_ids:
                continue
            new_entry = self._build_function_entry_node(box)
            new_entries.append(new_entry)
            existing_ids.add(new_entry.node_id)
        if new_entries:
            self._graph.nodes.extend(new_entries)

    def _prune_obsolete_function_io_nodes(self: Any) -> None:
        removed_node_ids = {
            node.node_id
            for node in self._graph.nodes
            if self._is_function_input(node) or self._is_function_output(node)
        }
        if removed_node_ids:
            self._graph.nodes = [
                node
                for node in self._graph.nodes
                if node.node_id not in removed_node_ids
            ]
            self._clear_removed_source_refs(
                removed_node_ids=removed_node_ids,
                removed_source_ids=set(),
            )
        for node in self._graph.nodes:
            if self._is_function_box(node):
                self._prune_box_io_metadata(node)

    def _function_box_boundary_input_sources(self: Any, box_id: str) -> list[str]:
        sources: list[str] = []
        seen_sources: set[str] = set()
        for node in self._graph.nodes:
            if self._is_function_input(node) or self._is_function_output(node):
                continue
            if not self._node_has_function_ancestor(node.node_id, box_id):
                continue
            for pin in self._input_pin_specs(node):
                source_id = str(self._input_source_id(node, pin['pin_id']) or '')
                if not source_id or source_id in seen_sources:
                    continue
                source_node = self._node_by_id(self._pure_node_id(source_id))
                if source_node is None:
                    continue
                if source_node.node_id == box_id:
                    continue
                if self._node_has_function_ancestor(source_node.node_id, box_id):
                    continue
                seen_sources.add(source_id)
                sources.append(source_id)
        return sources

    def _function_box_boundary_output_sources(self: Any, box_id: str) -> list[str]:
        sources: list[str] = []
        seen_sources: set[str] = set()
        for node in self._graph.nodes:
            if self._is_function_input(node) or self._is_function_output(node):
                continue
            if self._node_has_function_ancestor(node.node_id, box_id):
                continue
            for pin in self._input_pin_specs(node):
                source_id = str(self._input_source_id(node, pin['pin_id']) or '')
                if not source_id or source_id in seen_sources:
                    continue
                source_node = self._node_by_id(self._pure_node_id(source_id))
                if source_node is None:
                    continue
                if not self._node_has_function_ancestor(
                    source_node.node_id,
                    box_id,
                ):
                    continue
                seen_sources.add(source_id)
                sources.append(source_id)
        return sources

    def _function_box_pin_type_from_source(self: Any, source_id: str) -> str:
        source_node = self._node_by_id(self._pure_node_id(source_id))
        if source_node is None:
            return 'any'
        pin_index = self._source_pin_index(source_id)
        specs = self._output_pin_specs(source_node)
        if pin_index < len(specs):
            return str(specs[pin_index].get('type') or 'any')
        return 'any'

    @staticmethod
    def _is_auto_function_port_label(label: str, prefix: str) -> bool:
        stripped = label.strip().lower()
        return not stripped or stripped == prefix or stripped.startswith(f'{prefix} ')

    def _sync_function_box_ports(self: Any) -> None:
        self._prune_obsolete_function_io_nodes()

    def _source_inside_function_box(
        self,
        source_id: str,
        box_id: str,
    ) -> bool:
        owner = cast(_FunctionBoxOwner, self)
        source_node = owner._node_by_id(owner._pure_node_id(source_id))
        if source_node is None:
            return False
        is_inside: bool = owner._function_parent_id(source_node) == box_id
        return is_inside

    def _handle_function_box_input_click(
        self: Any,
        box: AcherionNode,
        input_node_id: str,
    ) -> None:
        pending = str(self._pending_source_node_id or '')
        if not pending or pending == input_node_id:
            self._start_connection(input_node_id)
            return
        if self._source_inside_function_box(pending, box.node_id):
            self._update_hint(
                'Function-box input pins accept external sources only. '
                'Click the input pin first, then wire it into an inner node.'
            )
            return
        self._connect_input_pin(box, f'fin:{input_node_id}')

    def _handle_function_box_output_click(
        self: Any,
        box: AcherionNode,
        output_node_id: str,
    ) -> None:
        output_node = self._node_by_id(output_node_id)
        if output_node is None:
            return
        pending = str(self._pending_source_node_id or '')
        external_source_id = self._box_output_source_id(box, output_node_id)
        if not pending or pending == external_source_id:
            self._start_connection(external_source_id)
            return
        if not self._source_inside_function_box(pending, box.node_id):
            self._update_hint(
                'Function-box output pins capture internal sources only. '
                'Select a node inside the box, or click the output pin '
                'first for external wiring.'
            )
            return
        self._connect_input_pin(output_node, 'source')

    def _box_output_source_id(self: Any, box: AcherionNode, output_node_id: str) -> str:
        output_order = list(box.params.get('output_order') or [])
        try:
            pin_index = output_order.index(output_node_id)
        except ValueError:
            pin_index = 0
        return f'{box.node_id}@{pin_index}'

    def _prune_box_io_metadata(self: Any, box: AcherionNode) -> None:
        box.params.pop('input_order', None)
        box.params.pop('output_order', None)
        box.params.pop('box_input_sources', None)
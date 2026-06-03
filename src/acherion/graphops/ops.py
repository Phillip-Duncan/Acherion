"""Graph-operations mixin for AcherionDesigner.

Provides system-node sync, node CRUD, connection management, and all
methods that mutate the graph model. Intended to be inherited by
AcherionDesigner only.
"""

import copy
import re
import uuid
from typing import Any, cast

import acherion.node_behaviors as acherion_node_behaviors

from acherion.constants import (
    _GRID_SNAP_SIZE,
    _GROUP_COLOURS,
    _MANUAL_X,
    _MANUAL_Y,
    _NODE_STEP,
    _NODE_TOP,
    _SOURCE_X,
)
from acherion.events import (
    AcherionExternalEvent,
    default_acherion_external_events,
    normalize_acherion_external_events,
)
from acherion.registry import (
    get_acherion_node_definition,
    is_acherion_system_sink_kind,
    is_acherion_system_source_kind,
)
from acherion.model import (
    AcherionNode,
    _default_node,
    _system_node_id,
)


_AcherionLayoutMetric = dict[str, float | int]
_AcherionLayoutMetrics = dict[str, _AcherionLayoutMetric]
_AcherionLayoutBounds = dict[str, float]
_AcherionLayoutTargets = dict[str, tuple[int, int]]
_AcherionLayoutCommandResult = tuple[bool, str | _AcherionLayoutTargets]

_LAYOUT_COMMAND_SPECS: dict[str, tuple[str, object]] = {
    'align_top': ('align', ('y', 'top')),
    'align_middle': ('align', ('y', 'center')),
    'align_bottom': ('align', ('y', 'bottom')),
    'align_left': ('align', ('x', 'left')),
    'align_center': ('align', ('x', 'center')),
    'align_right': ('align', ('x', 'right')),
    'straighten_connections': ('straighten', None),
    'distribute_horizontally': ('distribute', 'x'),
    'distribute_vertically': ('distribute', 'y'),
    'stack_horizontally': ('stack', 'x'),
    'stack_vertically': ('stack', 'y'),
}

_LAYOUT_COMMAND_MESSAGES: dict[str, str] = {
    'align_top': 'Aligned selected nodes to the top edge.',
    'align_middle': 'Aligned selected nodes to the vertical middle.',
    'align_bottom': 'Aligned selected nodes to the bottom edge.',
    'align_left': 'Aligned selected nodes to the left edge.',
    'align_center': 'Aligned selected nodes to the horizontal center.',
    'align_right': 'Aligned selected nodes to the right edge.',
    'straighten_connections': 'Straightened the selected node layout.',
    'distribute_horizontally': 'Distributed selected nodes horizontally.',
    'distribute_vertically': 'Distributed selected nodes vertically.',
    'stack_horizontally': 'Stacked selected nodes horizontally.',
    'stack_vertically': 'Stacked selected nodes vertically.',
}


class _GraphOpsMixin:
    """Graph-mutation methods for AcherionDesigner."""

    _CENTER_ADD_OFFSET = 48
    _CENTER_ADD_MAX_ATTEMPTS = 64
    _COPY_PASTE_OFFSET = _GRID_SNAP_SIZE * 2
    _STACK_GAP = _GRID_SNAP_SIZE

    _selected_connection_id: str | None = None

    @staticmethod
    def _snap_grid_value(value: int | float) -> int:
        return int(round(float(value) / _GRID_SNAP_SIZE) * _GRID_SNAP_SIZE)

    def _snap_grid_point(
        self: Any,
        x: int | float,
        y: int | float,
    ) -> tuple[int, int]:
        return (
            self._snap_grid_value(x),
            self._snap_grid_value(y),
        )

    # --- node predicates ---------------------------------------------------

    @staticmethod
    def _is_system_node(node: AcherionNode) -> bool:
        return bool(node.params.get('system_node'))

    def _is_system_source_node(self: Any, node: AcherionNode) -> bool:
        return self._is_system_node(node) and is_acherion_system_source_kind(
            node.kind
        )

    def _is_system_sink_node(self: Any, node: AcherionNode) -> bool:
        return self._is_system_node(node) and is_acherion_system_sink_kind(
            node.kind
        )

    @staticmethod
    def _pure_node_id(source_id: str) -> str:
        """Strip '@pin_index' suffix from a source id."""
        return source_id.split('@')[0] if source_id and '@' in source_id else (source_id or '')

    @staticmethod
    def _source_pin_index(source_id: str) -> int:
        """Return the output pin index encoded in a source id (default 0)."""
        if source_id and '@' in source_id:
            try:
                return int(source_id.split('@', 1)[1])
            except ValueError:
                return 0
        return 0

    def _manual_nodes(self: Any) -> list[AcherionNode]:
        return [
            n for n in self._graph.nodes if not self._is_system_node(n)
        ]

    def _external_events(self: Any) -> list[AcherionExternalEvent]:
        events: dict[str, AcherionExternalEvent]
        if self._host is not None:
            events = normalize_acherion_external_events(
                self._host.external_events()
            )
        else:
            events = default_acherion_external_events()
        for node in self._manual_nodes():
            definition = get_acherion_node_definition(node.kind)
            if definition is None:
                continue
            for event in definition.external_events(self, node):
                events[event.event_key] = event
        return list(normalize_acherion_external_events(events).values())

    def _sync_manual_schema_keys(self: Any) -> None:
        if self._host is not None:
            self._host.sync_manual_schema_keys(self)

    def _source_nodes(self: Any) -> list[AcherionNode]:
        return [
            n for n in self._graph.nodes if self._is_system_source_node(n)
        ]

    def _sink_nodes(self: Any) -> list[AcherionNode]:
        return [
            n for n in self._graph.nodes if self._is_system_sink_node(n)
        ]

    def _rebuild_graph(
        self: Any,
        manual_nodes: list[AcherionNode],
    ) -> None:
        self._graph.nodes = (
            self._source_nodes() + manual_nodes + self._sink_nodes()
        )
        self._ensure_function_box_entries()
        self._sync_function_box_ports()

    # --- position seeding --------------------------------------------------

    def _take_matching_node(  # type: ignore[return]
        self,
        *,
        consumed_ids: set[str],
        kind: str,
        key: str,
        param_key: str,
    ) -> AcherionNode | None:
        owner = cast(Any, self)
        expected_id = _system_node_id(kind, key)
        for node in owner._graph.nodes:
            if node.node_id in consumed_ids:
                continue
            if node.node_id == expected_id:
                consumed_ids.add(node.node_id)
                matched_node: AcherionNode = node
                return matched_node
            if node.kind != kind:
                continue
            if str(node.params.get(param_key) or '').strip() != key:
                continue
            consumed_ids.add(node.node_id)
            matched_node = node
            return matched_node
        return None

    def _seed_position(
        self: Any,
        node: AcherionNode,
        *,
        group: str,
        index: int,
    ) -> None:
        if bool(node.params.get('manual_position')):
            return
        if group == 'source':
            node.params.setdefault('dock', 'left')
            node.params.setdefault('y', _NODE_TOP + (index * _NODE_STEP))
            return
        if group == 'sink':
            node.params.setdefault('dock', 'right')
            node.params.setdefault('y', _NODE_TOP + (index * _NODE_STEP))
            return
        node.params.setdefault('dock', 'free')
        node.params.setdefault('x', _MANUAL_X)
        node.params.setdefault('y', _MANUAL_Y + (index * _NODE_STEP))

    def _rects_overlap(
        self: Any,
        *,
        left: int,
        top: int,
        width: int,
        height: int,
        other_left: int,
        other_top: int,
        other_width: int,
        other_height: int,
        padding: int = 24,
    ) -> bool:
        return not (
            (left + width + padding) <= other_left
            or left >= (other_left + other_width + padding)
            or (top + height + padding) <= other_top
            or top >= (other_top + other_height + padding)
        )

    def _visible_node_collision(
        self: Any,
        node: AcherionNode,
        *,
        left: int,
        top: int,
    ) -> bool:
        width = self._node_width(node)
        height = self._node_height(node)
        owner = cast(Any, self)
        for other_node in owner._graph.nodes:
            if other_node.node_id == node.node_id:
                continue
            if (
                owner._is_function_input(other_node)
                or owner._is_function_output(other_node)
                or owner._is_function_entry(other_node)
            ):
                continue
            if self._rects_overlap(
                left=left,
                top=top,
                width=width,
                height=height,
                other_left=self._node_world_left(other_node),
                other_top=self._node_world_top(other_node),
                other_width=self._node_width(other_node),
                other_height=self._node_height(other_node),
            ):
                return True
        return False

    def _resolve_centered_manual_position(
        self: Any,
        node: AcherionNode,
        *,
        center_x: int,
        center_y: int,
    ) -> tuple[int, int]:
        width = self._node_width(node)
        height = self._node_height(node)
        base_left = center_x - max(1, width // 2)
        base_top = center_y - max(1, height // 2)
        for attempt in range(self._CENTER_ADD_MAX_ATTEMPTS):
            offset = attempt * self._CENTER_ADD_OFFSET
            candidate_left = base_left + offset
            candidate_top = base_top + offset
            if not self._visible_node_collision(
                node,
                left=candidate_left,
                top=candidate_top,
            ):
                return candidate_left, candidate_top
        return base_left, base_top

    # --- system node sync --------------------------------------------------

    def _sync_system_nodes(self: Any) -> None:  # noqa: C901
        if self._host is not None:
            self._host.sync_system_nodes(self)
        return

    # --- node CRUD ---------------------------------------------------------

    def _add_node(
        self: Any,
        kind: str,
        center_x: int | None = None,
        center_y: int | None = None,
    ) -> None:
        manual_nodes = self._manual_nodes()
        new_node = _default_node(kind)
        if center_x is not None and center_y is not None:
            left, top = self._resolve_centered_manual_position(
                new_node,
                center_x=center_x,
                center_y=center_y,
            )
            new_node.params['x'] = left
            new_node.params['y'] = top
            new_node.params['dock'] = 'free'
            new_node.params['manual_position'] = True
            new_node.params['parent_function'] = self._containing_function_box_id(
                center_x,
                center_y,
            )
        else:
            self._seed_position(
                new_node, group='manual', index=len(manual_nodes)
            )
            target_box_id = self._selected_function_box_target()
            if target_box_id:
                self._place_node_inside_function_box(new_node, target_box_id)
        self._ensure_custom_function_entry(new_node)
        manual_nodes.append(new_node)
        self._rebuild_graph(manual_nodes)
        self._notify_change()

    def _add_node_at_position(
        self: Any, kind: str, x: int, y: int
    ) -> None:
        """Add a node of kind at a specific canvas position from a drag-drop."""
        manual_nodes = self._manual_nodes()
        new_node = _default_node(kind)
        x, y = self._snap_grid_point(x, y)
        new_node.params['x'] = x
        new_node.params['y'] = y
        new_node.params['dock'] = 'free'
        new_node.params['manual_position'] = True
        center_x = x + max(1, self._node_width(new_node) // 2)
        center_y = y + max(1, self._node_height(new_node) // 2)
        new_node.params['parent_function'] = self._containing_function_box_id(
            center_x,
            center_y,
        )
        self._ensure_custom_function_entry(new_node)
        manual_nodes.append(new_node)
        self._rebuild_graph(manual_nodes)
        self._notify_change()

    def _copy_selection_nodes(self: Any) -> list[AcherionNode]:
        """Return manual nodes currently eligible for clipboard copy."""
        selected_ids = set(self._selected_node_ids)
        if not selected_ids:
            return []
        expanded_ids = set(selected_ids)
        for node in self._manual_nodes():
            if node.node_id not in selected_ids:
                continue
            if not self._is_function_box(node):
                continue
            expanded_ids.update(
                child.node_id
                for child in self._function_box_descendants(node.node_id)
            )
        return [
            node
            for node in self._manual_nodes()
            if node.node_id in expanded_ids
            and not self._is_function_entry(node)
            and not self._is_function_input(node)
            and not self._is_function_output(node)
        ]

    @staticmethod
    def _copy_count_message(action: str, count: int) -> str:
        """Return a short clipboard status message."""
        noun = 'node' if count == 1 else 'nodes'
        return f'{action} {count} {noun}.'

    def _copy_group_snapshot(
        self: Any,
        nodes: list[AcherionNode],
    ) -> dict[str, str]:
        """Return copied group metadata keyed by original group name."""
        snapshot: dict[str, str] = {}
        for node in nodes:
            group_name = str(node.params.get('group') or '').strip()
            if not group_name or group_name in snapshot:
                continue
            snapshot[group_name] = str(
                self._graph.groups.get(group_name) or self._next_group_colour()
            )
        return snapshot

    def _copy_user_function_snapshot(
        self: Any,
        nodes: list[AcherionNode],
    ) -> dict[str, dict[str, Any]]:
        """Return copied custom-function definitions keyed by function path."""
        snapshot: dict[str, dict[str, Any]] = {}
        for node in nodes:
            if node.kind != 'custom_function':
                continue
            function_path = str(node.params.get('function_path') or '').strip()
            if not function_path.startswith('user.'):
                continue
            if function_path in snapshot:
                continue
            snapshot[function_path] = copy.deepcopy(
                dict((self._graph.user_functions or {}).get(function_path) or {})
            )
        return snapshot

    def _copy_selection_to_clipboard(self: Any) -> tuple[bool, str]:
        """Copy the current node selection into the designer clipboard."""
        nodes = self._copy_selection_nodes()
        if not nodes:
            return (False, 'Select nodes or a function box first.')
        self._clipboard_snapshot = {
            'groups': self._copy_group_snapshot(nodes),
            'nodes': [copy.deepcopy(node) for node in nodes],
            'user_functions': self._copy_user_function_snapshot(nodes),
        }
        self._clipboard_paste_count = 0
        return (True, self._copy_count_message('Copied', len(nodes)))

    def _next_group_copy_name(
        self: Any,
        group_name: str,
        reserved_names: set[str],
    ) -> str:
        """Return a unique pasted group name derived from one group."""
        base_name = str(group_name or '').strip() or 'Group'
        candidate = f'{base_name} Copy'
        suffix = 2
        while candidate in reserved_names or candidate in self._graph.groups:
            candidate = f'{base_name} Copy {suffix}'
            suffix += 1
        reserved_names.add(candidate)
        return candidate

    def _next_pasted_function_name(
        self: Any,
        node: AcherionNode,
        reserved_names: set[str],
    ) -> str:
        """Return a unique helper name for a pasted function box."""
        base_name = self._sanitize_identifier(
            str(node.params.get('function_name') or node.title or node.node_id),
            'function_box',
        )
        candidate = f'{base_name}_copy'
        suffix = 2
        while candidate in reserved_names:
            candidate = f'{base_name}_copy_{suffix}'
            suffix += 1
        reserved_names.add(candidate)
        return candidate

    @staticmethod
    def _rename_copied_function_source(
        source_code: str,
        function_name: str,
    ) -> str:
        """Rename the single top-level function defined in copied source."""
        clean_source = str(source_code or '').rstrip()
        clean_name = str(function_name or '').strip()
        if not clean_source or not clean_name:
            return clean_source
        return re.sub(
            r'(^\s*def\s+)[A-Za-z_][A-Za-z0-9_]*(\s*\()',
            rf'\1{clean_name}\2',
            clean_source,
            count=1,
            flags=re.M,
        )

    def _duplicate_custom_function_path(
        self: Any,
        function_path: str,
        copied_user_functions: dict[str, dict[str, Any]],
    ) -> str:
        """Create a detached user-function entry for one pasted node."""
        clean_path = str(function_path or '').strip()
        if not clean_path.startswith('user.'):
            return clean_path
        function_name = self._next_custom_function_name()
        new_path = f'user.{function_name}'
        current_data = dict(
            copied_user_functions.get(clean_path)
            or (self._graph.user_functions or {}).get(clean_path)
            or {}
        )
        source_code = self._rename_copied_function_source(
            str(current_data.get('source_code') or ''),
            function_name,
        )
        if not source_code:
            source_code = self._default_custom_function_source(function_name)
        data, _error = self._parse_custom_function_source(source_code)
        if data is None:
            data = {
                'label': function_name,
                'signature': f'{function_name}()',
                'min_args': 0,
                'max_args': 0,
                'param_names': [],
                'param_types': [],
                'return_type': 'any',
                'source_code': source_code.rstrip() + '\n',
            }
        self._graph.user_functions[new_path] = data
        return new_path

    def _remap_copied_source_id(
        self: Any,
        source_id: str,
        node_id_map: dict[str, str],
    ) -> str:
        """Return the pasted source id for one copied connection."""
        clean_source_id = str(source_id or '').strip()
        if not clean_source_id:
            return ''
        pure_node_id = self._pure_node_id(clean_source_id)
        mapped_node_id = node_id_map.get(pure_node_id)
        if mapped_node_id is None:
            return ''
        if '@' not in clean_source_id:
            return mapped_node_id
        return f'{mapped_node_id}@{clean_source_id.split("@", 1)[1]}'

    def _remap_copied_node_params(
        self: Any,
        node: AcherionNode,
        node_id_map: dict[str, str],
    ) -> None:
        """Rewrite internal source references on one pasted node clone."""
        exec_sources = [
            self._remap_copied_source_id(source_id, node_id_map)
            for source_id in list(node.params.get('exec_sources') or [])
        ]
        node.params['exec_sources'] = [
            source_id for source_id in exec_sources if source_id
        ]

        if 'arg_sources' in node.params:
            node.params['arg_sources'] = [
                self._remap_copied_source_id(source_id, node_id_map)
                for source_id in list(node.params.get('arg_sources') or [])
            ]

        if 'named_sources' in node.params:
            node.params['named_sources'] = {
                param_name: mapped_source_id
                for param_name, source_id in dict(
                    node.params.get('named_sources') or {}
                ).items()
                for mapped_source_id in [
                    self._remap_copied_source_id(source_id, node_id_map)
                ]
                if mapped_source_id
            }

        if 'box_input_sources' in node.params:
            node.params['box_input_sources'] = {
                input_node_id: mapped_source_id
                for input_node_id, source_id in dict(
                    node.params.get('box_input_sources') or {}
                ).items()
                for mapped_source_id in [
                    self._remap_copied_source_id(source_id, node_id_map)
                ]
                if mapped_source_id
            }

        definition = get_acherion_node_definition(node.kind)
        if definition is None:
            return
        for param_id in definition.source_param_ids(node):
            node.params[param_id] = self._remap_copied_source_id(
                str(node.params.get(param_id) or ''),
                node_id_map,
            )

    def _next_pasted_node_id(self: Any, existing_ids: set[str]) -> str:
        """Return a unique node id for one pasted node."""
        while True:
            node_id = uuid.uuid4().hex[:8]
            if node_id in existing_ids:
                continue
            existing_ids.add(node_id)
            return node_id

    def _pasted_selection_offset(
        self: Any,
        copied_nodes: list[AcherionNode],
        *,
        anchor_x: int | None,
        anchor_y: int | None,
    ) -> tuple[int, int]:
        """Return world-space paste offset for copied nodes."""
        if anchor_x is None or anchor_y is None:
            offset = self._COPY_PASTE_OFFSET * (self._clipboard_paste_count + 1)
            return (offset, offset)
        snapped_anchor_x, snapped_anchor_y = self._snap_grid_point(
            anchor_x,
            anchor_y,
        )
        min_left = min(self._node_world_left(node) for node in copied_nodes)
        min_top = min(self._node_world_top(node) for node in copied_nodes)
        return (
            snapped_anchor_x - min_left,
            snapped_anchor_y - min_top,
        )

    def _anchor_pasted_parent_function(
        self: Any,
        node: AcherionNode,
        *,
        left: int,
        top: int,
    ) -> str:
        """Return target parent function for one cursor-anchored paste."""
        if self._is_function_box(node):
            return ''
        center_x = left + max(1, self._node_width(node) // 2)
        center_y = top + max(1, self._node_height(node) // 2)
        return self._containing_function_box_id(center_x, center_y)

    def _paste_copied_nodes(
        self: Any,
        *,
        anchor_x: int | None = None,
        anchor_y: int | None = None,
    ) -> tuple[bool, str]:
        """Paste the current clipboard nodes with rewritten references."""
        snapshot = dict(self._clipboard_snapshot or {})
        copied_nodes = [
            copy.deepcopy(node)
            for node in list(snapshot.get('nodes') or [])
            if isinstance(node, AcherionNode)
        ]
        copied_user_functions = {
            str(path): copy.deepcopy(dict(data))
            for path, data in dict(snapshot.get('user_functions') or {}).items()
            if isinstance(path, str) and isinstance(data, dict)
        }
        if not copied_nodes:
            return (False, 'Copy nodes first.')

        offset_x, offset_y = self._pasted_selection_offset(
            copied_nodes,
            anchor_x=anchor_x,
            anchor_y=anchor_y,
        )
        node_id_map: dict[str, str] = {}
        existing_ids = {node.node_id for node in self._graph.nodes}
        for node in copied_nodes:
            node_id_map[node.node_id] = self._next_pasted_node_id(existing_ids)
        for node in copied_nodes:
            if not self._is_function_box(node):
                continue
            node_id_map[self._function_entry_node_id(node.node_id)] = (
                self._function_entry_node_id(node_id_map[node.node_id])
            )

        reserved_group_names = set(self._graph.groups)
        group_name_map: dict[str, str] = {}
        for group_name, colour in dict(snapshot.get('groups') or {}).items():
            pasted_group_name = self._next_group_copy_name(
                group_name,
                reserved_group_names,
            )
            group_name_map[str(group_name)] = pasted_group_name
            self._graph.groups[pasted_group_name] = str(
                colour or self._next_group_colour()
            )

        reserved_function_names = {
            str(node.params.get('function_name') or '').strip()
            for node in self._manual_nodes()
            if self._is_function_box(node)
        }
        pasted_nodes: list[AcherionNode] = []
        for original_node in copied_nodes:
            pasted_node = copy.deepcopy(original_node)
            pasted_node.node_id = node_id_map[original_node.node_id]
            pasted_node.params = copy.deepcopy(pasted_node.params)
            left = self._node_world_left(original_node) + offset_x
            top = self._node_world_top(original_node) + offset_y
            pasted_left, pasted_top = self._snap_grid_point(left, top)
            pasted_node.params['x'] = pasted_left
            pasted_node.params['y'] = pasted_top
            pasted_node.params['dock'] = 'free'
            pasted_node.params['manual_position'] = True

            parent_function_id = str(
                original_node.params.get('parent_function') or ''
            ).strip()
            if parent_function_id:
                mapped_parent_id = node_id_map.get(parent_function_id, '')
                if mapped_parent_id:
                    pasted_node.params['parent_function'] = mapped_parent_id
                elif anchor_x is None or anchor_y is None:
                    pasted_node.params['parent_function'] = parent_function_id
                else:
                    anchored_parent_id = self._anchor_pasted_parent_function(
                        pasted_node,
                        left=pasted_left,
                        top=pasted_top,
                    )
                    if anchored_parent_id:
                        pasted_node.params['parent_function'] = (
                            anchored_parent_id
                        )
                    else:
                        pasted_node.params.pop('parent_function', None)
            else:
                if anchor_x is None or anchor_y is None:
                    pasted_node.params.pop('parent_function', None)
                else:
                    anchored_parent_id = self._anchor_pasted_parent_function(
                        pasted_node,
                        left=pasted_left,
                        top=pasted_top,
                    )
                    if anchored_parent_id:
                        pasted_node.params['parent_function'] = (
                            anchored_parent_id
                        )
                    else:
                        pasted_node.params.pop('parent_function', None)

            group_name = str(original_node.params.get('group') or '').strip()
            if group_name in group_name_map:
                pasted_node.params['group'] = group_name_map[group_name]
            else:
                pasted_node.params.pop('group', None)

            if self._is_function_box(pasted_node):
                pasted_node.params['function_name'] = (
                    self._next_pasted_function_name(
                        original_node,
                        reserved_function_names,
                    )
                )

            if pasted_node.kind == 'custom_function':
                new_path = self._duplicate_custom_function_path(
                    str(original_node.params.get('function_path') or ''),
                    copied_user_functions,
                )
                pasted_node.params['function_path'] = new_path
                pasted_node.params['module'] = self._function_path_to_module(
                    new_path
                )

            self._remap_copied_node_params(pasted_node, node_id_map)
            pasted_nodes.append(pasted_node)

        manual_nodes = self._manual_nodes()
        manual_nodes.extend(pasted_nodes)
        self._rebuild_graph(manual_nodes)
        self._selected_connection_id = None
        self._selected_node_ids = {
            node.node_id for node in pasted_nodes
        }
        self._clipboard_paste_count += 1
        self._notify_change()
        return (True, self._copy_count_message('Pasted', len(pasted_nodes)))

    def _move_node(self: Any, node_id: str, direction: int) -> None:
        manual_nodes = self._manual_nodes()
        old_index = next(
            (
                i for i, n in enumerate(manual_nodes)
                if n.node_id == node_id
            ),
            -1,
        )
        if old_index < 0:
            return
        new_index = max(0, min(len(manual_nodes) - 1, old_index + direction))
        if old_index == new_index:
            return
        node = manual_nodes.pop(old_index)
        manual_nodes.insert(new_index, node)
        self._rebuild_graph(manual_nodes)
        self._notify_change()

    def _selected_layout_nodes(self: Any) -> list[AcherionNode]:
        selected_ids = set(self._selected_node_ids)
        if not selected_ids:
            return []
        selected_nodes = [
            node for node in self._graph.nodes
            if node.node_id in selected_ids and not self._is_function_entry(node)
        ]
        selected_box_ids = {
            node.node_id
            for node in selected_nodes
            if self._is_function_box(node)
        }
        return [
            node
            for node in selected_nodes
            if not any(
                box_id != node.node_id
                and self._node_has_function_ancestor(node.node_id, box_id)
                for box_id in selected_box_ids
            )
        ]

    def _layout_metrics(
        self: Any,
        node: AcherionNode,
    ) -> _AcherionLayoutMetric:
        left = int(self._node_world_left(node))
        top = int(self._node_world_top(node))
        width = int(self._node_width(node))
        height = int(self._node_height(node))
        return {
            'left': left,
            'top': top,
            'right': left + width,
            'bottom': top + height,
            'width': width,
            'height': height,
            'center_x': left + (width / 2.0),
            'center_y': top + (height / 2.0),
        }

    def _function_box_descendants(
        self: Any,
        box_id: str,
    ) -> list[AcherionNode]:
        return [
            node
            for node in self._manual_nodes()
            if node.node_id != box_id
            and self._node_has_function_ancestor(node.node_id, box_id)
        ]

    @staticmethod
    def _median(values: list[float]) -> float:
        ordered = sorted(values)
        mid = len(ordered) // 2
        if len(ordered) % 2:
            return ordered[mid]
        return (ordered[mid - 1] + ordered[mid]) / 2.0

    def _apply_layout_positions(
        self: Any,
        nodes: list[AcherionNode],
        targets: _AcherionLayoutTargets,
    ) -> bool:
        if not targets:
            return False
        current_positions = {
            node.node_id: (
                int(self._node_world_left(node)),
                int(self._node_world_top(node)),
            )
            for node in self._graph.nodes
        }
        resolved_targets = {
            node_id: self._snap_grid_point(left, top)
            for node_id, (left, top) in targets.items()
        }
        for node in nodes:
            if not self._is_function_box(node):
                continue
            current_left, current_top = current_positions.get(
                node.node_id,
                (0, 0),
            )
            target_left, target_top = resolved_targets.get(
                node.node_id,
                (current_left, current_top),
            )
            delta_x = target_left - current_left
            delta_y = target_top - current_top
            if delta_x == 0 and delta_y == 0:
                continue
            for child in self._function_box_descendants(node.node_id):
                child_left, child_top = current_positions.get(
                    child.node_id,
                    (
                        int(self._node_world_left(child)),
                        int(self._node_world_top(child)),
                    ),
                )
                resolved_targets[child.node_id] = self._snap_grid_point(
                    child_left + delta_x,
                    child_top + delta_y,
                )

        changed = False
        moved_nodes: list[tuple[AcherionNode, int, int]] = []
        for node_id, (left, top) in resolved_targets.items():
            node = self._node_by_id(node_id)
            if node is None:
                continue
            current_left, current_top = current_positions.get(
                node_id,
                (left, top),
            )
            if current_left == left and current_top == top:
                continue
            node.params['x'] = left
            node.params['y'] = top
            node.params['dock'] = 'free'
            node.params['manual_position'] = True
            moved_nodes.append((node, left, top))
            changed = True
        if not changed:
            return False
        for moved_node, left, top in moved_nodes:
            self._assign_node_to_containing_function_box(moved_node, left, top)
        self._notify_change()
        return True

    @staticmethod
    def _layout_selection_bounds(
        metrics: _AcherionLayoutMetrics,
    ) -> _AcherionLayoutBounds:
        left = min(float(data['left']) for data in metrics.values())
        top = min(float(data['top']) for data in metrics.values())
        right = max(float(data['right']) for data in metrics.values())
        bottom = max(float(data['bottom']) for data in metrics.values())
        return {
            'left': left,
            'top': top,
            'right': right,
            'bottom': bottom,
            'center_x': (left + right) / 2.0,
            'center_y': (top + bottom) / 2.0,
        }

    @staticmethod
    def _ordered_layout_nodes(
        nodes: list[AcherionNode],
        metrics: _AcherionLayoutMetrics,
        *,
        primary: str,
        secondary: str,
    ) -> list[AcherionNode]:
        return sorted(
            nodes,
            key=lambda node: (
                float(metrics[node.node_id][primary]),
                float(metrics[node.node_id][secondary]),
            ),
        )

    def _layout_axis_center_targets(
        self: Any,
        nodes: list[AcherionNode],
        metrics: _AcherionLayoutMetrics,
        *,
        axis: str,
        center_value: float,
    ) -> _AcherionLayoutTargets:
        targets: _AcherionLayoutTargets = {}
        for node in nodes:
            data = metrics[node.node_id]
            if axis == 'y':
                targets[node.node_id] = (
                    int(data['left']),
                    self._snap_grid_value(
                        center_value - (float(data['height']) / 2.0)
                    ),
                )
                continue
            targets[node.node_id] = (
                self._snap_grid_value(
                    center_value - (float(data['width']) / 2.0)
                ),
                int(data['top']),
            )
        return targets

    def _layout_align_targets(
        self: Any,
        nodes: list[AcherionNode],
        metrics: _AcherionLayoutMetrics,
        bounds: _AcherionLayoutBounds,
        *,
        axis: str,
        anchor: str,
    ) -> _AcherionLayoutTargets:
        if anchor == 'center':
            return self._layout_axis_center_targets(
                nodes,
                metrics,
                axis=axis,
                center_value=float(bounds['center_y' if axis == 'y' else 'center_x']),
            )

        targets: _AcherionLayoutTargets = {}
        for node in nodes:
            data = metrics[node.node_id]
            if axis == 'y':
                anchor_values = {
                    'top': float(bounds['top']),
                    'bottom': float(bounds['bottom']) - float(data['height']),
                }
                targets[node.node_id] = (
                    int(data['left']),
                    self._snap_grid_value(anchor_values[anchor]),
                )
                continue
            anchor_values = {
                'left': float(bounds['left']),
                'right': float(bounds['right']) - float(data['width']),
            }
            targets[node.node_id] = (
                self._snap_grid_value(anchor_values[anchor]),
                int(data['top']),
            )
        return targets

    def _layout_straighten_targets(
        self: Any,
        nodes: list[AcherionNode],
        metrics: _AcherionLayoutMetrics,
        bounds: _AcherionLayoutBounds,
    ) -> _AcherionLayoutTargets:
        horizontal = (
            (float(bounds['right']) - float(bounds['left']))
            >= (float(bounds['bottom']) - float(bounds['top']))
        )
        if horizontal:
            target_center = self._median([
                float(data['center_y']) for data in metrics.values()
            ])
            return self._layout_axis_center_targets(
                nodes,
                metrics,
                axis='y',
                center_value=target_center,
            )
        target_center = self._median([
            float(data['center_x']) for data in metrics.values()
        ])
        return self._layout_axis_center_targets(
            nodes,
            metrics,
            axis='x',
            center_value=target_center,
        )

    def _layout_distribute_targets(
        self: Any,
        nodes: list[AcherionNode],
        metrics: _AcherionLayoutMetrics,
        bounds: _AcherionLayoutBounds,
        *,
        axis: str,
    ) -> _AcherionLayoutCommandResult:
        if len(nodes) < 3:
            if axis == 'x':
                return (
                    False,
                    'Select at least three nodes to distribute horizontally.',
                )
            return (
                False,
                'Select at least three nodes to distribute vertically.',
            )

        if axis == 'x':
            ordered = self._ordered_layout_nodes(
                nodes,
                metrics,
                primary='left',
                secondary='top',
            )
            total_size = sum(
                float(metrics[node.node_id]['width']) for node in ordered
            )
            gap = max(
                0.0,
                (float(bounds['right']) - float(bounds['left']) - total_size)
                / (len(ordered) - 1),
            )
            cursor = float(bounds['left'])
            targets: _AcherionLayoutTargets = {}
            for node in ordered:
                data = metrics[node.node_id]
                targets[node.node_id] = (
                    self._snap_grid_value(cursor),
                    int(data['top']),
                )
                cursor += float(data['width']) + gap
            return (True, targets)

        ordered = self._ordered_layout_nodes(
            nodes,
            metrics,
            primary='top',
            secondary='left',
        )
        total_size = sum(
            float(metrics[node.node_id]['height']) for node in ordered
        )
        gap = max(
            0.0,
            (float(bounds['bottom']) - float(bounds['top']) - total_size)
            / (len(ordered) - 1),
        )
        cursor = float(bounds['top'])
        targets = {}
        for node in ordered:
            data = metrics[node.node_id]
            targets[node.node_id] = (
                int(data['left']),
                self._snap_grid_value(cursor),
            )
            cursor += float(data['height']) + gap
        return (True, targets)

    def _layout_stack_targets(
        self: Any,
        nodes: list[AcherionNode],
        metrics: _AcherionLayoutMetrics,
        bounds: _AcherionLayoutBounds,
        *,
        axis: str,
    ) -> _AcherionLayoutTargets:
        if axis == 'x':
            ordered = self._ordered_layout_nodes(
                nodes,
                metrics,
                primary='left',
                secondary='top',
            )
            cursor = float(bounds['left'])
            targets: _AcherionLayoutTargets = {}
            for node in ordered:
                data = metrics[node.node_id]
                targets[node.node_id] = self._snap_grid_point(
                    cursor,
                    float(bounds['center_y']) - (float(data['height']) / 2.0),
                )
                cursor += float(data['width']) + self._STACK_GAP
            return targets

        ordered = self._ordered_layout_nodes(
            nodes,
            metrics,
            primary='top',
            secondary='left',
        )
        cursor = float(bounds['top'])
        targets = {}
        for node in ordered:
            data = metrics[node.node_id]
            targets[node.node_id] = self._snap_grid_point(
                float(bounds['center_x']) - (float(data['width']) / 2.0),
                cursor,
            )
            cursor += float(data['height']) + self._STACK_GAP
        return targets

    def _layout_selected_nodes(
        self: Any,
        command: str,
    ) -> tuple[bool, str]:
        nodes = self._selected_layout_nodes()
        if len(nodes) < 2:
            return (False, 'Select at least two nodes first.')

        metrics: _AcherionLayoutMetrics = {
            node.node_id: self._layout_metrics(node)
            for node in nodes
        }
        bounds = self._layout_selection_bounds(metrics)
        command_spec = _LAYOUT_COMMAND_SPECS.get(command)
        if command_spec is None:
            return (False, 'Unknown layout command.')

        mode, config = command_spec
        dispatchers = {
            'align': lambda raw: (
                True,
                self._layout_align_targets(
                    nodes,
                    metrics,
                    bounds,
                    axis=cast(tuple[str, str], raw)[0],
                    anchor=cast(tuple[str, str], raw)[1],
                ),
            ),
            'straighten': lambda _raw: (
                True,
                self._layout_straighten_targets(nodes, metrics, bounds),
            ),
            'distribute': lambda raw: self._layout_distribute_targets(
                nodes,
                metrics,
                bounds,
                axis=cast(str, raw),
            ),
            'stack': lambda raw: (
                True,
                self._layout_stack_targets(
                    nodes,
                    metrics,
                    bounds,
                    axis=cast(str, raw),
                ),
            ),
        }
        ok, payload = dispatchers[mode](config)
        if not ok:
            return (False, cast(str, payload))
        targets = cast(_AcherionLayoutTargets, payload)

        if not self._apply_layout_positions(nodes, targets):
            return (True, 'Selection already matches that layout.')
        return (
            True,
            _LAYOUT_COMMAND_MESSAGES.get(
                command,
                'Updated selected node layout.',
            ),
        )

    def _delete_node(self: Any, node_id: str) -> None:
        node = self._node_by_id(node_id)
        if node is not None and self._is_function_entry(node):
            return
        manual_nodes = self._manual_nodes()
        if any(node.node_id == node_id and self._is_function_box(node) for node in manual_nodes):
            child_ids = {
                node.node_id for node in manual_nodes
                if self._function_parent_id(node) == node_id
            }
            child_ids.add(node_id)
            self._delete_nodes_batch(child_ids)
            return
        self._clear_removed_source_refs(
            removed_node_ids={node_id},
            removed_source_ids=set(),
        )
        manual_nodes = [
            n for n in self._manual_nodes() if n.node_id != node_id
        ]
        self._rebuild_graph(manual_nodes)
        self._cleanup_custom_function_entries()
        for node in manual_nodes:
            if self._is_function_box(node):
                self._prune_box_io_metadata(node)
        self._cleanup_empty_groups()
        self._notify_change()

    def _delete_nodes_batch(self: Any, node_ids: set[str]) -> None:
        if not node_ids:
            return
        manual_nodes = self._manual_nodes()
        expanded_ids = {
            node_id for node_id in node_ids
            if not any(
                node.node_id == node_id and self._is_function_entry(node)
                for node in manual_nodes
            )
        }
        for node in manual_nodes:
            if node.node_id in node_ids and self._is_function_box(node):
                expanded_ids.update(
                    child.node_id
                    for child in manual_nodes
                    if self._function_parent_id(child) == node.node_id
                )
        self._clear_removed_source_refs(
            removed_node_ids=expanded_ids,
            removed_source_ids=set(),
        )
        manual_nodes = [
            n for n in manual_nodes
            if n.node_id not in expanded_ids
        ]
        self._rebuild_graph(manual_nodes)
        self._cleanup_custom_function_entries()
        for node in manual_nodes:
            if self._is_function_box(node):
                self._prune_box_io_metadata(node)
        self._cleanup_empty_groups()
        self._notify_change()

    # --- group management -------------------------------------------------

    def _next_group_colour(self: Any) -> str:
        """Return next unused colour from the palette."""
        used = set(self._graph.groups.values())
        for colour in _GROUP_COLOURS:
            if colour not in used:
                return str(colour)
        return str(_GROUP_COLOURS[
            len(self._graph.groups) % len(_GROUP_COLOURS)
        ])

    def _create_group(self: Any, name: str, node_ids: set[str]) -> None:
        """Create a named group and assign selected nodes to it."""
        name = name.strip()
        if not name or name in self._graph.groups:
            return
        self._graph.groups[name] = self._next_group_colour()
        for node in self._graph.nodes:
            if node.node_id in node_ids:
                node.params['group'] = name
        self._notify_change()

    def _add_nodes_to_group(self: Any, name: str, node_ids: set[str]) -> None:
        """Move nodes into an existing group."""
        if name not in self._graph.groups:
            return
        for node in self._graph.nodes:
            if node.node_id in node_ids:
                node.params['group'] = name
        self._notify_change()

    def _remove_nodes_from_group(self: Any, node_ids: set[str]) -> None:
        """Remove nodes from their current group; prune empty groups."""
        for node in self._graph.nodes:
            if node.node_id in node_ids:
                node.params.pop('group', None)
        self._cleanup_empty_groups()
        self._notify_change()

    def _cleanup_empty_groups(self: Any) -> None:
        """Delete groups that have no member nodes."""
        members: set[str] = {
            str(n.params['group'])
            for n in self._graph.nodes
            if n.params.get('group')
        }
        self._graph.groups = {
            k: v
            for k, v in self._graph.groups.items()
            if k in members
        }

    def _extract_function_from_selection(
        self: Any,
        name: str,
        *,
        return_node_id: str | None = None,
    ) -> tuple[bool, str]:
        """Extract selected nodes into a composite function box."""
        selected_ids = set(self._selected_node_ids)
        if not selected_ids:
            return (False, 'Select nodes first.')

        selected_nodes = [
            node for node in self._manual_nodes()
            if node.node_id in selected_ids
        ]
        if len(selected_nodes) != len(selected_ids):
            return (False, 'Only manual nodes can be extracted into a function.')

        if any(self._is_function_box(node) for node in selected_nodes):
            return (False, 'Selecting a function box for extraction is not supported.')
        if any(
            self._is_function_input(node) or self._is_function_output(node)
            for node in selected_nodes
        ):
            return (False, 'Function input/output nodes cannot be re-extracted.')
        if any(self._is_function_entry(node) for node in selected_nodes):
            return (False, 'Function entry nodes cannot be re-extracted.')
        parent_ids = {
            self._function_parent_id(node) for node in selected_nodes
        }
        if len(parent_ids) > 1:
            return (
                False,
                'Select nodes from the same function scope.',
            )
        common_parent_id = next(iter(parent_ids), '')

        unsupported_kinds = {
            'for_each',
            'collect',
            'branch_route',
        }
        bad_kinds = sorted({
            node.kind
            for node in selected_nodes
            if (
                node.kind in unsupported_kinds
                or acherion_node_behaviors.function_box_unsupported(node)
            )
        })
        if bad_kinds:
            return (
                False,
                'Selection contains unsupported node kinds: '
                + ', '.join(bad_kinds),
            )

        function_slug = self._sanitize_identifier(name, 'function_box')
        manual_nodes = self._manual_nodes()
        insert_index = min(
            index
            for index, node in enumerate(manual_nodes)
            if node.node_id in selected_ids
        )
        box = _default_node('function_box')
        box.title = name.strip() or function_slug.replace('_', ' ').title()
        box.params['function_name'] = function_slug
        box.params['parent_function'] = common_parent_id
        box.params['manual_position'] = True
        box.params['dock'] = 'free'
        box.params['x'] = min(
            self._node_world_left(node) for node in selected_nodes
        ) - 48
        box.params['y'] = min(
            self._node_world_top(node) for node in selected_nodes
        ) - 72

        for node in selected_nodes:
            node.params['parent_function'] = box.node_id
            node.params.pop('group', None)

        new_manual_nodes = manual_nodes[:]
        new_manual_nodes.insert(insert_index, box)

        self._rebuild_graph(new_manual_nodes)
        self._selected_node_ids = {box.node_id}
        self._notify_change()
        return (
            True,
            f'Created function box {function_slug}. Boundary wires now define its inputs and outputs.',
        )




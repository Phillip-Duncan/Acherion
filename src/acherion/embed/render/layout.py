"""Geometry and link rendering mixin for AcherionDesigner."""

# pyright: reportAttributeAccessIssue=false

from __future__ import annotations

from typing import Any, cast

from nicegui import ui

from acherion.catalog import types as _catalog_types
from acherion.constants import (
    _BODY_TOP_PADDING,
    _CANVAS_WORLD_HEIGHT,
    _CANVAS_WORLD_WIDTH,
    _HEADER_HEIGHT,
    _MANUAL_X,
    _NODE_TOP,
    _NODE_WIDTH,
    _PIN_CENTER_OFFSET,
    _PIN_EDGE_OFFSET,
    _PIN_ROW_HEIGHT,
    _SINK_X,
    _SOURCE_X,
)
from acherion.registry import (
    _template_flavor,
)
from acherion.model import AcherionNode
from acherion.render.shared import (
    _DEFAULT_NODE_HEIGHT,
    _FUNCTION_BOX_BOTTOM_PAD,
    _FUNCTION_BOX_MIN_HEIGHT,
    _FUNCTION_BOX_MIN_WIDTH,
    _FUNCTION_BOX_MIN_WIDTH_COMPACT,
    _FUNCTION_BOX_PORT_BOTTOM_PAD,
    _FUNCTION_BOX_PORT_CARD_HEIGHT,
    _FUNCTION_BOX_PORT_GAP,
    _FUNCTION_BOX_PORT_TOP,
    _FUNCTION_BOX_SIDE_PAD,
    _FUNCTION_BOX_SIDE_PAD_COMPACT,
    _FUNCTION_BOX_TOP_PAD,
    _NODE_BODY_GAP,
)


_REROUTE_NODE_HEIGHT = 40
_REROUTE_NODE_WIDTH = 80


class _RenderLayoutMixin:
    """Canvas geometry and SVG link rendering methods."""

    @staticmethod
    def _coord_param(value: object, default: int) -> int:
        """Return an int coordinate while preserving zero and negatives."""
        if value in (None, ''):
            return default
        if isinstance(value, (int, float, str)):
            return int(cast(int | float | str, value))
        return int(str(value))

    def _canvas_origin_x(self) -> int:
        return _CANVAS_WORLD_WIDTH

    def _canvas_origin_y(self) -> int:
        return _CANVAS_WORLD_HEIGHT

    def _world_to_canvas_x(self, value: int) -> int:
        return int(self._canvas_origin_x() + value)

    def _world_to_canvas_y(self, value: int) -> int:
        return int(self._canvas_origin_y() + value)

    def _canvas_to_world_x(self, value: int) -> int:
        return int(value - self._canvas_origin_x())

    def _canvas_to_world_y(self, value: int) -> int:
        return int(value - self._canvas_origin_y())

    def _output_pin_style_tag(
        self: Any,
        node: AcherionNode,
        pin_index: int,
    ) -> str:
        """Return the compact style tag for one output pin."""
        output_specs = self._output_pin_specs(node)
        if pin_index >= len(output_specs):
            return 'any'
        pin_type = str(output_specs[pin_index].get('type') or 'any')
        return _catalog_types.pin_style_tag(pin_type)

    def _canvas_content_height(self) -> int:
        owner = cast(Any, self)
        if not owner._graph.nodes:
            return _CANVAS_WORLD_HEIGHT * 2
        max_y = max(
            top + height
            for _left, top, _width, height in (
                owner._node_bounds(n) for n in owner._graph.nodes
            )
        )
        height: int = int(max(_CANVAS_WORLD_HEIGHT * 2, max_y + 2000))
        return height

    def _canvas_height(self: Any) -> int:
        return int(self._canvas_content_height())

    def _canvas_content_width(self: Any) -> int:
        free_right = max(
            (
                left + width + 96
                for node in self._graph.nodes
                for left, _top, width, _height in [self._node_bounds(node)]
                if bool(node.params.get('manual_position'))
                or str(node.params.get('dock') or 'free') == 'free'
            ),
            default=0,
        )
        return max(_CANVAS_WORLD_WIDTH * 2, free_right + 2000)

    def _canvas_width(self: Any) -> int:
        return int(self._canvas_content_width())

    def _node_bounds(
        self: Any,
        node: AcherionNode,
    ) -> tuple[int, int, int, int]:
        revision = getattr(self, '_graph_cache_revision', None)
        if revision is not None:
            cache_revision = getattr(self, '_node_bounds_cache_revision', -1)
            cache = getattr(self, '_node_bounds_cache', None)
            if cache_revision == revision and isinstance(cache, dict):
                cached = cache.get(node.node_id)
                if cached is not None:
                    return cached
            if cache_revision != revision:
                self._node_bounds_cache_revision = revision
                self._node_bounds_cache = {}
                self._function_box_bounds_cache = {}
        bounds = self._node_bounds_uncached(node)
        if revision is not None:
            self._node_bounds_cache[node.node_id] = bounds
        return bounds

    def _node_bounds_uncached(
        self: Any,
        node: AcherionNode,
    ) -> tuple[int, int, int, int]:
        return (
            self._node_left(node),
            self._node_top(node),
            self._node_width(node),
            self._node_height(node),
        )

    def _function_box_bounds(
        self: Any,
        node: AcherionNode,
    ) -> tuple[int, int, int, int]:
        revision = getattr(self, '_graph_cache_revision', None)
        if revision is not None:
            cache_revision = getattr(self, '_node_bounds_cache_revision', -1)
            cache = getattr(self, '_function_box_bounds_cache', None)
            if cache_revision == revision and isinstance(cache, dict):
                cached = cache.get(node.node_id)
                if cached is not None:
                    return cached
        bounds = self._function_box_bounds_uncached(node)
        if revision is not None:
            if getattr(self, '_node_bounds_cache_revision', -1) != revision:
                self._node_bounds_cache_revision = revision
                self._node_bounds_cache = {}
                self._function_box_bounds_cache = {}
            self._function_box_bounds_cache[node.node_id] = bounds
        return bounds

    def _function_box_bounds_uncached(
        self: Any,
        node: AcherionNode,
    ) -> tuple[int, int, int, int]:
        side_pad = _FUNCTION_BOX_SIDE_PAD_COMPACT
        port_required_height = 0
        members = [
            child for child in self._visible_function_child_nodes(node.node_id)
            if child.node_id != node.node_id
        ]
        base_left = self._world_to_canvas_x(
            self._coord_param(node.params.get('x'), _MANUAL_X)
        )
        base_top = self._world_to_canvas_y(
            self._coord_param(node.params.get('y'), _NODE_TOP)
        )
        if not members:
            return (
                base_left,
                base_top,
                _FUNCTION_BOX_MIN_WIDTH_COMPACT,
                max(_FUNCTION_BOX_MIN_HEIGHT, port_required_height),
            )
        member_bounds = [self._node_bounds(child) for child in members]
        min_x = min(left for left, _top, _width, _height in member_bounds)
        min_y = min(top for _left, top, _width, _height in member_bounds)
        max_x = max(
            left + width
            for left, _top, width, _height in member_bounds
        )
        max_y = max(
            top + height
            for _left, top, _width, height in member_bounds
        )
        left = min_x - side_pad
        top = min_y - _FUNCTION_BOX_TOP_PAD
        width = max(
            _FUNCTION_BOX_MIN_WIDTH_COMPACT,
            (max_x - min_x) + (2 * side_pad),
        )
        height = max(
            _FUNCTION_BOX_MIN_HEIGHT,
            (max_y - min_y)
            + _FUNCTION_BOX_TOP_PAD
            + _FUNCTION_BOX_BOTTOM_PAD,
            port_required_height,
        )
        return (left, top, width, height)

    def _node_world_left(self, node: AcherionNode) -> int:
        owner = cast(Any, self)
        if owner._is_function_box(node):
            return int(
                owner._canvas_to_world_x(owner._function_box_bounds(node)[0])
            )
        dock = str(node.params.get('dock') or 'free')
        if dock == 'left' and not bool(node.params.get('manual_position')):
            return _SOURCE_X
        if dock == 'right' and not bool(node.params.get('manual_position')):
            return _SINK_X
        return int(self._coord_param(node.params.get('x'), _MANUAL_X))

    def _node_world_top(self, node: AcherionNode) -> int:
        owner = cast(Any, self)
        if owner._is_function_box(node):
            return int(
                owner._canvas_to_world_y(owner._function_box_bounds(node)[1])
            )
        return int(self._coord_param(node.params.get('y'), _NODE_TOP))

    def _node_width(self, node: AcherionNode) -> int:
        owner = cast(Any, self)
        if owner._is_function_box(node):
            width: int = int(owner._function_box_bounds(node)[2])
            return width
        if node.kind in {'reroute', 'exec_reroute'}:
            return _REROUTE_NODE_WIDTH
        return _NODE_WIDTH

    def _node_height(self, node: AcherionNode) -> int:
        owner = cast(Any, self)
        if owner._is_function_box(node):
            height: int = int(owner._function_box_bounds(node)[3])
            return height
        if node.kind in {'reroute', 'exec_reroute'}:
            return _REROUTE_NODE_HEIGHT
        has_top_exec_row = (
            owner._top_exec_input_pin(node) is not None
            or owner._top_exec_output_pin(node) is not None
        )
        pin_rows = max(
            1,
            owner._body_pin_row_count(node) + int(has_top_exec_row),
        )
        body_height = (2 * _BODY_TOP_PADDING) + (pin_rows * _PIN_ROW_HEIGHT)
        body_height += max(0, pin_rows - 1) * _NODE_BODY_GAP
        height = max(_DEFAULT_NODE_HEIGHT, _HEADER_HEIGHT + body_height)
        return height

    def _node_left(self, node: AcherionNode) -> int:
        owner = cast(Any, self)
        if owner._is_function_box(node):
            left: int = int(owner._function_box_bounds(node)[0])
            return left
        return int(self._world_to_canvas_x(self._node_world_left(node)))

    def _node_top(self, node: AcherionNode) -> int:
        owner = cast(Any, self)
        if owner._is_function_box(node):
            top: int = int(owner._function_box_bounds(node)[1])
            return top
        return int(self._world_to_canvas_y(self._node_world_top(node)))

    def _node_style(self: Any, node: AcherionNode) -> str:
        left, top, width, height = self._node_bounds(node)
        style = (
            f'left:{left}px;'
            f' top:{top}px;'
            f' width:{width}px;'
        )
        if self._is_function_box(node):
            style += f' height:{height}px;'
        elif node.kind in {'reroute', 'exec_reroute'}:
            style += f' height:{height}px;'
        return style

    def _node_tone_class(self: Any, node: AcherionNode) -> str:
        if self._is_function_box(node):
            return 'ach-tone-composite'
        return f'ach-tone-{_template_flavor(node.kind)}'

    def _pin_anchor(
        self,
        node: AcherionNode,
        *,
        direction: str,
        pin_index: int,
    ) -> tuple[int, int]:
        """Return canvas-pixel (x, y) of a pin's centre for fallback SVG."""
        owner = cast(Any, self)
        if owner._is_function_entry(node):
            box = owner._node_by_id(owner._function_parent_id(node))
            if box is not None:
                left = owner._node_left(box)
                top = owner._node_top(box)
                # Compact internal entry pin sits above the first side-port row,
                # not on a standard node header/body boundary.
                y = top + _FUNCTION_BOX_PORT_TOP - (
                    _FUNCTION_BOX_PORT_CARD_HEIGHT // 2
                )
                return (left + (_PIN_EDGE_OFFSET * 2), y)
        if node.kind in {'reroute', 'exec_reroute'}:
            left, top, width, height = owner._node_bounds(node)
            y = top + (height // 2)
            if direction == 'in':
                return (left + _PIN_EDGE_OFFSET, y)
            return (left + width - _PIN_EDGE_OFFSET, y)
        left, top, width, _height = owner._node_bounds(node)
        top_exec_input = owner._top_exec_input_pin(node)
        top_exec_output = owner._top_exec_output_pin(node)
        has_top_exec_row = (
            top_exec_input is not None
            or top_exec_output is not None
        )
        if direction == 'in':
            if top_exec_input is not None and pin_index == top_exec_input[0]:
                row_index = 0
            else:
                row_index = int(has_top_exec_row) + owner._body_pin_row_index(
                    node,
                    direction='in',
                    pin_index=pin_index,
                )
        else:
            if node.kind == 'else_if_branch':
                row_index = max(0, pin_index)
            elif node.kind == 'for_each':
                output_specs = owner._output_pin_specs(node)
                pin_id = (
                    str(output_specs[pin_index].get('pin_id') or '')
                    if pin_index < len(output_specs)
                    else ''
                )
                if pin_id == 'loop_body':
                    row_index = 0
                elif pin_id == 'completed':
                    row_index = 1
                else:
                    row_index = (
                        int(has_top_exec_row)
                        + owner._body_pin_row_index(
                            node,
                            direction='out',
                            pin_index=pin_index,
                        )
                    )
            elif node.kind == 'sequencer' and pin_index == 0:
                row_index = 0
            elif top_exec_output is not None and pin_index == top_exec_output[0]:
                row_index = 0
            else:
                row_index = int(has_top_exec_row) + owner._body_pin_row_index(
                    node,
                    direction='out',
                    pin_index=pin_index,
                )
        y = (
            top
            + _HEADER_HEIGHT
            + _BODY_TOP_PADDING
            + (row_index * _PIN_ROW_HEIGHT)
            + (row_index * _NODE_BODY_GAP)
            + _PIN_CENTER_OFFSET
        )
        if direction == 'in':
            return (left + _PIN_EDGE_OFFSET, y)
        return (left + width - _PIN_EDGE_OFFSET, y)

    def _connection_path_d(self: Any, spec: dict[str, Any]) -> str:
        sx, sy = self._pin_anchor(
            spec['source_node'],
            direction='out',
            pin_index=int(spec.get('out_pin_index', 0)),
        )
        ex, ey = self._pin_anchor(
            spec['target_node'],
            direction='in',
            pin_index=int(spec['input_index']),
        )
        dist = abs(ex - sx)
        t = max(96, min(240, int(dist * 0.55) or 96))
        if ex >= sx:
            c1, c2 = sx + t, ex - t
        else:
            loop = max(140, min(300, int((sx - ex) * 0.7) or 140))
            c1, c2 = sx + loop, ex - loop
        return f'M {sx} {sy} C {c1} {sy}, {c2} {ey}, {ex} {ey}'

    def _render_links(self: Any) -> None:
        specs = self._connection_specs()
        if not specs:
            return
        paths: list[str] = []
        for spec in specs:
            connection_id = str(spec['connection_id'])
            src_id = str(spec['source_node'].node_id)
            tgt_id = str(spec['target_node'].node_id)
            idx = int(spec['input_index'])
            out_idx = int(spec.get('out_pin_index', 0))
            path_d = self._connection_path_d(spec)
            style_tag = self._output_pin_style_tag(spec['source_node'], out_idx)
            path_cls = f'ach-link-path ach-link-path-type-{style_tag}'
            if self._selected_connection_id == connection_id:
                path_cls += ' ach-link-path-selected'
            paths.append(
                f'<path class="{path_cls}" '
                f'data-connection-id="{connection_id}" '
                f'data-source-node-id="{src_id}" '
                f'data-output-index="{out_idx}" '
                f'data-target-node-id="{tgt_id}" '
                f'data-input-index="{idx}" '
                f'd="{path_d}" />'
                f'<path class="ach-link-hitbox" '
                f'data-connection-id="{connection_id}" '
                f'data-source-node-id="{src_id}" '
                f'data-output-index="{out_idx}" '
                f'data-target-node-id="{tgt_id}" '
                f'data-input-index="{idx}" '
                f'd="{path_d}" />'
            )
        ui.html(
            '<svg class="ach-links">'
            + ''.join(paths)
            + '</svg>',
            sanitize=False,
        )

"""Unit tests for node copy/paste graph operations."""

from __future__ import annotations

import pytest

import acherion.graphops.catalog as acherion_graphops_catalog
import acherion.graphops.function_boxes as acherion_graphops_function_boxes
import acherion.graphops.ops as acherion_graphops_ops
import acherion.model as acherion_model


pytestmark = pytest.mark.unit


class _CopyPasteOwner(
    acherion_graphops_catalog._GraphOpsCatalogMixin,
    acherion_graphops_function_boxes._GraphOpsFunctionBoxesMixin,
    acherion_graphops_ops._GraphOpsMixin,
):
    """Minimal graph owner for copy/paste mutation tests."""

    def __init__(self, graph: acherion_model.AcherionGraph) -> None:
        self._graph = graph
        self._host = None
        self._selected_node_ids: set[str] = set()
        self._selected_connection_id: str | None = None
        self._pending_source_node_id: str | None = None
        self._clipboard_snapshot: dict[str, object] | None = None
        self._clipboard_paste_count = 0
        self.change_count = 0

    def _node_by_id(
        self,
        node_id: str,
    ) -> acherion_model.AcherionNode | None:
        pure_id = self._pure_node_id(node_id)
        for node in self._graph.nodes:
            if node.node_id == pure_id:
                return node
        return None

    def _node_world_left(self, node: acherion_model.AcherionNode) -> int:
        return int(node.params.get('x') or 0)

    def _node_world_top(self, node: acherion_model.AcherionNode) -> int:
        return int(node.params.get('y') or 0)

    def _node_width(self, node: acherion_model.AcherionNode) -> int:
        del node
        return 200

    def _node_height(self, node: acherion_model.AcherionNode) -> int:
        del node
        return 120

    def _node_bounds(
        self,
        node: acherion_model.AcherionNode,
    ) -> tuple[int, int, int, int]:
        return (
            self._node_world_left(node),
            self._node_world_top(node),
            self._node_width(node),
            self._node_height(node),
        )

    def _world_to_canvas_x(self, value: int) -> int:
        return int(value)

    def _world_to_canvas_y(self, value: int) -> int:
        return int(value)

    def _canvas_to_world_x(self, value: int) -> int:
        return int(value)

    def _canvas_to_world_y(self, value: int) -> int:
        return int(value)

    def _notify_change(self) -> None:
        self.change_count += 1


def test_copy_paste_selected_group_preserves_internal_links() -> None:
    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id='c1',
                kind='constant',
                params={
                    'group': 'Numbers',
                    'value_type': 'int',
                    'number_value': 1,
                    'x': 0,
                    'y': 0,
                },
            ),
            acherion_model.AcherionNode(
                node_id='c2',
                kind='constant',
                params={
                    'group': 'Numbers',
                    'value_type': 'int',
                    'number_value': 2,
                    'x': 40,
                    'y': 0,
                },
            ),
            acherion_model.AcherionNode(
                node_id='list1',
                kind='make_list',
                params={
                    'group': 'Numbers',
                    'arg_sources': ['c1', 'c2'],
                    'x': 80,
                    'y': 0,
                },
            ),
        ],
        groups={'Numbers': '#112233'},
    )
    owner = _CopyPasteOwner(graph)
    owner._selected_node_ids = {'c1', 'c2', 'list1'}

    copied, copy_message = owner._copy_selection_to_clipboard()

    assert copied is True
    assert copy_message == 'Copied 3 nodes.'

    pasted, paste_message = owner._paste_copied_nodes()

    assert pasted is True
    assert paste_message == 'Pasted 3 nodes.'
    assert owner.change_count == 1
    assert len(owner._selected_node_ids) == 3

    pasted_nodes = [
        node
        for node in owner._manual_nodes()
        if node.node_id in owner._selected_node_ids
    ]
    pasted_list = next(
        node for node in pasted_nodes if node.kind == 'make_list'
    )
    pasted_constants = [
        node for node in pasted_nodes if node.kind == 'constant'
    ]
    pasted_group_names = {
        str(node.params.get('group') or '') for node in pasted_nodes
    }

    assert pasted_group_names == {'Numbers Copy'}
    assert owner._graph.groups['Numbers Copy'] == '#112233'
    assert pasted_list.params['arg_sources'] == [
        pasted_constants[0].node_id,
        pasted_constants[1].node_id,
    ] or pasted_list.params['arg_sources'] == [
        pasted_constants[1].node_id,
        pasted_constants[0].node_id,
    ]
    assert all(int(node.params['x']) >= 40 for node in pasted_nodes)


def test_copy_paste_function_box_includes_descendants() -> None:
    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id='box1',
                kind='function_box',
                title='Function Box',
                params={
                    'function_name': 'function_box',
                    'x': 100,
                    'y': 100,
                },
            ),
            acherion_model.AcherionNode(
                node_id='inner',
                kind='call_function',
                params={
                    'function_path': 'list',
                    'module': 'builtins',
                    'arg_count': 0,
                    'arg_sources': [],
                    'exec_sources': ['box1:entry'],
                    'parent_function': 'box1',
                    'x': 140,
                    'y': 160,
                },
            ),
        ]
    )
    owner = _CopyPasteOwner(graph)
    owner._selected_node_ids = {'box1'}

    copied, _copy_message = owner._copy_selection_to_clipboard()
    pasted, paste_message = owner._paste_copied_nodes()

    assert copied is True
    assert pasted is True
    assert paste_message == 'Pasted 2 nodes.'

    pasted_nodes = [
        node
        for node in owner._manual_nodes()
        if node.node_id in owner._selected_node_ids
    ]
    pasted_box = next(
        node for node in pasted_nodes if node.kind == 'function_box'
    )
    pasted_inner = next(
        node for node in pasted_nodes if node.kind == 'call_function'
    )

    assert pasted_box.node_id != 'box1'
    assert pasted_inner.params['parent_function'] == pasted_box.node_id
    assert pasted_inner.params['exec_sources'] == [
        f'{pasted_box.node_id}:entry'
    ]
    assert pasted_box.params['function_name'] == 'function_box_copy'


def test_paste_at_cursor_places_selection_at_anchor() -> None:
    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id='c1',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 1,
                    'x': 0,
                    'y': 0,
                },
            ),
            acherion_model.AcherionNode(
                node_id='c2',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 2,
                    'x': 40,
                    'y': 20,
                },
            ),
        ]
    )
    owner = _CopyPasteOwner(graph)
    owner._selected_node_ids = {'c1', 'c2'}

    copied, _copy_message = owner._copy_selection_to_clipboard()
    pasted, paste_message = owner._paste_copied_nodes(
        anchor_x=253,
        anchor_y=167,
    )

    assert copied is True
    assert pasted is True
    assert paste_message == 'Pasted 2 nodes.'

    pasted_nodes = [
        node
        for node in owner._manual_nodes()
        if node.node_id in owner._selected_node_ids
    ]

    assert min(int(node.params['x']) for node in pasted_nodes) == 260
    assert min(int(node.params['y']) for node in pasted_nodes) == 160


def test_paste_at_cursor_rehomes_copied_inner_nodes() -> None:
    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id='box1',
                kind='function_box',
                title='Function Box',
                params={
                    'function_name': 'function_box',
                    'x': 100,
                    'y': 100,
                },
            ),
            acherion_model.AcherionNode(
                node_id='inner',
                kind='constant',
                params={
                    'parent_function': 'box1',
                    'value_type': 'int',
                    'number_value': 1,
                    'x': 140,
                    'y': 160,
                },
            ),
        ]
    )
    owner = _CopyPasteOwner(graph)
    owner._selected_node_ids = {'inner'}

    copied, _copy_message = owner._copy_selection_to_clipboard()
    pasted, paste_message = owner._paste_copied_nodes(
        anchor_x=520,
        anchor_y=400,
    )

    assert copied is True
    assert pasted is True
    assert paste_message == 'Pasted 1 node.'

    pasted_node = next(
        node
        for node in owner._manual_nodes()
        if node.node_id in owner._selected_node_ids
    )

    assert pasted_node.params.get('parent_function') in (None, '')
    assert int(pasted_node.params['x']) == 520
    assert int(pasted_node.params['y']) == 400